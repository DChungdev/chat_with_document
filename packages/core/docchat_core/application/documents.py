"""Use case tài liệu: tải lên (202, xử lý bất đồng bộ), liệt kê, xem, xóa (US-101…103)."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from collections.abc import Callable
from typing import BinaryIO
from uuid import UUID

from docchat_core.application.common import Clock, IdFactory, new_id, utc_now
from docchat_core.application.compliance import require_notice_accepted
from docchat_core.config import AppConfig
from docchat_core.domain import Document
from docchat_core.domain.errors import (
    FileTooLarge,
    InvalidFileType,
    LimitExceeded,
    NotFound,
)
from docchat_core.ports import FileStoragePort, RateLimiter, UnitOfWorkFactory

logger = logging.getLogger(__name__)

UPLOAD_SCOPE = "document_upload"
UPLOAD_RATE_BUCKET = "upload"
UPLOAD_RATE_LIMIT = 20  # lần/giờ/người dùng [Đề xuất]
UPLOAD_RATE_WINDOW = 3600
PDF_MAGIC = b"%PDF-"
_CHUNK = 1024 * 1024
_STORAGE_DELETE_ATTEMPTS = 3


def _sanitize_name(filename: str | None) -> str:
    base = re.split(r"[\\/]", filename or "")[-1]
    base = re.sub(r"[\x00-\x1f\x7f]", "", base).strip()
    return base[:255] or "document.pdf"


def _measure(content: BinaryIO) -> tuple[int, bytes]:
    """Trả (kích thước, 5 byte đầu) rồi đưa con trỏ về đầu tệp."""
    content.seek(0, 2)
    size = content.tell()
    content.seek(0)
    head = content.read(len(PDF_MAGIC))
    content.seek(0)
    return size, head


def _sha256(content: BinaryIO) -> str:
    digest = hashlib.sha256()
    while block := content.read(_CHUNK):
        digest.update(block)
    content.seek(0)
    return digest.hexdigest()


class DocumentsService:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        storage: FileStoragePort,
        config: AppConfig,
        rate_limiter: RateLimiter,
        *,
        clock: Clock = utc_now,
        id_factory: IdFactory = new_id,
        trace_context: Callable[[], dict[str, str]] = dict,
    ) -> None:
        self._uow = uow_factory
        self._storage = storage
        self._config = config
        self._limiter = rate_limiter
        self._clock = clock
        self._new_id = id_factory
        self._trace_context = trace_context

    async def upload(
        self,
        user_id: UUID,
        *,
        filename: str | None,
        content_type: str | None,
        content: BinaryIO,
        idempotency_key: UUID,
    ) -> Document:
        await self._limiter.hit(user_id, UPLOAD_RATE_BUCKET, UPLOAD_RATE_LIMIT, UPLOAD_RATE_WINDOW)

        max_size = await self._config.max_file_size_bytes()
        max_files = await self._config.max_files_per_user()
        accepted_types = await self._config.get("accepted_types")

        async with self._uow.for_user(user_id) as uow:
            await require_notice_accepted(uow)
            existing_id = await uow.idempotency.get(UPLOAD_SCOPE, idempotency_key)
            if existing_id is not None:
                existing = await uow.documents.get(existing_id)
                if existing is not None:
                    return existing  # gửi lại cùng khóa ⇒ trả bản ghi cũ, không tạo trùng
            if await uow.documents.count() >= max_files:
                raise LimitExceeded(f"Tối đa {max_files} tệp.")

        size, head = _measure(content)
        if (content_type or "").lower() not in accepted_types or head != PDF_MAGIC:
            raise InvalidFileType()
        if size == 0:
            raise InvalidFileType("Tệp rỗng.")
        if size > max_size:
            raise FileTooLarge(f"Giới hạn tối đa là {max_size // (1024 * 1024)} MB.")

        document_id = self._new_id()
        storage_key = f"{user_id}/{document_id}.pdf"  # không dùng tên tệp gốc làm khóa
        doc = Document(
            id=document_id,
            user_id=user_id,
            name=_sanitize_name(filename),
            size_bytes=size,
            storage_key=storage_key,
            uploaded_at=self._clock(),
            content_sha256=_sha256(content),
        )

        await self._storage.put(storage_key, content, "application/pdf")
        try:
            async with self._uow.for_user(user_id) as uow:
                await uow.documents.add(doc)
                # Cùng giao dịch với bản ghi tài liệu: không có tài liệu mồ côi hay job mồ côi.
                await uow.jobs.enqueue(doc.id, self._trace_context())
                await uow.idempotency.put(UPLOAD_SCOPE, idempotency_key, doc.id)
        except BaseException:
            await self._storage.delete(storage_key)  # DB lỗi ⇒ dọn tệp vừa ghi
            raise
        return doc

    async def list(
        self, user_id: UUID, limit: int = 50, cursor: str | None = None
    ) -> tuple[list[Document], str | None]:
        async with self._uow.for_user(user_id) as uow:
            return await uow.documents.list_page(min(max(limit, 1), 100), cursor)

    async def get(self, user_id: UUID, document_id: UUID) -> Document:
        async with self._uow.for_user(user_id) as uow:
            doc = await uow.documents.get(document_id)
        if doc is None:
            raise NotFound()
        return doc

    async def delete(self, user_id: UUID, document_id: UUID) -> None:
        """Xóa dữ liệu dẫn xuất trong DB trước, rồi tới PDF gốc (US-103).

        Audit `document_deleted` do trigger CSDL ghi; citation tự về valid=false nhờ FK SET NULL.
        """
        async with self._uow.for_user(user_id) as uow:
            doc = await uow.documents.get(document_id)
            if doc is None:
                raise NotFound()
            await uow.documents.delete(document_id)
        await self._delete_object(doc.id, doc.storage_key)

    async def _delete_object(self, document_id: UUID, key: str) -> None:
        for attempt in range(1, _STORAGE_DELETE_ATTEMPTS + 1):
            try:
                await self._storage.delete(key)
                return
            except Exception:
                logger.warning(
                    "storage delete failed",
                    extra={"document_id": str(document_id), "attempt": attempt},
                    exc_info=True,
                )
                await asyncio.sleep(0.2 * attempt)
        # Hết số lần thử: để lại dấu vết cho vận hành dọn tay (khóa = user_id/document_id.pdf).
        logger.error(
            "storage object orphaned",
            extra={"event": "storage_orphaned", "document_id": str(document_id)},
        )
