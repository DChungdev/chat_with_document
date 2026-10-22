"""Kiểm cú pháp mọi câu SQL của repository PostgreSQL mà KHÔNG cần CSDL.

Chạy từng phương thức với kết nối giả ghi lại câu lệnh, đổi `:param` thành `$n`, rồi cho pglast
(parser của chính PostgreSQL) phân tích. Không thay thế test tích hợp nhưng bắt lỗi cú pháp sớm.
"""

import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from docchat_core.domain import (
    Citation,
    Conversation,
    Document,
    Message,
    TelemetryEvent,
    UserRole,
)
from docchat_infra.persistence import repositories as r

pglast = pytest.importorskip("pglast")

NOW = datetime.now(UTC)
UID = uuid4()
ROW: dict[str, Any] = {
    "id": uuid4(), "user_id": UID, "name": "a.pdf", "size_bytes": 1, "page_count": None,
    "status": "processing", "error_code": None, "storage_key": "k", "content_sha256": None,
    "uploaded_at": NOW, "processed_at": None, "conversation_id": uuid4(), "role": "user",
    "text": "t", "grounded": None, "parent_message_id": None, "client_message_id": None,
    "created_at": NOW, "completed_at": None, "last_activity_at": NOW, "version": "v",
    "content": "c", "message_id": uuid4(), "ordinal": 1, "page": 1, "document_id": uuid4(),
    "chunk_id": None, "document_name": None, "snippet": None, "n": 0, "resource_id": uuid4(),
    "ok": 1, "allowed_props": ["a"], "external_subject": "s",
}  # fmt: skip


class FakeResult:
    rowcount = 1

    def __init__(self, sql: str) -> None:
        # `status` có hai enum khác nhau: tài liệu (processing) và tin nhắn (complete)
        self.row = {**ROW, "status": "complete"} if "messages" in sql else ROW

    def mappings(self) -> "FakeResult":
        return self

    def first(self) -> dict[str, Any]:
        return self.row

    def all(self) -> list[dict[str, Any]]:
        return [self.row]


class FakeConn:
    def __init__(self) -> None:
        self.sql: list[str] = []

    async def execute(self, stmt: Any, params: Any = None) -> FakeResult:
        self.sql.append(str(stmt))
        return FakeResult(str(stmt))


def to_pg(sql: str) -> str:
    n = 0

    def sub(m: re.Match[str]) -> str:
        nonlocal n
        n += 1
        return f"${n}"

    return re.sub(r"(?<!:):(\w+)", sub, sql)  # bỏ qua `::`


async def run_all() -> list[str]:
    c = FakeConn()
    doc = Document(uuid4(), UID, "a.pdf", 1, "k", NOW)
    msg = Message.new_user(uuid4(), uuid4(), UID, "q", NOW)
    cit = Citation(uuid4(), uuid4(), UID, 1, 1, uuid4(), uuid4(), "a.pdf")
    ev = TelemetryEvent(NOW, "answer_completed", "h" * 64, uuid4(), "0.1.0", {"a": 1})
    cursor = r._encode_cursor(NOW, uuid4())
    users, docs = r.PgUsers(c, UID), r.PgDocuments(c, UID)  # type: ignore[arg-type]
    await users.upsert_by_subject("s", UserRole.USER)
    await docs.add(doc)
    await docs.get(doc.id)
    await docs.get_many([doc.id])
    await docs.list_page(10, None)
    await docs.list_page(10, cursor)
    await docs.list_ready_ids(5)
    await docs.count()
    await docs.delete(doc.id)
    await r.PgJobs(c, UID).enqueue(doc.id, {"a": "b"})  # type: ignore[arg-type]
    idem = r.PgIdempotency(c, UID)  # type: ignore[arg-type]
    await idem.get("s", uuid4())
    await idem.put("s", uuid4(), uuid4())
    convs = r.PgConversations(c, UID)  # type: ignore[arg-type]
    await convs.add(Conversation(uuid4(), UID, NOW, NOW))
    await convs.get(uuid4())
    msgs = r.PgMessages(c, UID)  # type: ignore[arg-type]
    await msgs.add(msg)
    await msgs.update(msg)
    await msgs.get(msg.id)
    await msgs.find_user_message_by_client_id(uuid4(), uuid4())
    await msgs.find_reply(uuid4())
    await msgs.set_documents(msg.id, [uuid4()])
    cits = r.PgCitations(c, UID)  # type: ignore[arg-type]
    await cits.add_many([cit])
    await cits.get_view(cit.id)
    await cits.for_message(cit.message_id)
    notices = r.PgNotices(c, UID)  # type: ignore[arg-type]
    await notices.current()
    await notices.has_accepted("v")
    await notices.accept("v")
    tel = r.PgTelemetry(c, UID)  # type: ignore[arg-type]
    await tel.allowlist()
    await tel.add_many([ev])
    return c.sql


async def test_every_repository_query_parses_as_postgres_sql() -> None:
    statements = await run_all()
    assert len(statements) >= 28
    for sql in statements:
        try:
            pglast.parse_sql(to_pg(sql))
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"SQL không hợp lệ: {sql!r}: {exc}")


async def test_every_query_is_scoped_to_the_bound_user() -> None:
    """Truy vấn đọc/ghi dữ liệu người dùng phải có điều kiện user_id tường minh (ADR-07)."""
    exempt = (
        "data_notice_versions",
        "telemetry_event_types",
        "INSERT INTO users",
        "INSERT INTO telemetry_events",
        "INSERT INTO ingest_jobs",  # không có cột user_id; luôn đi kèm INSERT tài liệu của chính người dùng
    )
    for sql in await run_all():
        if any(e in sql for e in exempt):
            continue
        scoped = re.search(r"\buser_id\b|:u\b", sql) is not None
        assert scoped, f"thiếu lọc user_id: {sql!r}"
