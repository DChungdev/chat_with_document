"""Repository cho worker ingest (vai trò app_worker): hàng đợi, trạng thái tài liệu, ghi chunk.

Worker xử lý tài liệu của mọi người dùng nên không đặt `app.user_id`; chính sách RLS riêng của
worker (p_documents_worker, p_chunks_worker) cho phép việc này (Database_Design_SQL mục 5).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from types import TracebackType
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from docchat_core.domain import Document
from docchat_core.ports.ingest import IngestJob, NewChunk
from docchat_infra.persistence.repositories import _DOC_COLS, _doc
from docchat_infra.persistence.session import system_transaction


def vector_literal(values: Sequence[float]) -> str:
    """Dạng văn bản của pgvector: '[0.1,0.2,...]' (ép kiểu bằng CAST(... AS vector))."""
    return "[" + ",".join(repr(float(v)) for v in values) + "]"


class PgIngestJobs:
    def __init__(self, conn: AsyncConnection) -> None:
        self.conn = conn

    async def claim(self, worker_id: str) -> IngestJob | None:
        row = (
            (
                await self.conn.execute(
                    text(
                        "SELECT id, document_id, attempts, trace_context FROM fn_claim_ingest_job(:w)"
                    ),
                    {"w": worker_id},
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return IngestJob(row["id"], row["document_id"], row["attempts"], row["trace_context"] or {})

    async def complete(self, job_id: int) -> None:
        await self.conn.execute(
            text(
                "UPDATE ingest_jobs SET status = 'done', locked_at = NULL, locked_by = NULL, "
                "last_error = NULL WHERE id = :id"
            ),
            {"id": job_id},
        )

    async def retry(self, job_id: int, delay_seconds: float, error_code: str) -> None:
        await self.conn.execute(
            text(
                "UPDATE ingest_jobs SET status = 'queued', locked_at = NULL, locked_by = NULL, "
                "run_after = now() + make_interval(secs => :d), last_error = :e WHERE id = :id"
            ),
            {"id": job_id, "d": delay_seconds, "e": error_code},
        )

    async def fail(self, job_id: int, error_code: str) -> None:
        await self.conn.execute(
            text(
                "UPDATE ingest_jobs SET status = 'failed', locked_at = NULL, locked_by = NULL, "
                "last_error = :e WHERE id = :id"
            ),
            {"id": job_id, "e": error_code},
        )

    async def requeue_stale(self, timeout_seconds: float) -> int:
        res = await self.conn.execute(
            text(
                "UPDATE ingest_jobs SET status = 'queued', locked_at = NULL, locked_by = NULL "
                "WHERE status = 'running' AND locked_at < now() - make_interval(secs => :t)"
            ),
            {"t": timeout_seconds},
        )
        return int(res.rowcount)

    async def queue_length(self) -> int:
        row = (
            (
                await self.conn.execute(
                    text("SELECT count(*) AS n FROM ingest_jobs WHERE status = 'queued'")
                )
            )
            .mappings()
            .first()
        )
        return int(row["n"]) if row else 0


class PgIngestDocuments:
    def __init__(self, conn: AsyncConnection) -> None:
        self.conn = conn

    async def get(self, document_id: UUID) -> Document | None:
        row = (
            (
                await self.conn.execute(
                    text(f"SELECT {_DOC_COLS} FROM documents WHERE id = :id"), {"id": document_id}
                )
            )
            .mappings()
            .first()
        )
        return _doc(row) if row else None

    async def mark_ready(self, document_id: UUID, page_count: int, now: datetime) -> bool:
        res = await self.conn.execute(
            text(
                "UPDATE documents SET status = 'ready', page_count = :p, processed_at = :t, "
                "error_code = NULL WHERE id = :id AND status = 'processing'"
            ),
            {"id": document_id, "p": page_count, "t": now},
        )
        return bool(res.rowcount)

    async def mark_error(self, document_id: UUID, error_code: str, now: datetime) -> bool:
        res = await self.conn.execute(
            text(
                "UPDATE documents SET status = 'error', error_code = :e, processed_at = :t "
                "WHERE id = :id AND status = 'processing'"
            ),
            {"id": document_id, "e": error_code, "t": now},
        )
        return bool(res.rowcount)


class PgChunkWriter:
    def __init__(self, conn: AsyncConnection) -> None:
        self.conn = conn

    async def replace(
        self, document_id: UUID, user_id: UUID, model: str, chunks: Sequence[NewChunk]
    ) -> bool:
        # Khóa dòng tài liệu: nếu API xóa đồng thời, ta thấy ngay (hoặc chờ rồi thấy không còn).
        alive = (
            (
                await self.conn.execute(
                    text("SELECT 1 AS ok FROM documents WHERE id = :id FOR SHARE"),
                    {"id": document_id},
                )
            )
            .mappings()
            .first()
        )
        if alive is None:
            return False
        await self.conn.execute(
            text("DELETE FROM chunks WHERE document_id = :d"), {"d": document_id}
        )
        if chunks:
            await self.conn.execute(
                text(
                    "INSERT INTO chunks (document_id, user_id, ordinal, page_start, page_end, text, "
                    "token_count, embedding, embedding_model) VALUES (:d, :u, :o, :ps, :pe, :t, :n, "
                    "CAST(:e AS vector), :m)"
                ),
                [
                    {
                        "d": document_id, "u": user_id, "o": c.ordinal, "ps": c.page_start,
                        "pe": c.page_end, "t": c.text, "n": c.token_count,
                        "e": vector_literal(c.embedding), "m": model,
                    }
                    for c in chunks
                ],
            )  # fmt: skip
        return True


class PgWorkerUnitOfWork:
    jobs: PgIngestJobs
    documents: PgIngestDocuments
    chunks: PgChunkWriter

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._cm: Any = None

    async def __aenter__(self) -> PgWorkerUnitOfWork:
        self._cm = system_transaction(self._engine)
        conn = await self._cm.__aenter__()
        self.jobs, self.documents, self.chunks = (
            PgIngestJobs(conn),
            PgIngestDocuments(conn),
            PgChunkWriter(conn),
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self._cm.__aexit__(exc_type, exc, tb)


class PgWorkerUnitOfWorkFactory:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    def begin(self) -> PgWorkerUnitOfWork:
        return PgWorkerUnitOfWork(self._engine)
