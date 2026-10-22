"""C2 + C6: pipeline ingest đầu-cuối trên adapter trong bộ nhớ (PDF thật, pypdf thật)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from docchat_core.application.ingest import BACKOFF_BASE_SECONDS, STALE_JOB_SECONDS, IngestService
from docchat_core.config import AppConfig
from docchat_core.domain import Document, DocumentStatus
from docchat_core.ports.ingest import EmbeddingError
from docchat_infra.embedding import FakeEmbedding
from docchat_infra.memory import (
    InMemoryFileStorage,
    MemoryStore,
    MemoryUnitOfWorkFactory,
    MemoryWorkerUnitOfWorkFactory,
)
from docchat_infra.pdf import PypdfExtractor
from docchat_infra.pdf.synthetic import encrypt_pdf, make_pdf

DIM = 64
SENT = "Điều khoản thanh toán quy định thời hạn và phương thức thanh toán giữa hai bên. "
T0 = datetime(2026, 10, 22, 8, 0, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now


class Cfg:
    def __init__(self, **values: Any) -> None:
        self.values = values

    async def load_all(self) -> dict[str, Any]:
        return dict(self.values)


class SpyMetrics:
    def __init__(self) -> None:
        self.stages: list[str] = []
        self.seconds: list[float] = []
        self.lengths: list[int] = []

    def stage_error(self, stage: str) -> None:
        self.stages.append(stage)

    def ingest_seconds(self, seconds: float) -> None:
        self.seconds.append(seconds)

    def queue_length(self, length: int) -> None:
        self.lengths.append(length)


class FlakyEmbedding(FakeEmbedding):
    def __init__(self, fail_times: int = 0, retryable: bool = True, dim: int = DIM) -> None:
        super().__init__(dim)
        self.fail_times, self.retryable, self.calls = fail_times, retryable, 0
        self.on_call: Callable[[], None] | None = None

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls += 1
        if self.on_call:
            self.on_call()
        if self.calls <= self.fail_times:
            raise EmbeddingError("boom", retryable=self.retryable)
        return await super().embed_documents(texts)


class Rig:
    def __init__(self, embedder: FlakyEmbedding | None = None, **config: Any) -> None:
        self.clock = Clock()
        self.store = MemoryStore()
        self.storage = InMemoryFileStorage()
        self.embedder = embedder or FlakyEmbedding()
        self.metrics = SpyMetrics()
        self.api = MemoryUnitOfWorkFactory(self.store)
        self.service = IngestService(
            MemoryWorkerUnitOfWorkFactory(self.store, self.clock),
            self.storage,
            PypdfExtractor(),
            self.embedder,
            AppConfig(
                Cfg(chunk_tokens=120, chunk_overlap_tokens=20, chunk_min_tokens=5, **config),
                ttl_seconds=0,
            ),
            worker_id="w1",
            metrics=self.metrics,
            clock=self.clock,
        )
        self.user = uuid4()

    async def upload(self, data: bytes, name: str = "a.pdf") -> UUID:
        """Mô phỏng API: lưu tệp, tạo tài liệu `processing`, xếp job."""
        doc_id = uuid4()
        key = f"{self.user}/{doc_id}.pdf"
        self.storage.objects[key] = data
        doc = Document(doc_id, self.user, name, len(data), key, self.clock())
        async with self.api.for_user(self.user) as uow:
            await uow.documents.add(doc)
            await uow.jobs.enqueue(doc_id, {"traceparent": "00-aa-bb-01"})
        return doc_id

    def doc(self, doc_id: UUID) -> Document | None:
        return self.store.documents.get(doc_id)

    def chunks(self, doc_id: UUID) -> list[dict[str, Any]]:
        rows = [r for r in self.store.chunk_rows.values() if r["document_id"] == doc_id]
        return sorted(rows, key=lambda r: r["ordinal"])

    def job(self, doc_id: UUID) -> dict[str, Any]:
        return self.store.job_rows[doc_id]


def pdf(pages: int = 3) -> bytes:
    return make_pdf([f"Trang {i}\n" + SENT * 6 for i in range(1, pages + 1)])


@pytest.fixture()
def rig() -> Rig:
    return Rig()


# ---------- thành công ----------
async def test_pdf_becomes_ready_with_chunks_pages_and_embeddings(rig: Rig) -> None:
    doc_id = await rig.upload(pdf(3))
    assert await rig.service.process_next() is True

    doc = rig.doc(doc_id)
    assert doc and doc.status is DocumentStatus.READY and doc.page_count == 3
    assert doc.processed_at == T0
    chunks = rig.chunks(doc_id)
    assert len(chunks) >= 3
    assert [c["ordinal"] for c in chunks] == list(range(len(chunks)))
    for c in chunks:
        assert 1 <= c["page_start"] <= c["page_end"] <= 3 and c["page_end"] - c["page_start"] <= 1
        assert len(c["embedding"]) == DIM and c["model"] == rig.embedder.model
        assert c["user_id"] == rig.user
        assert (
            c["embedding"] == (await rig.embedder.embed_documents([c["text"]]))[0]
        )  # đúng thứ tự lô
    assert rig.job(doc_id)["status"] == "done"
    assert rig.metrics.seconds and rig.metrics.stages == []


async def test_job_carries_trace_context_and_queue_length_is_reported(rig: Rig) -> None:
    doc_id = await rig.upload(pdf(1))
    assert rig.job(doc_id)["trace_context"] == {"traceparent": "00-aa-bb-01"}
    await rig.service.process_next()
    assert rig.metrics.lengths == [1]


async def test_empty_queue_returns_false(rig: Rig) -> None:
    assert await rig.service.process_next() is False


async def test_many_chunks_are_embedded_in_batches_preserving_order() -> None:
    rig = Rig(embed_batch_size=4)
    doc_id = await rig.upload(make_pdf([SENT * 60]))
    await rig.service.process_next()
    chunks = rig.chunks(doc_id)
    assert len(chunks) > 8 and rig.embedder.calls == -(-len(chunks) // 4)
    for c in chunks:
        assert c["embedding"] == (await rig.embedder.embed_documents([c["text"]]))[0]


# ---------- lỗi vĩnh viễn: không thử lại ----------
@pytest.mark.parametrize(
    ("data", "code"),
    [
        (make_pdf(["", ""]), "NO_TEXT"),  # PDF quét
        (encrypt_pdf(make_pdf(["bí mật"]), "pw"), "PDF_PASSWORD"),
        (b"%PDF-1.4 rac khong phai pdf", "PDF_CORRUPT"),
    ],
)
async def test_unreadable_pdf_is_marked_error_without_retry(
    rig: Rig, data: bytes, code: str
) -> None:
    doc_id = await rig.upload(data)
    await rig.service.process_next()
    doc = rig.doc(doc_id)
    assert doc and doc.status is DocumentStatus.ERROR and doc.error_code == code
    assert rig.chunks(doc_id) == []
    assert rig.job(doc_id)["status"] == "done"  # không xếp lại
    assert rig.embedder.calls == 0 and rig.metrics.stages == ["extract"]


async def test_too_many_pages_is_rejected() -> None:
    rig = Rig(max_pdf_pages=2)
    doc_id = await rig.upload(pdf(3))
    await rig.service.process_next()
    assert rig.doc(doc_id).error_code == "PDF_TOO_MANY_PAGES"  # type: ignore[union-attr]


async def test_one_bad_file_does_not_affect_others(rig: Rig) -> None:
    bad = await rig.upload(b"nope")
    good = await rig.upload(pdf(2))
    await rig.service.process_next()
    await rig.service.process_next()
    assert rig.doc(bad).status is DocumentStatus.ERROR  # type: ignore[union-attr]
    assert rig.doc(good).status is DocumentStatus.READY  # type: ignore[union-attr]


async def test_non_retryable_embedding_error_is_permanent() -> None:
    rig = Rig(FlakyEmbedding(fail_times=99, retryable=False))
    doc_id = await rig.upload(pdf(1))
    await rig.service.process_next()
    assert rig.doc(doc_id).error_code == "EMBEDDING_FAILED"  # type: ignore[union-attr]
    assert rig.job(doc_id)["status"] == "done" and rig.embedder.calls == 1


# ---------- lỗi tạm thời: thử lại có backoff ----------
async def test_transient_embedding_failure_retries_with_backoff_then_succeeds() -> None:
    rig = Rig(FlakyEmbedding(fail_times=1))
    doc_id = await rig.upload(pdf(1))
    await rig.service.process_next()

    job = rig.job(doc_id)
    assert (
        job["status"] == "queued"
        and job["attempts"] == 1
        and job["last_error"] == "EMBEDDING_FAILED"
    )
    assert job["run_after"] == T0 + timedelta(seconds=BACKOFF_BASE_SECONDS)
    assert rig.doc(doc_id).status is DocumentStatus.PROCESSING  # type: ignore[union-attr]
    assert await rig.service.process_next() is False  # chưa đến hạn

    rig.clock.now = T0 + timedelta(seconds=BACKOFF_BASE_SECONDS + 1)
    assert await rig.service.process_next() is True
    assert rig.doc(doc_id).status is DocumentStatus.READY  # type: ignore[union-attr]
    assert rig.job(doc_id)["status"] == "done" and rig.job(doc_id)["attempts"] == 2


async def test_gives_up_after_max_attempts_and_marks_error() -> None:
    rig = Rig(FlakyEmbedding(fail_times=99))
    doc_id = await rig.upload(pdf(1))
    for _ in range(3):
        rig.clock.now += timedelta(hours=1)
        await rig.service.process_next()
    doc = rig.doc(doc_id)
    assert doc and doc.status is DocumentStatus.ERROR and doc.error_code == "EMBEDDING_FAILED"
    assert rig.job(doc_id)["status"] == "failed" and rig.job(doc_id)["attempts"] == 3
    assert rig.metrics.stages == ["embed"] * 3


async def test_storage_failure_retries_then_reports_storage_error(rig: Rig) -> None:
    doc_id = await rig.upload(pdf(1))
    del rig.storage.objects[rig.doc(doc_id).storage_key]  # type: ignore[union-attr]
    for _ in range(3):
        rig.clock.now += timedelta(hours=1)
        await rig.service.process_next()
    assert rig.doc(doc_id).error_code == "STORAGE_ERROR"  # type: ignore[union-attr]


async def test_wrong_embedding_dimension_is_not_written() -> None:
    class Wrong(FlakyEmbedding):
        async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
            return [[0.0] * (DIM - 1) for _ in texts]

    rig = Rig(Wrong())
    doc_id = await rig.upload(pdf(1))
    await rig.service.process_next()
    assert rig.chunks(doc_id) == [] and rig.job(doc_id)["status"] == "queued"


async def test_unexpected_crash_is_retried_and_eventually_reported(rig: Rig) -> None:
    class Boom:
        def extract(self, data: bytes, *, max_pages: int) -> list[Any]:
            raise RuntimeError("nội dung bí mật trong lỗi")

    rig.service._extractor = Boom()  # type: ignore[assignment]
    doc_id = await rig.upload(pdf(1))
    for _ in range(3):
        rig.clock.now += timedelta(hours=1)
        await rig.service.process_next()
    assert rig.doc(doc_id).error_code == "INGEST_FAILED"  # type: ignore[union-attr]


# ---------- idempotent / đồng thời ----------
async def test_rerun_does_not_duplicate_chunks(rig: Rig) -> None:
    doc_id = await rig.upload(pdf(2))
    await rig.service.process_next()
    first = [c["text"] for c in rig.chunks(doc_id)]

    # Giả lập worker chết sau khi ghi chunk nhưng trước khi xong job: tài liệu quay về processing.
    rig.store.documents[doc_id].status = DocumentStatus.PROCESSING
    rig.store.documents[doc_id].processed_at = None
    rig.job(doc_id).update(status="queued")
    await rig.service.process_next()
    assert [c["text"] for c in rig.chunks(doc_id)] == first
    assert len(rig.store.chunk_rows) == len(first)


async def test_rerun_on_already_ready_document_is_a_noop(rig: Rig) -> None:
    doc_id = await rig.upload(pdf(1))
    await rig.service.process_next()
    n_calls = rig.embedder.calls
    rig.job(doc_id).update(status="queued")
    await rig.service.process_next()
    assert rig.embedder.calls == n_calls and rig.job(doc_id)["status"] == "done"


async def test_document_deleted_while_processing_leaves_no_chunks() -> None:
    rig = Rig()
    doc_id = await rig.upload(pdf(2))

    def delete_now() -> None:
        rig.store.documents.pop(doc_id, None)  # người dùng xóa đúng lúc đang embed

    rig.embedder.on_call = delete_now
    await rig.service.process_next()
    assert rig.chunks(doc_id) == [] and rig.store.chunk_rows == {}
    assert rig.job(doc_id)["status"] == "done"


async def test_job_for_deleted_document_completes_quietly(rig: Rig) -> None:
    doc_id = await rig.upload(pdf(1))
    del rig.store.documents[doc_id]
    assert await rig.service.process_next() is True
    assert rig.job(doc_id)["status"] == "done" and rig.embedder.calls == 0


async def test_stale_running_job_is_requeued_and_processed(rig: Rig) -> None:
    doc_id = await rig.upload(pdf(1))
    rig.job(doc_id).update(
        status="running", attempts=1, locked_at=T0 - timedelta(seconds=STALE_JOB_SECONDS + 1)
    )  # worker cũ đã chết
    assert await rig.service.process_next() is True
    assert rig.doc(doc_id).status is DocumentStatus.READY  # type: ignore[union-attr]


async def test_fresh_running_job_is_left_alone(rig: Rig) -> None:
    doc_id = await rig.upload(pdf(1))
    rig.job(doc_id).update(status="running", attempts=1, locked_at=T0)
    assert await rig.service.process_next() is False  # worker khác đang xử lý


async def test_two_workers_never_take_the_same_job(rig: Rig) -> None:
    a, b = await rig.upload(pdf(1)), await rig.upload(pdf(1))
    other = MemoryWorkerUnitOfWorkFactory(rig.store, rig.clock)
    async with other.begin() as u1, other.begin() as u2:
        j1, j2 = await u1.jobs.claim("w1"), await u2.jobs.claim("w2")
        assert j1 and j2 and {j1.document_id, j2.document_id} == {a, b}
        assert await u1.jobs.claim("w1") is None


# ---------- riêng tư ----------
async def test_pdf_text_never_reaches_logs(rig: Rig, caplog: pytest.LogCaptureFixture) -> None:
    secret = "MAT-KHAU-CANARY-98765"
    rig.service._extractor = _Failing()  # type: ignore[assignment]
    doc_id = await rig.upload(make_pdf([f"{SENT} {secret}"]))
    with caplog.at_level(logging.DEBUG):
        await rig.service.process_next()
    assert secret not in caplog.text and secret not in str([r.__dict__ for r in caplog.records])
    assert rig.doc(doc_id) is not None


class _Failing:
    def extract(self, data: bytes, *, max_pages: int) -> list[Any]:
        text = data.decode("latin-1")
        raise RuntimeError(f"lỗi kèm nội dung: {text[:200]}")
