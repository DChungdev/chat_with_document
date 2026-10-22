"""Kiểm cú pháp SQL của repository worker bằng parser PostgreSQL (không cần CSDL)."""

import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from docchat_core.ports.ingest import NewChunk
from docchat_infra.persistence import worker as w

pglast = pytest.importorskip("pglast")

NOW = datetime.now(UTC)
ROW: dict[str, Any] = {
    "id": uuid4(), "user_id": uuid4(), "name": "a.pdf", "size_bytes": 1, "page_count": None,
    "status": "processing", "error_code": None, "storage_key": "k", "content_sha256": None,
    "uploaded_at": NOW, "processed_at": None, "document_id": uuid4(), "attempts": 1,
    "trace_context": {"traceparent": "x"}, "n": 3, "ok": 1,
}  # fmt: skip


class FakeResult:
    rowcount = 1

    def mappings(self) -> "FakeResult":
        return self

    def first(self) -> dict[str, Any]:
        return ROW


class FakeConn:
    def __init__(self) -> None:
        self.sql: list[str] = []
        self.params: list[Any] = []

    async def execute(self, stmt: Any, params: Any = None) -> FakeResult:
        self.sql.append(str(stmt))
        self.params.append(params)
        return FakeResult()


def to_pg(sql: str) -> str:
    n = 0

    def sub(m: re.Match[str]) -> str:
        nonlocal n
        n += 1
        return f"${n}"

    return re.sub(r"(?<!:):(\w+)", sub, sql)


async def exercise() -> FakeConn:
    c = FakeConn()
    jobs, docs, chunks = w.PgIngestJobs(c), w.PgIngestDocuments(c), w.PgChunkWriter(c)  # type: ignore[arg-type]
    job = await jobs.claim("w1")
    assert job and job.attempts == 1 and job.trace_context == {"traceparent": "x"}
    await jobs.complete(1)
    await jobs.retry(1, 30.0, "EMBEDDING_FAILED")
    await jobs.fail(1, "EMBEDDING_FAILED")
    await jobs.requeue_stale(600)
    assert await jobs.queue_length() == 3
    await docs.get(uuid4())
    await docs.mark_ready(uuid4(), 3, NOW)
    await docs.mark_error(uuid4(), "NO_TEXT", NOW)
    await chunks.replace(uuid4(), uuid4(), "m", [NewChunk(0, 1, 1, "t", 1, [0.1, 0.2])])
    return c


async def test_worker_queries_parse_as_postgres_sql() -> None:
    conn = await exercise()
    assert len(conn.sql) >= 12
    for sql in conn.sql:
        try:
            pglast.parse_sql(to_pg(sql))
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"SQL không hợp lệ: {sql!r}: {exc}")


async def test_claim_uses_the_skip_locked_function() -> None:
    conn = await exercise()
    assert "fn_claim_ingest_job" in conn.sql[0]  # FOR UPDATE SKIP LOCKED nằm trong hàm CSDL


async def test_chunk_replace_deletes_old_chunks_before_insert_in_same_unit() -> None:
    conn = await exercise()
    sql = [s for s in conn.sql if "chunks" in s]
    assert "DELETE FROM chunks" in sql[0] and "INSERT INTO chunks" in sql[1]
    assert any("FOR SHARE" in s for s in conn.sql)  # khóa dòng tài liệu chống xóa đồng thời


def test_vector_literal_format() -> None:
    assert w.vector_literal([0.1, -2, 3.5]) == "[0.1,-2.0,3.5]"
    assert w.vector_literal([]) == "[]"
