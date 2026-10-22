"""D6: dừng sinh (US-205) và tạo lại câu trả lời."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID, uuid4

import pytest
from api_helpers import Env, completed, parse_sse

from docchat_core.domain import MessageRole, MessageStatus
from docchat_core.domain.errors import AnswerFailed, NotFound
from docchat_core.ports import Token


@pytest.fixture()
def ready(env: Env):  # type: ignore[no-untyped-def]
    env.accept_notice()
    doc, chunk = env.seed_ready_document()
    return env, doc, chunk, env.conversation()


def ai_messages(env: Env) -> list[Any]:
    ms = sorted(env.store.messages.values(), key=lambda m: m.created_at)
    return [m for m in ms if m.role is MessageRole.AI]


async def start(env: Env, conv: str) -> Any:
    ctx = await env.container.chat.prepare(
        env.user_id("alice"), UUID(conv), question="Câu hỏi?", document_ids=[]
    )
    return ctx, env.container.chat.stream(ctx)


# ---------- dừng ----------
async def test_stop_mid_stream_keeps_partial_text_and_marks_stopped(ready) -> None:  # type: ignore[no-untyped-def]
    env, *_, conv = ready
    env.pipeline.script = [Token("Một "), Token("hai "), 30.0, Token("ba")]
    ctx, stream = await start(env, conv)
    uid = env.user_id("alice")

    events = [
        await anext(stream),
        await anext(stream),
        await anext(stream),
    ]  # message, token, token
    assert [e.name for e in events] == ["message", "token", "token"]
    await env.container.chat.stop(uid, ctx.ai_message.id)
    rest = [e async for e in stream]

    assert [e.name for e in rest] == ["done"]
    assert rest[0].data == {
        "messageId": str(ctx.ai_message.id), "status": "stopped", "grounded": False, "citationCount": 0,
    }  # fmt: skip
    ai = ai_messages(env)[0]
    assert ai.status is MessageStatus.STOPPED and ai.text == "Một hai "  # giữ phần đã nhận
    assert env.store.citations == {}


async def test_stop_works_while_waiting_for_a_slow_first_token(ready) -> None:  # type: ignore[no-untyped-def]
    env, *_, conv = ready
    env.pipeline.script = [30.0, Token("muộn")]
    ctx, stream = await start(env, conv)
    await anext(stream)  # message
    waiter = asyncio.create_task(anext(stream))
    await asyncio.sleep(0.05)
    await env.container.chat.stop(env.user_id("alice"), ctx.ai_message.id)
    ev = await asyncio.wait_for(waiter, 2)
    assert ev.name == "done" and ev.data["status"] == "stopped"
    assert ai_messages(env)[0].status is MessageStatus.STOPPED


async def test_stop_is_idempotent_for_finished_messages(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.pipeline.script = [Token("xong"), completed(doc, chunk)]
    ctx, stream = await start(env, conv)
    _ = [e async for e in stream]
    await env.container.chat.stop(env.user_id("alice"), ctx.ai_message.id)  # không lỗi
    await env.container.chat.stop(env.user_id("alice"), ctx.ai_message.id)
    assert ai_messages(env)[0].status is MessageStatus.COMPLETE  # không bị ghi đè


async def test_stop_rejects_unknown_foreign_or_user_messages(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.pipeline.script = [Token("x"), completed(doc, chunk)]
    ctx, stream = await start(env, conv)
    _ = [e async for e in stream]
    env.accept_notice("bob")
    env.client.get("/api/v1/config", headers=env.headers("bob"))
    chat = env.container.chat
    with pytest.raises(NotFound):
        await chat.stop(env.user_id("bob"), ctx.ai_message.id)  # tin nhắn của người khác
    with pytest.raises(NotFound):
        await chat.stop(env.user_id("alice"), uuid4())
    with pytest.raises(NotFound):
        await chat.stop(
            env.user_id("alice"), ctx.ai_message.parent_message_id
        )  # câu hỏi, không phải trả lời


async def test_stop_registry_is_cleaned_up(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.pipeline.script = [Token("x"), completed(doc, chunk)]
    ctx, stream = await start(env, conv)
    _ = [e async for e in stream]
    assert env.container.chat._active == {}


def test_stop_endpoint_returns_202_and_404(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.pipeline.script = [Token("x"), completed(doc, chunk)]
    env.ask(conv)
    ai = ai_messages(env)[0]
    h = env.headers()
    assert env.client.post(f"/api/v1/messages/{ai.id}/stop", headers=h).status_code == 202
    assert env.client.post(f"/api/v1/messages/{uuid4()}/stop", headers=h).status_code == 404
    assert (
        env.client.post(f"/api/v1/messages/{ai.id}/stop", headers=env.headers("bob")).status_code
        == 404
    )


# ---------- tạo lại ----------
def test_regenerate_after_failure_creates_a_new_answer_for_the_same_question(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.pipeline.script = [AnswerFailed("LLM_TIMEOUT", "generate", True)]
    first = parse_sse(env.ask(conv, "Điều khoản thanh toán?").text)
    assert first[-1][0] == "error"
    failed = ai_messages(env)[0]
    assert failed.status is MessageStatus.FAILED

    env.pipeline.script = [Token("Đã có đáp án."), completed(doc, chunk)]
    r = env.client.post(f"/api/v1/messages/{failed.id}/regenerate", headers=env.headers())
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(r.text)
    assert [n for n, _ in events] == ["message", "token", "citations", "done"]

    answers = ai_messages(env)
    assert len(answers) == 2  # bản cũ được giữ để kiểm toán
    new = next(m for m in answers if m.id != failed.id)
    assert events[0][1]["messageId"] == str(new.id)
    assert new.parent_message_id == failed.parent_message_id  # cùng một câu hỏi
    assert new.status is MessageStatus.COMPLETE and new.text == "Đã có đáp án."
    assert failed.status is MessageStatus.FAILED
    users = [m for m in env.store.messages.values() if m.role is MessageRole.USER]
    assert len(users) == 1  # không nhân đôi câu hỏi
    assert env.pipeline.calls[-1]["question"] == "Điều khoản thanh toán?"
    assert env.pipeline.calls[-1]["document_ids"] == (doc.id,)  # cùng phạm vi tài liệu đã chọn


def test_regenerate_works_from_interrupted_and_stopped_answers(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.pipeline.script = [Token("dở"), AnswerFailed("LLM_UNAVAILABLE", "generate", True)]
    env.ask(conv)
    interrupted = ai_messages(env)[0]
    assert interrupted.status is MessageStatus.INTERRUPTED
    env.pipeline.script = [Token("ok"), completed(doc, chunk)]
    assert (
        env.client.post(
            f"/api/v1/messages/{interrupted.id}/regenerate", headers=env.headers()
        ).status_code
        == 200
    )


def test_regenerate_skips_documents_that_were_deleted_meanwhile(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    doc2, chunk2 = env.seed_ready_document(name="b.pdf")
    env.pipeline.script = [AnswerFailed("LLM_TIMEOUT")]
    env.ask(conv, documentIds=[str(doc.id), str(doc2.id)])
    failed = ai_messages(env)[0]
    env.client.delete(f"/api/v1/documents/{doc.id}", headers=env.headers())

    env.pipeline.script = [Token("ok"), completed(doc2, chunk2)]
    assert (
        env.client.post(
            f"/api/v1/messages/{failed.id}/regenerate", headers=env.headers()
        ).status_code
        == 200
    )
    assert env.pipeline.calls[-1]["document_ids"] == (doc2.id,)

    env.client.delete(f"/api/v1/documents/{doc2.id}", headers=env.headers())
    r = env.client.post(f"/api/v1/messages/{failed.id}/regenerate", headers=env.headers())
    assert r.status_code == 422 and r.json()["code"] == "NO_READY_DOCUMENTS"


async def test_cannot_regenerate_an_answer_that_is_still_streaming(ready) -> None:  # type: ignore[no-untyped-def]
    env, *_, conv = ready
    env.pipeline.script = [Token("a"), 30.0]
    ctx, stream = await start(env, conv)
    await anext(stream)
    with pytest.raises(Exception) as ei:
        await env.container.chat.prepare_regenerate(env.user_id("alice"), ctx.ai_message.id)
    assert getattr(ei.value, "code", "") == "INVALID_STATE"
    await stream.aclose()


def test_regenerate_enforces_ownership_kill_switch_and_rate_limit(ready) -> None:  # type: ignore[no-untyped-def]
    env, doc, chunk, conv = ready
    env.pipeline.script = [AnswerFailed("LLM_TIMEOUT")]
    env.ask(conv)
    failed = ai_messages(env)[0]
    url = f"/api/v1/messages/{failed.id}/regenerate"

    assert env.client.post(url, headers=env.headers("bob")).status_code == 404
    assert (
        env.client.post(f"/api/v1/messages/{uuid4()}/regenerate", headers=env.headers()).status_code
        == 404
    )

    env.config.values["qa_enabled"] = False
    r = env.client.post(url, headers=env.headers())
    assert r.status_code == 503 and r.json()["code"] == "QA_DISABLED"
    env.config.values["qa_enabled"] = True

    env.pipeline.script = [Token("x"), completed(doc, chunk)]
    codes = [env.client.post(url, headers=env.headers()).status_code for _ in range(31)]
    assert 429 in codes  # dùng chung hạn mức 30 câu hỏi/phút với hỏi mới
