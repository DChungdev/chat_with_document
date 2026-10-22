"""B7 (hội thoại + SSE), B8 (xem nguồn dẫn), B9 (kill switch)."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from api_helpers import Env, completed, make_env, parse_sse

from docchat_core.application.chat import AskContext
from docchat_core.domain import MessageStatus
from docchat_core.domain.errors import AnswerFailed
from docchat_core.ports import Completed, Token


@pytest.fixture()
def ready(env: Env):  # type: ignore[no-untyped-def]
    env.accept_notice()
    doc, chunk = env.seed_ready_document()
    return env, doc, chunk, env.conversation()


def _messages(env: Env):  # type: ignore[no-untyped-def]
    ms = sorted(env.store.messages.values(), key=lambda m: m.created_at)
    return [m for m in ms if m.role.value == "user"], [m for m in ms if m.role.value == "ai"]


def test_conversation_creation_is_idempotent(env: Env) -> None:
    key = str(uuid4())
    h = {**env.headers(), "Idempotency-Key": key}
    a = env.client.post("/api/v1/conversations", headers=h)
    b = env.client.post("/api/v1/conversations", headers=h)
    assert a.status_code == b.status_code == 201
    assert a.json()["id"] == b.json()["id"] and len(env.store.conversations) == 1


def test_ask_happy_path_streams_and_persists(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.pipeline.script = [Token("Thanh toán "), Token("trong 30 ngày."), completed(doc, chunk)]
    r = env.ask(conv, "Điều khoản thanh toán?", documentIds=[str(doc.id)])

    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["cache-control"] == "no-cache" and r.headers["x-accel-buffering"] == "no"
    events = parse_sse(r.text)
    assert [n for n, _ in events] == ["message", "token", "token", "citations", "done"]

    users, ais = _messages(env)
    ai = ais[0]
    assert events[0][1] == {"messageId": str(ai.id), "status": "streaming"}
    assert "".join(d["text"] for n, d in events if n == "token") == "Thanh toán trong 30 ngày."
    cits = events[3][1]["citations"]
    assert len(cits) == 1 and cits[0]["valid"] is True
    assert cits[0]["documentName"] == "baogia.pdf" and cits[0]["page"] == 4
    assert cits[0]["documentId"] == str(doc.id)
    assert events[4][1] == {
        "messageId": str(ai.id), "status": "complete", "grounded": True, "citationCount": 1,
    }  # fmt: skip

    # đã lưu: câu hỏi (complete), câu trả lời (complete + grounded), 1 citation, tài liệu được chọn
    assert users[0].text == "Điều khoản thanh toán?" and users[0].status is MessageStatus.COMPLETE
    assert ai.status is MessageStatus.COMPLETE and ai.grounded is True
    assert ai.text == "Thanh toán trong 30 ngày." and ai.parent_message_id == users[0].id
    assert env.store.message_documents[users[0].id] == [doc.id]
    assert env.pipeline.calls[0]["document_ids"] == (doc.id,)


def test_ask_without_document_ids_uses_all_ready_documents(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    doc2, _ = env.seed_ready_document(name="hopdong.pdf")
    env.pipeline.script = [Completed(False, ())]
    assert env.ask(conv).status_code == 200
    assert set(env.pipeline.calls[0]["document_ids"]) == {doc.id, doc2.id}


def test_not_found_answer_is_grounded_false_without_citations(ready) -> None:  # type: ignore[no-untyped-def]
    env, _, _, conv = ready
    env.pipeline.script = [Token("Không tìm thấy trong tài liệu đã tải."), Completed(False, ())]
    events = parse_sse(env.ask(conv, "Thời tiết hôm nay?").text)
    assert [n for n, _ in events] == ["message", "token", "citations", "done"]
    assert events[2][1] == {"citations": []}
    assert events[3][1]["grounded"] is False and events[3][1]["citationCount"] == 0
    assert env.store.citations == {}


def test_no_ready_documents_is_422_and_nothing_stored(env: Env) -> None:
    env.accept_notice()
    conv = env.conversation()
    env.upload()  # đang processing, chưa ready
    r = env.ask(conv)
    assert r.status_code == 422 and r.json()["code"] == "NO_READY_DOCUMENTS"
    assert env.store.messages == {} and env.pipeline.calls == []


def test_selecting_non_ready_document_is_409(ready) -> None:  # type: ignore[no-untyped-def]
    env, _, _, conv = ready
    pending = env.upload().json()["id"]
    r = env.ask(conv, documentIds=[pending])
    assert r.status_code == 409 and r.json()["code"] == "DOCUMENT_NOT_READY"


def test_other_users_document_or_conversation_is_404(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, _, conv = ready
    env.accept_notice("bob")
    bob_conv = env.conversation("bob")
    r = env.ask(bob_conv, "x?", sub="bob", documentIds=[str(doc.id)])
    assert r.status_code == 404 and r.json()["code"] == "NOT_FOUND"
    r = env.ask(conv, "x?", sub="bob")  # hội thoại của alice
    assert r.status_code == 404
    assert env.pipeline.calls == []


@pytest.mark.parametrize(
    ("question", "docs", "status", "code"),
    [
        ("   ", None, 400, "VALIDATION_ERROR"),
        ("x" * 2001, None, 413, "QUESTION_TOO_LONG"),
        ("ok?", [str(uuid4()) for _ in range(11)], 400, "VALIDATION_ERROR"),
    ],
)
def test_validation_errors_use_problem_json(ready, question, docs, status, code) -> None:  # type: ignore[no-untyped-def]
    env, _, _, conv = ready
    body = {"documentIds": docs} if docs else {}
    r = env.ask(conv, question, **body)
    assert r.status_code == status and r.json()["code"] == code
    assert r.headers["content-type"].startswith("application/problem+json")
    assert env.store.messages == {}


def test_pydantic_validation_error_does_not_echo_input(ready) -> None:  # type: ignore[no-untyped-def]
    env, _, _, conv = ready
    r = env.client.post(
        f"/api/v1/conversations/{conv}/messages",
        json={"question": "BÍ-MẬT", "documentIds": ["not-a-uuid"]},
        headers=env.headers(),
    )
    assert r.status_code == 400 and "BÍ-MẬT" not in r.text and "not-a-uuid" not in r.text


def test_error_before_any_token_marks_message_failed_but_keeps_question(ready) -> None:  # type: ignore[no-untyped-def]
    env, *_, conv = ready
    env.pipeline.script = [AnswerFailed("LLM_TIMEOUT", "generate", True)]
    events = parse_sse(env.ask(conv, "Câu hỏi quan trọng?").text)
    assert [n for n, _ in events] == ["message", "error"]
    err = events[1][1]
    assert err["code"] == "LLM_TIMEOUT" and err["retryable"] is True and err["stage"] == "generate"
    users, ais = _messages(env)
    assert users[0].text == "Câu hỏi quan trọng?"  # câu hỏi không mất (CN-05)
    assert ais[0].status is MessageStatus.FAILED and ais[0].error_code == "LLM_TIMEOUT"


def test_error_mid_stream_keeps_partial_text_as_interrupted(ready) -> None:  # type: ignore[no-untyped-def]
    env, *_, conv = ready
    env.pipeline.script = [Token("Phần đầu "), AnswerFailed("LLM_UNAVAILABLE", "generate", True)]
    events = parse_sse(env.ask(conv).text)
    assert [n for n, _ in events] == ["message", "token", "error"]
    _, ais = _messages(env)
    assert ais[0].status is MessageStatus.INTERRUPTED and ais[0].text == "Phần đầu "


def test_unexpected_pipeline_crash_is_reported_without_leaking_details(ready) -> None:  # type: ignore[no-untyped-def]
    env, *_, conv = ready
    env.pipeline.script = [RuntimeError("bí mật trong thông điệp lỗi")]
    r = env.ask(conv)
    assert "bí mật" not in r.text
    events = parse_sse(r.text)
    assert events[-1][0] == "error" and events[-1][1]["code"] == "INTERNAL_ERROR"


def test_pipeline_ending_without_completed_is_an_error(ready) -> None:  # type: ignore[no-untyped-def]
    env, *_, conv = ready
    env.pipeline.script = [Token("cụt")]
    events = parse_sse(env.ask(conv).text)
    assert events[-1][0] == "error"
    _, ais = _messages(env)
    assert ais[0].status is MessageStatus.INTERRUPTED


def test_persist_failure_on_completion_is_reported_as_error(ready, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from docchat_infra.memory.store import MemCitations

    env, doc, chunk, conv = ready

    async def boom(self, citations):  # type: ignore[no-untyped-def]
        raise ConnectionError("db down")

    monkeypatch.setattr(MemCitations, "add_many", boom)
    env.pipeline.script = [Token("a"), completed(doc, chunk)]
    events = parse_sse(env.ask(conv).text)
    assert events[-1][0] == "error"
    _, ais = _messages(env)
    assert ais[0].status is MessageStatus.INTERRUPTED  # không kẹt ở streaming


async def test_client_disconnect_marks_interrupted_and_keeps_partial(ready) -> None:  # type: ignore[no-untyped-def]
    env, *_, conv = ready
    env.pipeline.script = [Token("Một "), Token("hai "), 5.0, Token("ba")]
    uid = env.user_id("alice")
    ctx: AskContext = await env.container.chat.prepare(
        uid, __import__("uuid").UUID(conv), question="q?", document_ids=[]
    )
    stream = env.container.chat.stream(ctx)
    assert (await anext(stream)).name == "message"
    assert (await anext(stream)).data == {"text": "Một "}
    await stream.aclose()  # client đóng kết nối giữa chừng
    _, ais = _messages(env)
    assert ais[0].status is MessageStatus.INTERRUPTED and ais[0].text == "Một "


async def test_ping_is_sent_while_waiting_for_slow_pipeline(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.container.chat._ping = 0.05
    env.pipeline.script = [0.2, completed(doc, chunk)]
    ctx = await env.container.chat.prepare(
        env.user_id("alice"), __import__("uuid").UUID(conv), question="q?", document_ids=[]
    )
    names = [ev.name async for ev in env.container.chat.stream(ctx)]
    assert names.count("ping") >= 2 and names[-1] == "done"


def test_client_message_id_replays_completed_answer_without_calling_pipeline(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.pipeline.script = [Token("Đáp án."), completed(doc, chunk)]
    cmid = str(uuid4())
    first = parse_sse(env.ask(conv, clientMessageId=cmid).text)
    second = parse_sse(env.ask(conv, clientMessageId=cmid).text)
    assert len(env.pipeline.calls) == 1  # không gọi LLM lần hai
    assert len(_messages(env)[0]) == 1  # không tạo câu hỏi trùng
    assert second[0] == first[0]  # cùng messageId
    assert [n for n, _ in second] == ["message", "token", "citations", "done"]
    assert second[1][1]["text"] == "Đáp án."


def test_client_message_id_while_in_progress_is_409(ready) -> None:  # type: ignore[no-untyped-def]
    env, *_, conv = ready
    cmid = uuid4()
    # Mô phỏng yêu cầu đầu còn đang chạy: đã prepare nhưng chưa hoàn tất.
    asyncio.run(
        env.container.chat.prepare(
            env.user_id("alice"), __import__("uuid").UUID(conv), question="q?",
            document_ids=[], client_message_id=cmid,
        )  # fmt: skip
    )
    r = env.ask(conv, clientMessageId=str(cmid))
    assert r.status_code == 409 and r.json()["code"] == "REQUEST_IN_PROGRESS"


def test_ask_rate_limit_is_30_per_minute(ready) -> None:  # type: ignore[no-untyped-def]
    env, *_, conv = ready
    env.pipeline.script = [Completed(False, ())]
    codes = [env.ask(conv, f"q{i}?").status_code for i in range(31)]
    assert codes[:30] == [200] * 30 and codes[30] == 429


# ---------- B8 ----------
def test_citation_returns_source_snippet(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.pipeline.script = [completed(doc, chunk)]
    env.ask(conv)
    cid = str(next(iter(env.store.citations)))
    r = env.client.get(f"/api/v1/citations/{cid}", headers=env.headers())
    assert r.status_code == 200
    assert r.json() == {
        "id": cid, "documentId": str(doc.id), "documentName": "baogia.pdf",
        "page": 4, "snippet": "Thanh toán trong 30 ngày.", "valid": True,
    }  # fmt: skip


def test_citation_of_other_user_is_404(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.pipeline.script = [completed(doc, chunk)]
    env.ask(conv)
    cid = next(iter(env.store.citations))
    assert env.client.get(f"/api/v1/citations/{cid}", headers=env.headers("bob")).status_code == 404
    assert env.client.get(f"/api/v1/citations/{uuid4()}", headers=env.headers()).status_code == 404


def test_citation_snippet_is_truncated_to_configured_length() -> None:
    for e in make_env({"citation_snippet_max_chars": 20}):
        e.accept_notice()
        doc, chunk = e.seed_ready_document(text="a" * 100)
        conv = e.conversation()
        e.pipeline.script = [completed(doc, chunk)]
        e.ask(conv)
        cid = next(iter(e.store.citations))
        snippet = e.client.get(f"/api/v1/citations/{cid}", headers=e.headers()).json()["snippet"]
        assert len(snippet) == 20 and snippet.endswith("…")
