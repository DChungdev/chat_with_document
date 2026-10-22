"""Thực thể miền thuần (không phụ thuộc hạ tầng). Xem Database_Design_SQL mục 4 và API_Design 3.4."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from docchat_core.domain.errors import InvalidTransition


class UserRole(StrEnum):
    USER = "user"
    EVALUATOR = "evaluator"
    OPS = "ops"


class DocumentStatus(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class MessageRole(StrEnum):
    USER = "user"
    AI = "ai"


class MessageStatus(StrEnum):
    SENDING = "sending"
    STREAMING = "streaming"
    COMPLETE = "complete"
    INTERRUPTED = "interrupted"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass(frozen=True)
class User:
    id: UUID
    external_subject: str
    role: UserRole = UserRole.USER


@dataclass
class Document:
    id: UUID
    user_id: UUID
    name: str
    size_bytes: int
    storage_key: str
    uploaded_at: datetime
    status: DocumentStatus = DocumentStatus.PROCESSING
    page_count: int | None = None
    error_code: str | None = None
    content_sha256: str | None = None
    processed_at: datetime | None = None

    def mark_ready(self, page_count: int, now: datetime) -> None:
        """processing → ready. Chỉ worker gọi (API_Design 3.6)."""
        if self.status is not DocumentStatus.PROCESSING:
            raise InvalidTransition()
        if page_count < 1:
            raise InvalidTransition("Số trang phải lớn hơn 0.")
        self.status, self.page_count, self.processed_at = DocumentStatus.READY, page_count, now

    def mark_error(self, error_code: str, now: datetime) -> None:
        """processing → error, luôn kèm mã lỗi để UI hiển thị lý do."""
        if self.status is not DocumentStatus.PROCESSING:
            raise InvalidTransition()
        if not error_code:
            raise InvalidTransition("Thiếu mã lỗi.")
        self.status, self.error_code, self.processed_at = DocumentStatus.ERROR, error_code, now


@dataclass
class Chunk:
    id: UUID
    document_id: UUID
    user_id: UUID
    ordinal: int
    page_start: int
    page_end: int
    text: str
    token_count: int
    embedding_model: str = ""

    def __post_init__(self) -> None:
        if self.page_start < 1 or self.page_end < self.page_start:
            raise ValueError("page range không hợp lệ")


@dataclass
class Conversation:
    id: UUID
    user_id: UUID
    created_at: datetime
    last_activity_at: datetime


_TERMINAL = {
    MessageStatus.COMPLETE,
    MessageStatus.INTERRUPTED,
    MessageStatus.FAILED,
    MessageStatus.STOPPED,
}
_ALLOWED: dict[MessageStatus, set[MessageStatus]] = {
    MessageStatus.SENDING: {MessageStatus.STREAMING, MessageStatus.FAILED},
    MessageStatus.STREAMING: _TERMINAL,
}


@dataclass
class Message:
    id: UUID
    conversation_id: UUID
    user_id: UUID
    role: MessageRole
    status: MessageStatus
    created_at: datetime
    text: str = ""
    grounded: bool | None = None  # chỉ có nghĩa với role=AI
    parent_message_id: UUID | None = None
    client_message_id: UUID | None = None
    error_code: str | None = None
    completed_at: datetime | None = None

    @classmethod
    def new_user(
        cls,
        id: UUID,
        conversation_id: UUID,
        user_id: UUID,
        text: str,
        now: datetime,
        client_message_id: UUID | None = None,
    ) -> Message:
        """Câu hỏi được lưu ở trạng thái hoàn tất NGAY, trước khi gọi dịch vụ ngoài (CN-05)."""
        return cls(
            id=id,
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.USER,
            status=MessageStatus.COMPLETE,
            created_at=now,
            text=text,
            client_message_id=client_message_id,
            completed_at=now,
        )

    @classmethod
    def new_ai(
        cls, id: UUID, conversation_id: UUID, user_id: UUID, parent: UUID, now: datetime
    ) -> Message:
        return cls(
            id=id,
            conversation_id=conversation_id,
            user_id=user_id,
            role=MessageRole.AI,
            status=MessageStatus.SENDING,
            created_at=now,
            parent_message_id=parent,
        )

    def _to(self, new: MessageStatus, now: datetime | None = None) -> None:
        if new not in _ALLOWED.get(self.status, set()):
            raise InvalidTransition()
        self.status = new
        if new in _TERMINAL:
            self.completed_at = now

    def start_streaming(self) -> None:
        self._to(MessageStatus.STREAMING)

    def append(self, chunk: str) -> None:
        if self.status is not MessageStatus.STREAMING:
            raise InvalidTransition()
        self.text += chunk

    def complete(self, grounded: bool, now: datetime) -> None:
        self._to(MessageStatus.COMPLETE, now)
        self.grounded = grounded

    def interrupt(self, now: datetime) -> None:
        self._to(MessageStatus.INTERRUPTED, now)

    def stop(self, now: datetime) -> None:
        self._to(MessageStatus.STOPPED, now)

    def fail(self, error_code: str, now: datetime) -> None:
        self._to(MessageStatus.FAILED, now)
        self.error_code = error_code


@dataclass(frozen=True)
class Citation:
    id: UUID
    message_id: UUID
    user_id: UUID
    ordinal: int
    page: int
    document_id: UUID | None = None
    chunk_id: UUID | None = None
    document_name: str | None = None

    @property
    def valid(self) -> bool:
        """Khớp cột sinh `citations.valid`: nguồn còn khi chunk còn tồn tại."""
        return self.chunk_id is not None


@dataclass(frozen=True)
class CitationView:
    """Citation kèm đoạn nguồn (đọc qua JOIN chunks; không sao chép snippet vào citations)."""

    citation: Citation
    snippet: str | None


@dataclass(frozen=True)
class DataNotice:
    version: str
    content: str


@dataclass(frozen=True)
class TelemetryEvent:
    ts: datetime
    name: str
    user_hash: str
    session_id: UUID
    app_version: str
    props: dict[str, object] = field(default_factory=dict)
