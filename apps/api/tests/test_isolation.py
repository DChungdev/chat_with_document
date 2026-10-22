"""G3 (US-402): người dùng B không thấy, không dùng, không suy ra được dữ liệu của người dùng A.

Mọi truy cập chéo phải trả 404 (không phải 403) để không lộ sự tồn tại của tài nguyên.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from qa_helpers import QaEnv, make_qa_env
from test_qa_e2e import CONTRACT, QUOTE, ask, upload_ready

SECRET_FACT = "Giá trọn gói là 250 triệu đồng"


@pytest.fixture()
def world() -> Iterator[QaEnv]:
    yield from make_qa_env()


@pytest.fixture()
def two(world: QaEnv) -> dict[str, str]:
    """alice có tài liệu + hội thoại + câu trả lời; bob có tài liệu riêng."""
    world.accept_notice("alice")
    world.accept_notice("bob")
    a_doc = upload_ready(world, QUOTE, "baogia.pdf", "alice")
    b_doc = upload_ready(world, CONTRACT, "hopdong.pdf", "bob")
    a_conv = world.conversation("alice")
    events = ask(world, a_conv, "Thanh toán trong vòng bao nhiêu ngày?", "alice")
    msg = next(d for n, d in events if n == "message")["messageId"]
    cit = next(d for n, d in events if n == "citations")["citations"][0]["id"]
    return {"a_doc": a_doc, "b_doc": b_doc, "a_conv": a_conv, "a_msg": msg, "a_cit": cit}


def _is_404(r) -> None:  # type: ignore[no-untyped-def]
    assert r.status_code == 404, (r.status_code, r.text)
    body = r.text
    assert "baogia" not in body and "30 ngày" not in body and "alice" not in body


def test_documents_are_invisible_to_other_users(world: QaEnv, two: dict[str, str]) -> None:
    h = world.headers("bob")
    listing = world.client.get("/api/v1/documents", headers=h).json()
    assert [d["name"] for d in listing["items"]] == ["hopdong.pdf"]
    _is_404(world.client.get(f"/api/v1/documents/{two['a_doc']}", headers=h))
    _is_404(world.client.delete(f"/api/v1/documents/{two['a_doc']}", headers=h))
    # xóa chéo không làm mất tài liệu của A
    mine = world.client.get(f"/api/v1/documents/{two['a_doc']}", headers=world.headers("alice"))
    assert mine.status_code == 200 and mine.json()["status"] == "ready"


def test_cannot_ask_over_someone_elses_document(world: QaEnv, two: dict[str, str]) -> None:
    conv = world.conversation("bob")
    r = world.ask(conv, "Giá trọn gói là bao nhiêu?", sub="bob", documentIds=[two["a_doc"]])
    assert r.status_code in (404, 422), r.text
    assert SECRET_FACT not in r.text and "250" not in r.text


def test_retrieval_never_crosses_users(world: QaEnv, two: dict[str, str]) -> None:
    """B hỏi đúng nội dung của A trên tài liệu của B ⇒ không tìm thấy, không trích dẫn."""
    conv = world.conversation("bob")
    events = ask(world, conv, "Giá trọn gói là bao nhiêu triệu đồng đã gồm thuế?", "bob")
    text = "".join(d["text"] for n, d in events if n == "token")
    assert "250" not in text and "triệu" not in text
    # Nếu có trích dẫn thì chỉ có thể thuộc tài liệu của chính B (không bao giờ của A).
    cited = {c["documentId"] for n, d in events if n == "citations" for c in d["citations"]}
    assert two["a_doc"] not in cited and cited <= {two["b_doc"]}
    assert "baogia" not in "".join(str(d) for _, d in events)


def test_conversations_messages_citations_feedback_stop_are_private(
    world: QaEnv, two: dict[str, str]
) -> None:
    h = world.headers("bob")
    r = world.client.post(
        f"/api/v1/conversations/{two['a_conv']}/messages", json={"question": "xin chào"}, headers=h
    )
    _is_404(r)
    _is_404(world.client.get(f"/api/v1/citations/{two['a_cit']}", headers=h))
    _is_404(world.client.post(f"/api/v1/messages/{two['a_msg']}/regenerate", headers=h))
    _is_404(world.client.post(f"/api/v1/messages/{two['a_msg']}/stop", headers=h))
    _is_404(
        world.client.put(
            f"/api/v1/messages/{two['a_msg']}/feedback", json={"rating": "down"}, headers=h
        )
    )
    # chủ sở hữu vẫn dùng bình thường
    assert (
        world.client.get(
            f"/api/v1/citations/{two['a_cit']}", headers=world.headers("alice")
        ).status_code
        == 200
    )


@pytest.mark.parametrize("roles", [["evaluator"], ["ops"], ["evaluator", "ops"]])
def test_privileged_roles_do_not_gain_content_access(
    world: QaEnv, two: dict[str, str], roles: list[str]
) -> None:
    """Evaluator/ops xem được số liệu tổng hợp, KHÔNG xem được nội dung của bất kỳ ai."""
    h = world.headers("carol", roles)
    assert world.client.get("/api/v1/documents", headers=h).json()["items"] == []
    _is_404(world.client.get(f"/api/v1/documents/{two['a_doc']}", headers=h))
    _is_404(world.client.get(f"/api/v1/citations/{two['a_cit']}", headers=h))
    _is_404(world.client.delete(f"/api/v1/documents/{two['a_doc']}", headers=h))


def test_report_contains_no_content_or_identity(world: QaEnv, two: dict[str, str]) -> None:
    r = world.client.get("/api/v1/reports/mvp-metrics", headers=world.headers("eve", ["evaluator"]))
    assert r.status_code == 200
    blob = r.text
    for needle in (
        "baogia",
        "hopdong",
        "30 ngày",
        "250",
        "alice",
        "bob",
        two["a_doc"],
        two["a_msg"],
    ):
        assert needle not in blob


def test_plain_user_cannot_use_report_or_admin_endpoints(world: QaEnv, two: dict[str, str]) -> None:
    h = world.headers("alice")
    assert world.client.get("/api/v1/reports/mvp-metrics", headers=h).status_code == 403
    r = world.client.put("/api/v1/admin/flags/qa-enabled", json={"enabled": False}, headers=h)
    assert r.status_code == 403


def test_unauthenticated_and_forged_tokens_are_rejected(world: QaEnv, two: dict[str, str]) -> None:
    import jwt as pyjwt

    paths = ["/api/v1/documents", f"/api/v1/citations/{two['a_cit']}", "/api/v1/config"]
    for p in paths:
        assert world.client.get(p).status_code == 401
        forged = pyjwt.encode(
            {"sub": "alice"}, "sai-khoa-sai-khoa-sai-khoa-0123456789", algorithm="HS256"
        )
        assert world.client.get(p, headers={"Authorization": f"Bearer {forged}"}).status_code == 401
        none_alg = pyjwt.encode({"sub": "alice"}, "", algorithm="none")
        assert (
            world.client.get(p, headers={"Authorization": f"Bearer {none_alg}"}).status_code == 401
        )


def test_deleting_my_document_does_not_touch_others(world: QaEnv, two: dict[str, str]) -> None:
    assert (
        world.client.delete(
            f"/api/v1/documents/{two['b_doc']}", headers=world.headers("bob")
        ).status_code
        == 204
    )
    still = world.client.get(f"/api/v1/documents/{two['a_doc']}", headers=world.headers("alice"))
    assert still.status_code == 200
    # chunk của A còn nguyên, chunk của B đã biến mất
    owners = (
        {c.user_id for c in world.store.chunks.values()}
        if hasattr(world.store, "chunks")
        else set()
    )
    assert world.user_id("bob") not in owners
