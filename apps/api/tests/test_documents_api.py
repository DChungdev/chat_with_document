"""B4 (tải lên/liệt kê), B6 (chặn khi chưa xác nhận thông báo), B11 (xóa)."""

from __future__ import annotations

import logging
from uuid import uuid4

import pytest
from api_helpers import PDF, Env, make_env

from docchat_infra.memory.store import MemJobs


@pytest.fixture()
def accepted(env: Env) -> Env:
    env.accept_notice("alice")
    return env


# ---------- B3/B5: xác thực & định dạng lỗi ----------
def test_unauthenticated_returns_problem_json(env: Env) -> None:
    r = env.client.get("/api/v1/documents")
    assert r.status_code == 401
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["code"] == "UNAUTHENTICATED" and body["status"] == 401
    assert body["requestId"] == r.headers["x-request-id"]


# ---------- B6 ----------
def test_upload_blocked_until_notice_accepted(env: Env) -> None:
    r = env.upload()
    assert r.status_code == 403 and r.json()["code"] == "NOTICE_NOT_ACCEPTED"
    assert env.storage.objects == {} and env.store.documents == {}
    env.accept_notice()
    assert env.upload().status_code == 202


# ---------- B4 ----------
def test_upload_returns_202_and_enqueues(accepted: Env) -> None:
    r = accepted.upload(name="baogia.pdf")
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "processing" and body["name"] == "baogia.pdf"
    assert body["sizeBytes"] == len(PDF) and body["pageCount"] is None
    assert r.headers["location"] == f"/api/v1/documents/{body['id']}"

    uid = accepted.user_id("alice")
    doc = next(iter(accepted.store.documents.values()))
    assert doc.user_id == uid and doc.content_sha256 and len(doc.content_sha256) == 64
    assert doc.storage_key == f"{uid}/{doc.id}.pdf"  # không dùng tên tệp gốc làm khóa
    assert accepted.storage.objects[doc.storage_key] == PDF
    assert doc.id in accepted.store.jobs  # job cùng giao dịch với bản ghi tài liệu


def test_upload_name_is_sanitized_and_not_in_storage_key(accepted: Env) -> None:
    r = accepted.upload(name="..\\..\\etc/hop dong.pdf")
    assert r.status_code == 202
    assert r.json()["name"] == "hop dong.pdf"
    assert all("hop" not in k for k in accepted.storage.objects)


def test_sanitize_name_strips_control_chars_and_limits_length() -> None:
    from docchat_core.application.documents import _sanitize_name

    assert _sanitize_name("a\x00b\x1f.pdf") == "ab.pdf"
    assert _sanitize_name("x" * 400)[:3] == "xxx" and len(_sanitize_name("x" * 400)) == 255
    assert _sanitize_name(None) == "document.pdf" and _sanitize_name("  ") == "document.pdf"


@pytest.mark.parametrize(
    ("content", "ctype"),
    [
        (b"hello, this is not a pdf", "application/pdf"),  # sai chữ ký dù khai báo PDF
        (PDF, "text/plain"),  # đúng chữ ký nhưng sai MIME
        (b"", "application/pdf"),  # tệp rỗng
    ],
)
def test_invalid_file_rejected_without_side_effects(
    accepted: Env, content: bytes, ctype: str
) -> None:
    r = accepted.upload(content=content, content_type=ctype)
    assert r.status_code == 400 and r.json()["code"] == "INVALID_FILE_TYPE"
    assert accepted.storage.objects == {} and accepted.store.documents == {}


def test_file_too_large_returns_413() -> None:
    for e in make_env({"max_file_size_bytes": 20}):
        e.accept_notice()
        r = e.upload(content=PDF)
        assert r.status_code == 413 and r.json()["code"] == "FILE_TOO_LARGE"
        assert e.storage.objects == {}


def test_limit_exceeded_returns_409() -> None:
    for e in make_env({"max_files_per_user": 2}):
        e.accept_notice()
        assert e.upload().status_code == 202
        assert e.upload().status_code == 202
        r = e.upload()
        assert r.status_code == 409 and r.json()["code"] == "LIMIT_EXCEEDED"


def test_idempotency_key_returns_same_document(accepted: Env) -> None:
    key = uuid4()
    first = accepted.upload(key=key)
    again = accepted.upload(key=key)
    assert first.status_code == again.status_code == 202
    assert first.json()["id"] == again.json()["id"]
    assert len(accepted.store.documents) == 1 and len(accepted.storage.objects) == 1


@pytest.mark.parametrize("header", [None, "not-a-uuid"])
def test_idempotency_key_required(accepted: Env, header: str | None) -> None:
    headers = accepted.headers()
    if header:
        headers["Idempotency-Key"] = header
    r = accepted.client.post(
        "/api/v1/documents", files={"file": ("a.pdf", PDF, "application/pdf")}, headers=headers
    )
    assert r.status_code == 400 and r.json()["code"] == "VALIDATION_ERROR"


def test_one_bad_file_does_not_affect_others(accepted: Env) -> None:
    ok1 = accepted.upload(name="a.pdf")
    bad = accepted.upload(name="b.pdf", content=b"nope")
    ok2 = accepted.upload(name="c.pdf")
    assert (ok1.status_code, bad.status_code, ok2.status_code) == (202, 400, 202)
    assert len(accepted.store.documents) == 2


