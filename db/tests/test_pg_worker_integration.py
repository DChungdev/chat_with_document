"""Hàng đợi + ghi chỉ mục trên PostgreSQL thật (cần Docker; chạy trong CI bằng `-m integration`)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import psycopg
import pytest
import pytest_asyncio

from docchat_core.application.ingest import IngestService
from docchat_core.config import AppConfig
from docchat_core.domain import Document, DocumentStatus, UserRole
from docchat_core.ports.ingest import NewChunk
from docchat_infra.embedding import FakeEmbedding
from docchat_infra.memory import InMemoryFileStorage
from docchat_infra.pdf import PypdfExtractor
from docchat_infra.pdf.synthetic import make_pdf
from docchat_infra.persistence import (
    PgUnitOfWorkFactory,
    PgWorkerUnitOfWorkFactory,
    PostgresConfigStore,
    create_engine,
)

pytestmark = pytest.mark.integration

DIM = 1024  # khớp EMBEDDING_DIM mặc định của migration
SENT = "Điều khoản thanh toán quy định thời hạn và phương thức thanh toán giữa hai bên. "


def url(migrated: Any, dsn_for: Any, role: str) -> str:
    return dsn_for(migrated, role).replace("postgresql://", "postgresql+psycopg://")


@pytest_asyncio.fixture()
async def rig(migrated: Any, dsn_for: Any) -> AsyncIterator[dict[str, Any]]:
    api = create_engine(url(migrated, dsn_for, "docchat_api"), pool_size=2)
    worker = create_engine(url(migrated, dsn_for, "docchat_worker"), pool_size=4)
    yield {
        "api": PgUnitOfWorkFactory(api),
        "worker": PgWorkerUnitOfWorkFactory(worker),
        "worker_engine": worker,
        "dsn": lambda role: dsn_for(migrated, role),
        "su": lambda: psycopg.connect(dsn_for(migrated, "postgres", "postgres"), autocommit=True),
    }
    await api.dispose()
    await worker.dispose()


async def upload(rig: dict[str, Any], data: bytes | None = None, storage: Any = None) -> Document:
    async with rig["api"].system() as uow:
        user = await uow.users.upsert_by_subject(f"it|{uuid4()}", UserRole.USER)
    did = uuid4()
    doc = Document(
        did, user.id, "a.pdf", len(data or b"x"), f"{user.id}/{did}.pdf", datetime.now(UTC)
    )
    if storage is not None and data is not None:
        storage.objects[doc.storage_key] = data
    async with rig["api"].for_user(user.id) as uow:
        await uow.documents.add(doc)
        await uow.jobs.enqueue(did, {"traceparent": "00-aa-bb-01"})
    return doc


def drain(rig: dict[str, Any]) -> None:
    """Dọn hàng đợi của các test trước để test claim xác định."""
    with rig["su"]() as c:
        c.execute(
            "UPDATE docchat.ingest_jobs SET status = 'done' WHERE status IN ('queued','running')"
        )


async def test_claim_returns_job_once_with_trace_context(rig: dict[str, Any]) -> None:
    drain(rig)
    doc = await upload(rig)
    async with rig["worker"].begin() as uow:
        job = await uow.jobs.claim("w1")
    assert job and job.document_id == doc.id and job.attempts == 1
    assert job.trace_context == {"traceparent": "00-aa-bb-01"}
    async with rig["worker"].begin() as uow:
        assert await uow.jobs.claim("w2") is None  # đã bị khóa
        assert await uow.jobs.queue_length() == 0


async def test_concurrent_workers_get_different_jobs_skip_locked(rig: dict[str, Any]) -> None:
    drain(rig)
    a, b = await upload(rig), await upload(rig)
    async with rig["worker"].begin() as u1, rig["worker"].begin() as u2:
        j1 = await u1.jobs.claim("w1")  # giữ giao dịch mở: dòng đang bị khóa
        j2 = await u2.jobs.claim("w2")
        assert j1 and j2 and {j1.document_id, j2.document_id} == {a.id, b.id}


async def test_retry_delays_and_stale_running_jobs_are_requeued(rig: dict[str, Any]) -> None:
    drain(rig)
    doc = await upload(rig)
    async with rig["worker"].begin() as uow:
        job = await uow.jobs.claim("w1")
        assert job
        await uow.jobs.retry(job.id, 3600, "EMBEDDING_FAILED")
    async with rig["worker"].begin() as uow:
        assert await uow.jobs.claim("w1") is None  # chưa đến hạn thử lại

    with rig["su"]() as c:  # giả lập: đến hạn, bị nhận rồi worker chết từ 20 phút trước
        c.execute(
            "UPDATE docchat.ingest_jobs SET run_after = now() - interval '1 minute' WHERE document_id=%s",
            (doc.id,),
        )
    async with rig["worker"].begin() as uow:
        assert (await uow.jobs.claim("w1")) is not None
    with rig["su"]() as c:
        c.execute(
            "UPDATE docchat.ingest_jobs SET locked_at = now() - interval '20 minutes' WHERE document_id=%s",
            (doc.id,),
        )
    async with rig["worker"].begin() as uow:
        assert await uow.jobs.requeue_stale(600) == 1
        again = await uow.jobs.claim("w2")
    assert again and again.attempts == 3  # tăng ở mỗi lần nhận


async def test_chunk_replace_is_idempotent_and_vectors_are_searchable(rig: dict[str, Any]) -> None:
    doc = await upload(rig)
    emb = FakeEmbedding(DIM)
    texts = ["thanh toán trong 30 ngày", "bảo hành thiết bị 12 tháng"]
    vecs = await emb.embed_documents(texts)
    chunks = [
        NewChunk(i, i + 1, i + 1, t, 5, v) for i, (t, v) in enumerate(zip(texts, vecs, strict=True))
    ]
    for _ in range(2):  # chạy hai lần: không trùng
        async with rig["worker"].begin() as uow:
            assert await uow.chunks.replace(doc.id, doc.user_id, "fake-bow-v1", chunks) is True
    with rig["su"]() as c:
        n = c.execute(
            "SELECT count(*) FROM docchat.chunks WHERE document_id=%s", (doc.id,)
        ).fetchone()
        assert n == (2,)
        q = await emb.embed_query("thời hạn thanh toán")
        lit = "[" + ",".join(map(repr, q)) + "]"
        best = c.execute(
            "SELECT text, page_start, embedding_model FROM docchat.chunks WHERE document_id=%s "
            "ORDER BY embedding <=> %s::vector LIMIT 1",
            (doc.id, lit),
        ).fetchone()
    assert best == ("thanh toán trong 30 ngày", 1, "fake-bow-v1")


async def test_replace_on_deleted_document_writes_nothing(rig: dict[str, Any]) -> None:
    doc = await upload(rig)
    async with rig["api"].for_user(doc.user_id) as uow:
        await uow.documents.delete(doc.id)
    async with rig["worker"].begin() as uow:
        ok = await uow.chunks.replace(
            doc.id, doc.user_id, "m", [NewChunk(0, 1, 1, "t", 1, [0.0] * DIM)]
        )
    assert ok is False


async def test_mark_ready_and_error_only_from_processing(rig: dict[str, Any]) -> None:
    doc = await upload(rig)
    now = datetime.now(UTC)
    async with rig["worker"].begin() as uow:
        assert await uow.documents.mark_ready(doc.id, 3, now) is True
        assert await uow.documents.mark_ready(doc.id, 3, now) is False
        assert await uow.documents.mark_error(doc.id, "NO_TEXT", now) is False
    async with rig["api"].for_user(doc.user_id) as uow:
        got = await uow.documents.get(doc.id)
    assert got and got.status is DocumentStatus.READY and got.page_count == 3


async def test_full_pipeline_on_postgres(rig: dict[str, Any], migrated: Any, dsn_for: Any) -> None:
    drain(rig)
    storage = InMemoryFileStorage()
    pdf = make_pdf([f"Trang {i}\n" + SENT * 8 for i in range(1, 4)])
    doc = await upload(rig, pdf, storage)
    config = AppConfig(PostgresConfigStore(rig["worker_engine"]), ttl_seconds=0)
    service = IngestService(
        rig["worker"], storage, PypdfExtractor(), FakeEmbedding(DIM), config, worker_id="it"
    )
    assert await service.process_next() is True

    async with rig["api"].for_user(doc.user_id) as uow:
        got = await uow.documents.get(doc.id)
    assert got and got.status is DocumentStatus.READY and got.page_count == 3
    with rig["su"]() as c:
        rows = c.execute(
            "SELECT ordinal, page_start, page_end, embedding_model, vector_dims(embedding) "
            "FROM docchat.chunks WHERE document_id=%s ORDER BY ordinal",
            (doc.id,),
        ).fetchall()
        job = c.execute(
            "SELECT status FROM docchat.ingest_jobs WHERE document_id=%s", (doc.id,)
        ).fetchone()
    assert len(rows) >= 3 and [r[0] for r in rows] == list(range(len(rows)))
    assert all(1 <= r[1] <= r[2] <= 3 and r[3] == "fake-bow-v1" and r[4] == DIM for r in rows)
    assert job == ("done",)


async def test_concurrent_delete_during_processing_is_handled(rig: dict[str, Any]) -> None:
    drain(rig)
    storage = InMemoryFileStorage()
    doc = await upload(rig, make_pdf([SENT * 6]), storage)

    class DeletingEmbedding(FakeEmbedding):
        async def embed_documents(self, texts: Any) -> list[list[float]]:
            async with rig["api"].for_user(doc.user_id) as uow:  # người dùng xóa giữa chừng
                await uow.documents.delete(doc.id)
            return await super().embed_documents(texts)

    config = AppConfig(PostgresConfigStore(rig["worker_engine"]), ttl_seconds=0)
    service = IngestService(
        rig["worker"], storage, PypdfExtractor(), DeletingEmbedding(DIM), config, worker_id="it"
    )
    await asyncio.wait_for(service.process_next(), timeout=30)
    with rig["su"]() as c:
        assert c.execute(
            "SELECT count(*) FROM docchat.chunks WHERE document_id=%s", (doc.id,)
        ).fetchone() == (0,)
