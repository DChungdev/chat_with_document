"""Cổng cho pipeline ingest (workstream C): trích xuất PDF, embedding, hàng đợi và ghi chỉ mục."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from types import TracebackType
from typing import Protocol
from uuid import UUID

from docchat_core.domain import Document


# ---------- trích xuất PDF ----------
@dataclass(frozen=True)
class PageText:
    number: int  # 1-based
    text: str


class ExtractionError(Exception):
    """Lỗi vĩnh viễn của PDF (không thử lại). `code` hiển thị cho UI qua documents.error_code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)  # thông điệp chỉ là mã, không chứa nội dung
        self.code = code


# Mã lỗi (khớp API_Design 3.4.1)
PDF_PASSWORD = "PDF_PASSWORD"  # noqa: S105  (mã lỗi, không phải mật khẩu)
PDF_CORRUPT = "PDF_CORRUPT"
NO_TEXT = "NO_TEXT"
PDF_TOO_MANY_PAGES = "PDF_TOO_MANY_PAGES"
EMBEDDING_FAILED = "EMBEDDING_FAILED"
STORAGE_ERROR = "STORAGE_ERROR"
INGEST_FAILED = "INGEST_FAILED"


class PdfExtractor(Protocol):
    def extract(self, data: bytes, *, max_pages: int) -> list[PageText]:
        """Đồng bộ và tốn CPU: gọi qua thread pool. Ném `ExtractionError`. Không OCR (ADR-09)."""
        ...


# ---------- embedding ----------
class EmbeddingError(Exception):
    def __init__(self, message: str = "embedding failed", *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


class EmbeddingPort(Protocol):
    @property
    def dimension(self) -> int: ...
    @property
    def model(self) -> str:
        """Tên + phiên bản mô hình; ghi vào chunks.embedding_model để phục vụ re-embed."""
        ...

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Một lô văn bản chunk; vector đã chuẩn hóa L2, đúng `dimension` chiều."""
        ...

    async def embed_query(self, text: str) -> list[float]: ...


# ---------- hàng đợi + ghi chỉ mục (vai trò app_worker) ----------
@dataclass(frozen=True)
class IngestJob:
    id: int
    document_id: UUID
    attempts: int  # đã gồm lần đang chạy
    trace_context: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class NewChunk:
    ordinal: int
    page_start: int
    page_end: int
    text: str
    token_count: int
    embedding: Sequence[float]


class IngestJobRepository(Protocol):
    async def claim(self, worker_id: str) -> IngestJob | None:
        """Nhận một job `queued` đến hạn; an toàn khi nhiều worker (FOR UPDATE SKIP LOCKED)."""
        ...

    async def complete(self, job_id: int) -> None: ...
    async def retry(self, job_id: int, delay_seconds: float, error_code: str) -> None: ...
    async def fail(self, job_id: int, error_code: str) -> None: ...
    async def requeue_stale(self, timeout_seconds: float) -> int:
        """Job `running` quá hạn khóa (worker chết) quay lại `queued`."""
        ...

    async def queue_length(self) -> int: ...


class IngestDocumentRepository(Protocol):
    async def get(self, document_id: UUID) -> Document | None:
        """Không lọc theo người dùng: worker xử lý tài liệu của mọi người."""
        ...

    async def mark_ready(self, document_id: UUID, page_count: int, now: datetime) -> bool:
        """processing → ready. False nếu tài liệu đã bị xóa hoặc không còn `processing`."""
        ...

    async def mark_error(self, document_id: UUID, error_code: str, now: datetime) -> bool: ...


class ChunkWriter(Protocol):
    async def replace(
        self, document_id: UUID, user_id: UUID, model: str, chunks: Sequence[NewChunk]
    ) -> bool:
        """Xóa chunk cũ rồi ghi chunk mới trong cùng giao dịch (idempotent).

        False nếu tài liệu đã bị xóa giữa chừng (không ghi gì).
        """
        ...


class WorkerUnitOfWork(Protocol):
    @property
    def jobs(self) -> IngestJobRepository: ...
    @property
    def documents(self) -> IngestDocumentRepository: ...
    @property
    def chunks(self) -> ChunkWriter: ...

    async def __aenter__(self) -> WorkerUnitOfWork: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...


class WorkerUnitOfWorkFactory(Protocol):
    def begin(self) -> WorkerUnitOfWork: ...


class IngestMetrics(Protocol):
    def stage_error(self, stage: str) -> None: ...
    def ingest_seconds(self, seconds: float) -> None: ...
    def queue_length(self, length: int) -> None: ...