def test_db_failure_after_put_cleans_storage_and_rolls_back(
    accepted: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def boom(self: MemJobs, document_id: object, trace_context: object) -> None:
        raise ConnectionError("db down")

    monkeypatch.setattr(MemJobs, "enqueue", boom)
    r = accepted.upload()
    assert r.status_code == 500 and r.json()["code"] == "INTERNAL_ERROR"
    assert accepted.storage.objects == {}  # tệp vừa ghi bị dọn
    assert accepted.store.documents == {}  # giao dịch rollback


def test_upload_rate_limit(accepted: Env) -> None:
    for _ in range(20):
        accepted.upload()
    r = accepted.upload()
    assert r.status_code == 429
    assert r.json()["code"] == "RATE_LIMITED" and r.json()["retryable"] is True
    assert int(r.headers["retry-after"]) >= 1


# ---------- liệt kê / chi tiết ----------
def test_list_newest_first_with_cursor(accepted: Env) -> None:
    ids = [accepted.upload(name=f"d{i}.pdf").json()["id"] for i in range(5)]
    h = accepted.headers()
    page1 = accepted.client.get("/api/v1/documents?limit=2", headers=h).json()
    assert [d["id"] for d in page1["items"]] == ids[::-1][:2]
    assert page1["nextCursor"]
    page2 = accepted.client.get(
        f"/api/v1/documents?limit=2&cursor={page1['nextCursor']}", headers=h
    )
    assert [d["id"] for d in page2.json()["items"]] == ids[::-1][2:4]
    page3 = accepted.client.get(
        f"/api/v1/documents?limit=2&cursor={page2.json()['nextCursor']}", headers=h
    ).json()
    assert [d["id"] for d in page3["items"]] == ids[::-1][4:] and page3["nextCursor"] is None


def test_documents_isolated_between_users(accepted: Env) -> None:
    accepted.accept_notice("bob")
    doc_id = accepted.upload("alice").json()["id"]
    bob = accepted.headers("bob")
    assert accepted.client.get("/api/v1/documents", headers=bob).json()["items"] == []
    r = accepted.client.get(f"/api/v1/documents/{doc_id}", headers=bob)
    assert r.status_code == 404 and r.json()["code"] == "NOT_FOUND"
    # xóa tài liệu người khác cũng 404 và không có tác dụng
    assert accepted.client.delete(f"/api/v1/documents/{doc_id}", headers=bob).status_code == 404
    assert (
        accepted.client.get(f"/api/v1/documents/{doc_id}", headers=accepted.headers()).status_code
        == 200
    )


# ---------- B11 ----------
def test_delete_removes_document_file_and_invalidates_citations(accepted: Env) -> None:
    doc_id = accepted.upload().json()["id"]
    doc = next(iter(accepted.store.documents.values()))
    key = doc.storage_key
    assert key in accepted.storage.objects

    r = accepted.client.delete(f"/api/v1/documents/{doc_id}", headers=accepted.headers())
    assert r.status_code == 204
    assert (
        accepted.client.get(f"/api/v1/documents/{doc_id}", headers=accepted.headers()).status_code
        == 404
    )
    assert key not in accepted.storage.objects
    assert doc.id not in accepted.store.jobs  # job chờ bị hủy
    assert (accepted.user_id("alice"), "document_deleted", doc.id) in accepted.store.audit


def test_delete_invalidates_existing_citations(accepted: Env) -> None:
    from api_helpers import completed

    doc, chunk = accepted.seed_ready_document()
    conv = accepted.conversation()
    accepted.pipeline.script = [completed(doc, chunk)]
    assert accepted.ask(conv).status_code == 200
    cit_id = next(iter(accepted.store.citations))
    h = accepted.headers()

    before = accepted.client.get(f"/api/v1/citations/{cit_id}", headers=h).json()
    assert before["valid"] is True and before["snippet"]

    assert accepted.client.delete(f"/api/v1/documents/{doc.id}", headers=h).status_code == 204
    after = accepted.client.get(f"/api/v1/citations/{cit_id}", headers=h)
    assert after.status_code == 200  # không 404, không để trống (PRD 4.2)
    assert after.json() == {
        "id": str(cit_id), "documentId": None, "documentName": None,
        "page": 4, "snippet": None, "valid": False,
    }  # fmt: skip


def test_delete_survives_storage_failure(accepted: Env, caplog: pytest.LogCaptureFixture) -> None:
    doc_id = accepted.upload().json()["id"]
    accepted.storage.fail_delete = True
    with caplog.at_level(logging.ERROR, logger="docchat_core.application.documents"):
        r = accepted.client.delete(f"/api/v1/documents/{doc_id}", headers=accepted.headers())
    assert r.status_code == 204  # DB đã xóa; người dùng không bị chặn vì lỗi lưu trữ
    assert doc_id not in {str(k) for k in accepted.store.documents}
    orphan = [x for x in caplog.records if getattr(x, "event", "") == "storage_orphaned"]
    assert orphan and orphan[0].document_id == doc_id  # type: ignore[attr-defined]
