"""Triển khai trong bộ nhớ của các cổng worker ingest (test và benchmark)."""

from __future__ import annotations

import copy
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from types import TracebackType
from typing import Any
from uuid import UUID, uuid4

from docchat_core.domain import Document, DocumentStatus
from docchat_core.ports.ingest import IngestJob, NewChunk
from docchat_infra.memory.store import MemoryStore


def _now() -> datetime:
    return datetime.now(UTC)


class MemIngestJobs:
    def __init__(self, store: MemoryStore, clock: Callable[[], datetime]) -> None:
        self.s, self.clock = store, clock

    def _rows(self) -> list[tuple[UUID, dict[str, Any]]]:
        return sorted(self.s.job_rows.items(), key=lambda kv: kv[1]["id"])

    async def claim(self, worker_id: str) -> IngestJob | None:
        now = self.clock()
        for doc_id, row in self._rows():
            due = row["run_after"] is None or row["run_after"] <= now
            if row["status"] == "queued" and due:
                row.update(status="running", locked_at=now, attempts=row["attempts"] + 1)
                return IngestJob(row["id"], doc_id, row["attempts"], dict(row["trace_context"]))
        return None

    def _by_id(self, job_id: int) -> dict[str, Any]:
        return next(r for r in self.s.job_rows.values() if r["id"] == job_id)

    async def complete(self, job_id: int) -> None:
        self._by_id(job_id).update(status="done", locked_at=None, last_error=None)

    async def retry(self, job_id: int, delay_seconds: float, error_code: str) -> None:
        self._by_id(job_id).update(
            status="queued",
            locked_at=None,
            last_error=error_code,
            run_after=self.clock() + timedelta(seconds=delay_seconds),
        )

    async def fail(self, job_id: int, error_code: str) -> None:
        self._by_id(job_id).update(status="failed", locked_at=None, last_error=error_code)

    async def requeue_stale(self, timeout_seconds: float) -> int:
        limit = self.clock() - timedelta(seconds=timeout_seconds)
        n = 0
        for row in self.s.job_rows.values():
            if row["status"] == "running" and row["locked_at"] < limit:
                row.update(status="queued", locked_at=None)
                n += 1
        return n

    async def queue_length(self) -> int:
        return sum(1 for r in self.s.job_rows.values() if r["status"] == "queued")


class MemIngestDocuments:
    def __init__(self, store: MemoryStore) -> None:
        self.s = store

    async def get(self, document_id: UUID) -> Document | None:
        d = self.s.documents.get(document_id)
        return copy.copy(d) if d else None

    async def mark_ready(self, document_id: UUID, page_count: int, now: datetime) -> bool:
        d = self.s.documents.get(document_id)
        if d is None or d.status is not DocumentStatus.PROCESSING:
            return False
        d.mark_ready(page_count, now)
        return True

    async def mark_error(self, document_id: UUID, error_code: str, now: datetime) -> bool:
        d = self.s.documents.get(document_id)
        if d is None or d.status is not DocumentStatus.PROCESSING:
            return False
        d.mark_error(error_code, now)
        return True


class MemChunkWriter:
    def __init__(self, store: MemoryStore) -> None:
        self.s = store

    async def replace(
        self, document_id: UUID, user_id: UUID, model: str, chunks: Sequence[NewChunk]
    ) -> bool:
        if document_id not in self.s.documents:
            return False
        for cid in [c for c, r in self.s.chunk_rows.items() if r["document_id"] == document_id]:
            del self.s.chunk_rows[cid]
            self.s.chunk_text.pop(cid, None)
        for c in chunks:
            cid = uuid4()
            self.s.chunk_rows[cid] = {
                "id": cid,
                "document_id": document_id,
                "user_id": user_id,
                "ordinal": c.ordinal,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "text": c.text,
                "token_count": c.token_count,
                "embedding": list(c.embedding),
                "model": model,
            }
            self.s.chunk_text[cid] = (document_id, c.text)
        return True


class MemoryWorkerUnitOfWork:
    def __init__(self, store: MemoryStore, clock: Callable[[], datetime]) -> None:
        self._store = store
        self._snap: dict[str, Any] | None = None
        self.jobs = MemIngestJobs(store, clock)
        self.documents = MemIngestDocuments(store)
        self.chunks = MemChunkWriter(store)

    async def __aenter__(self) -> MemoryWorkerUnitOfWork:
        self._snap = self._store.snapshot()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None and self._snap is not None:
            self._store.restore(self._snap)
        self._snap = None


class MemoryWorkerUnitOfWorkFactory:
    def __init__(self, store: MemoryStore, clock: Callable[[], datetime] = _now) -> None:
        self.store, self.clock = store, clock

    def begin(self) -> MemoryWorkerUnitOfWork:
        return MemoryWorkerUnitOfWork(self.store, self.clock)
