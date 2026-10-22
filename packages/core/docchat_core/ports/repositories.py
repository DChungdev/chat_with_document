"""Cổng lưu trữ. Mọi repository được gắn với MỘT người dùng khi tạo Unit of Work, nên không có
phương thức nào truy cập dữ liệu mà thiếu `user_id` (US-402, ADR-07). Chỉ `UserRepository` và
UoW `system()` đứng ngoài ràng buộc này.
"""

from __future__ import annotations

from collections.abc import Sequence
from types import TracebackType
from typing import Protocol
from uuid import UUID

from docchat_core.domain import (
    Citation,
    CitationView,
    Conversation,
    DataNotice,
    Document,
    Message,
    TelemetryEvent,
    User,
    UserRole,
)


class UserRepository(Protocol):
    async def upsert_by_subject(self, subject: str, role: UserRole) -> User:
        """Tạo người dùng ở lần đăng nhập đầu (just-in-time) và cập nhật `last_seen_at`."""
        ...


class DocumentRepository(Protocol):
    async def add(self, doc: Document) -> None: ...
    async def get(self, document_id: UUID) -> Document | None: ...
    async def get_many(self, document_ids: Sequence[UUID]) -> list[Document]: ...
    async def list_page(self, limit: int, cursor: str | None) -> tuple[list[Document], str | None]:
        """Mới nhất trước. `cursor` mờ đục; trả cursor tiếp theo hoặc None khi hết."""
        ...

    async def list_ready_ids(self, limit: int) -> list[UUID]: ...
    async def count(self) -> int: ...
    async def delete(self, document_id: UUID) -> bool:
        """Xóa tài liệu; chunk xóa theo cascade, citation về valid=false (do FK SET NULL)."""
        ...


class JobQueue(Protocol):
    async def enqueue(self, document_id: UUID, trace_context: dict[str, str]) -> None: ...


class IdempotencyRepository(Protocol):
    async def get(self, scope: str, key: UUID) -> UUID | None: ...
    async def put(self, scope: str, key: UUID, resource_id: UUID) -> None: ...


class ConversationRepository(Protocol):
    async def add(self, conversation: Conversation) -> None: ...
    async def get(self, conversation_id: UUID) -> Conversation | None: ...


class MessageRepository(Protocol):
    async def add(self, message: Message) -> None: ...
    async def update(self, message: Message) -> None: ...
    async def get(self, message_id: UUID) -> Message | None: ...
    async def find_user_message_by_client_id(
        self, conversation_id: UUID, client_message_id: UUID
    ) -> Message | None: ...
    async def find_reply(self, parent_message_id: UUID) -> Message | None: ...
    async def set_documents(self, message_id: UUID, document_ids: Sequence[UUID]) -> None: ...


class CitationRepository(Protocol):
    async def add_many(self, citations: Sequence[Citation]) -> None: ...
    async def get_view(self, citation_id: UUID) -> CitationView | None: ...
    async def for_message(self, message_id: UUID) -> list[CitationView]: ...


class NoticeRepository(Protocol):
    async def current(self) -> DataNotice | None: ...
    async def has_accepted(self, version: str) -> bool: ...
    async def accept(self, version: str) -> None:
        """Idempotent: xác nhận lại cùng phiên bản không tạo dòng/audit mới."""
        ...


class TelemetryRepository(Protocol):
    async def allowlist(self) -> dict[str, frozenset[str]]:
        """Tên sự kiện → tập thuộc tính được phép (bảng telemetry_event_types)."""
        ...

    async def add_many(self, events: Sequence[TelemetryEvent]) -> None: ...


class UnitOfWork(Protocol):
    """Một giao dịch. Thoát khối `async with` bình thường ⇒ commit; có ngoại lệ ⇒ rollback."""

    @property
    def users(self) -> UserRepository: ...

    @property
    def documents(self) -> DocumentRepository: ...

    @property
    def jobs(self) -> JobQueue: ...

    @property
    def idempotency(self) -> IdempotencyRepository: ...

    @property
    def conversations(self) -> ConversationRepository: ...

    @property
    def messages(self) -> MessageRepository: ...

    @property
    def citations(self) -> CitationRepository: ...

    @property
    def notices(self) -> NoticeRepository: ...

    @property
    def telemetry(self) -> TelemetryRepository: ...

    async def __aenter__(self) -> UnitOfWork: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...


class UnitOfWorkFactory(Protocol):
    def for_user(self, user_id: UUID) -> UnitOfWork:
        """UoW dưới danh tính `user_id` (RLS: app.user_id)."""
        ...

    def system(self) -> UnitOfWork:
        """UoW không gắn người dùng — chỉ dùng cho tra cứu/tạo người dùng khi xác thực."""
        ...
