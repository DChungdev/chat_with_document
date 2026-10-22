"""Cổng dịch vụ: lưu tệp, giới hạn tần suất, xác thực, pipeline trả lời, ghi cấu hình."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Any, BinaryIO, Protocol
from uuid import UUID

from docchat_core.domain import UserRole


class FileStoragePort(Protocol):
    async def put(self, key: str, content: BinaryIO, content_type: str) -> None:
        """`content` là file-like đã đặt ở đầu tệp; adapter không nạp cả tệp vào RAM nếu tránh được."""
        ...

    async def get(self, key: str) -> bytes: ...
    async def delete(self, key: str) -> None:
        """Idempotent: xóa đối tượng không tồn tại không phải lỗi."""
        ...

    async def exists(self, key: str) -> bool: ...


class RateLimiter(Protocol):
    async def hit(self, user_id: UUID, bucket: str, limit: int, window_seconds: int) -> None:
        """Ghi nhận một lượt; ném `RateLimited(retry_after)` nếu vượt `limit` trong `window_seconds`."""
        ...


@dataclass(frozen=True)
class Principal:
    """Danh tính đã xác thực, trích từ JWT (`sub`, `roles`)."""

    subject: str
    roles: frozenset[UserRole] = field(default_factory=lambda: frozenset({UserRole.USER}))


class AuthProvider(Protocol):
    async def authenticate(self, token: str) -> Principal:
        """Ném `Unauthenticated` / `SessionExpired` nếu token không hợp lệ."""
        ...


@dataclass(frozen=True)
class CitationRef:
    """Nguồn dẫn do pipeline trả về — sinh từ ID chunk đã truy xuất, không do LLM tự ghi (ADR-03)."""

    ordinal: int
    chunk_id: UUID
    document_id: UUID
    document_name: str
    page: int


@dataclass(frozen=True)
class Token:
    text: str


@dataclass(frozen=True)
class Completed:
    grounded: bool
    citations: Sequence[CitationRef] = ()


AnswerEvent = Token | Completed


class AnswerPipeline(Protocol):
    """Truy xuất + sinh câu trả lời. Triển khai ở workstream D; B7 chỉ điều phối.

    Phát `Token` lần lượt rồi đúng một `Completed`. Lỗi: ném `AnswerFailed`.
    """

    def answer(
        self, *, user_id: UUID, question: str, document_ids: Sequence[UUID]
    ) -> AsyncIterator[AnswerEvent]: ...


class ConfigWriter(Protocol):
    async def set_value(self, key: str, value: Any) -> None: ...
