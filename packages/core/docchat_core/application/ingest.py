"""Pipeline ingest: nhận job → tải PDF → trích xuất → chunk → embed → ghi chỉ mục → `ready` (C6).

Tách lỗi vĩnh viễn (PDF hỏng/mật khẩu/không có văn bản ⇒ tài liệu `error`, không thử lại) khỏi lỗi
tạm thời (embedding/lưu trữ/CSDL ⇒ thử lại có backoff, quá số lần mới đánh `error`).
Idempotent: chạy lại job xóa chunk cũ trước khi ghi. Không bao giờ ghi nội dung vào log.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable, Sequence

from docchat_core.application.chunking import ChunkDraft, ChunkingConfig, chunk_pages, clean_pages
from docchat_core.application.common import Clock, utc_now
from docchat_core.config import AppConfig
from docchat_core.domain import DocumentStatus
from docchat_core.ports import FileStoragePort
from docchat_core.ports.ingest import (
    EMBEDDING_FAILED,
    INGEST_FAILED,
    NO_TEXT,
    STORAGE_ERROR,
    EmbeddingError,
    EmbeddingPort,
    ExtractionError,
    IngestJob,
    IngestMetrics,
    NewChunk,
    PageText,
    PdfExtractor,
    WorkerUnitOfWorkFactory,
)

logger = logging.getLogger(__name__)

BACKOFF_BASE_SECONDS = 30.0  # lần thử lại thứ n chờ 30 · 2^(n-1) giây [Đề xuất]
STALE_JOB_SECONDS = 600.0  # worker chết giữa chừng: sau 10 phút job được nhận lại
EMBED_CONCURRENCY = 3  # 2–4 lô song song (VectorDB mục 7)


class _NoMetrics:
    def stage_error(self, stage: str) -> None:
        pass

    def ingest_seconds(self, seconds: float) -> None:
        pass

    def queue_length(self, length: int) -> None:
        pass


class _Permanent(Exception):
    """Lỗi vĩnh viễn không phải do PDF (vd. embedding từ chối đầu vào): đánh `error`, không thử lại."""

    def __init__(self, stage: str, code: str) -> None:
        super().__init__(stage)
        self.stage = stage
        self.code = code


class _Retry(Exception):
    """Lỗi tạm thời: thử lại job."""

    def __init__(self, stage: str, final_code: str) -> None:
        super().__init__(stage)
        self.stage = stage
        self.final_code = final_code


class IngestService:
    def __init__(
        self,
        uow_factory: WorkerUnitOfWorkFactory,
        storage: FileStoragePort,
        extractor: PdfExtractor,
        embedder: EmbeddingPort,
        config: AppConfig,
        *,
        worker_id: str = "worker",
        metrics: IngestMetrics | None = None,
        clock: Clock = utc_now,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._uow = uow_factory
        self._storage = storage
        self._extractor = extractor
        self._embedder = embedder
        self._config = config
        self._worker_id = worker_id
        self._metrics: IngestMetrics = metrics or _NoMetrics()
        self._clock = clock
        self._mono = monotonic
        self._sleep = sleep

    # ---------- vòng lặp ----------
    async def process_next(self) -> bool:
        """Nhận và xử lý đúng một job. False nếu hàng đợi trống."""
        async with self._uow.begin() as uow:
            await uow.jobs.requeue_stale(STALE_JOB_SECONDS)
            self._metrics.queue_length(await uow.jobs.queue_length())
            job = await uow.jobs.claim(self._worker_id)  # commit ngay để khóa job
        if job is None:
            return False
        await self.run_job(job)
        return True

    async def run_forever(self, stop: asyncio.Event, poll_interval: float = 2.0) -> None:
        while not stop.is_set():
            try:
                worked = await self.process_next()
            except Exception:
                logger.error(
                    "ingest loop error", extra={"event": "ingest_loop_error"}, exc_info=True
                )
                worked = False
            if not worked:
                try:
                    await asyncio.wait_for(stop.wait(), timeout=poll_interval)
                except TimeoutError:
                    pass

    # ---------- một job ----------
    async def run_job(self, job: IngestJob) -> None:
        started = self._mono()
        extra = {"job_id": job.id, "document_id": str(job.document_id), "attempt": job.attempts}
        max_attempts = int(await self._config.get("ingest_max_attempts"))
        try:
            outcome = await self._process(job)
        except ExtractionError as exc:
            self._metrics.stage_error("extract")
            await self._finish_with_error(job, exc.code)
            logger.info("document rejected", extra={**extra, "error_code": exc.code})
            return
        except _Permanent as exc:
            self._metrics.stage_error(exc.stage)
            await self._finish_with_error(job, exc.code)
            logger.info(
                "document rejected", extra={**extra, "stage": exc.stage, "error_code": exc.code}
            )
            return
        except _Retry as exc:
            self._metrics.stage_error(exc.stage)
            if job.attempts >= max_attempts:
                await self._finish_with_error(job, exc.final_code, failed=True)
                logger.error("ingest gave up", extra={**extra, "stage": exc.stage})
            else:
                delay = BACKOFF_BASE_SECONDS * 2 ** (job.attempts - 1)
                async with self._uow.begin() as uow:
                    await uow.jobs.retry(job.id, delay, exc.final_code)
                logger.warning("ingest will retry", extra={**extra, "stage": exc.stage})
            return
        except Exception as exc:
            self._metrics.stage_error("write")
            logger.error(
                "ingest crashed",
                extra={**extra, "stage": "write", "exc_type": type(exc).__name__},
            )
            if job.attempts >= max_attempts:
                await self._finish_with_error(job, INGEST_FAILED, failed=True)
            else:
                async with self._uow.begin() as uow:
                    await uow.jobs.retry(
                        job.id, BACKOFF_BASE_SECONDS * 2 ** (job.attempts - 1), INGEST_FAILED
                    )
            return
        if outcome:  # chỉ đo thời gian của lần xử lý thành công
            self._metrics.ingest_seconds(self._mono() - started)
        logger.info("ingest finished", extra=extra)

    async def _process(self, job: IngestJob) -> bool:
        """True nếu đã ghi chỉ mục; False nếu không còn việc (tài liệu đã xóa/đã xử lý)."""
        async with self._uow.begin() as uow:
            doc = await uow.documents.get(job.document_id)
        if doc is None or doc.status is not DocumentStatus.PROCESSING:
            async with self._uow.begin() as uow:  # đã xóa hoặc đã xử lý xong (job chạy lại)
                await uow.jobs.complete(job.id)
            return False

        try:
            data = await self._storage.get(doc.storage_key)
        except Exception as exc:
            raise _Retry("extract", STORAGE_ERROR) from exc

        max_pages = int(await self._config.get("max_pdf_pages"))
        pages = await asyncio.to_thread(self._extractor.extract, data, max_pages=max_pages)
        del data

        drafts = self._chunk(pages, await self._chunk_config())
        if not drafts:
            raise ExtractionError(NO_TEXT)

        embeddings = await self._embed([d.text for d in drafts])
        chunks = [
            NewChunk(d.ordinal, d.page_start, d.page_end, d.text, d.token_count, e)
            for d, e in zip(drafts, embeddings, strict=True)
        ]

        async with self._uow.begin() as uow:
            written = await uow.chunks.replace(doc.id, doc.user_id, self._embedder.model, chunks)
            if written:
                ready = await uow.documents.mark_ready(doc.id, len(pages), self._clock())
                if not ready:
                    raise _Retry(
                        "write", INGEST_FAILED
                    )  # rollback: không để chunk mà tài liệu chưa ready
            await uow.jobs.complete(job.id)
        return written

    # ---------- các bước ----------
    async def _chunk_config(self) -> ChunkingConfig:
        return ChunkingConfig(
            max_tokens=int(await self._config.get("chunk_tokens")),
            overlap_tokens=int(await self._config.get("chunk_overlap_tokens")),
            min_tokens=int(await self._config.get("chunk_min_tokens")),
            max_page_span=int(await self._config.get("chunk_max_page_span")),
        )

    @staticmethod
    def _chunk(pages: list[PageText], cfg: ChunkingConfig) -> list[ChunkDraft]:
        return chunk_pages(clean_pages(pages), cfg)

    async def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        batch = max(1, int(await self._config.get("embed_batch_size")))
        sem = asyncio.Semaphore(EMBED_CONCURRENCY)

        async def one(part: Sequence[str]) -> list[list[float]]:
            async with sem:
                return await self._embedder.embed_documents(part)

        parts = [texts[i : i + batch] for i in range(0, len(texts), batch)]
        try:
            results = await asyncio.gather(*(one(p) for p in parts))
        except EmbeddingError as exc:
            if exc.retryable:
                raise _Retry("embed", EMBEDDING_FAILED) from exc
            raise _Permanent("embed", EMBEDDING_FAILED) from exc
        vectors = [v for part in results for v in part]
        if len(vectors) != len(texts) or any(len(v) != self._embedder.dimension for v in vectors):
            raise _Retry("embed", EMBEDDING_FAILED)
        return vectors

    async def _finish_with_error(self, job: IngestJob, code: str, *, failed: bool = False) -> None:
        async with self._uow.begin() as uow:
            await uow.documents.mark_error(job.document_id, code, self._clock())
            if failed:
                await uow.jobs.fail(job.id, code)
            else:
                await uow.jobs.complete(job.id)
