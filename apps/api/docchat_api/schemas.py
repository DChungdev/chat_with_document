"""DTO của API (camelCase theo API_Design mục 3.2)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from docchat_core.domain import CitationView, Conversation, Document


class Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DocumentOut(Camel):
    id: UUID
    name: str
    size_bytes: int
    uploaded_at: datetime
    status: str
    page_count: int | None = None
    error_code: str | None = None

    @classmethod
    def of(cls, d: Document) -> DocumentOut:
        return cls(
            id=d.id, name=d.name, size_bytes=d.size_bytes, uploaded_at=d.uploaded_at,
            status=d.status.value, page_count=d.page_count, error_code=d.error_code,
        )  # fmt: skip


class DocumentPage(Camel):
    items: list[DocumentOut]
    next_cursor: str | None = None


class CitationOut(Camel):
    id: UUID
    document_id: UUID | None
    document_name: str | None
    page: int
    snippet: str | None
    valid: bool

    @classmethod
    def of(cls, v: CitationView) -> CitationOut:
        c = v.citation
        return cls(
            id=c.id, document_id=c.document_id, document_name=c.document_name,
            page=c.page, snippet=v.snippet, valid=c.valid,
        )  # fmt: skip


class ConversationOut(Camel):
    id: UUID
    created_at: datetime

    @classmethod
    def of(cls, c: Conversation) -> ConversationOut:
        return cls(id=c.id, created_at=c.created_at)


class AppConfigOut(Camel):
    qa_enabled: bool
    max_file_size_bytes: int
    max_files: int
    max_question_length: int
    max_documents_per_question: int
    accepted_types: list[str]
    notice_version: str | None
    notice_accepted: bool


class DataNoticeOut(Camel):
    version: str
    content: str
    accepted: bool


class AcceptIn(Camel):
    version: str = Field(min_length=1, max_length=64)


class AskIn(Camel):
    question: str = Field(max_length=100_000)  # giới hạn thật đọc từ cấu hình ở lõi
    document_ids: list[UUID] = Field(default_factory=list, max_length=100)
    client_message_id: UUID | None = None


class TelemetryEventIn(Camel):
    name: str = Field(max_length=64)
    ts: datetime
    session_id: UUID
    app_version: str = Field(max_length=64)
    props: dict[str, Any] = Field(default_factory=dict)


class TelemetryIn(Camel):
    events: list[TelemetryEventIn] = Field(max_length=50)


class TelemetryOut(Camel):
    accepted: int
    rejected: int


class FlagIn(Camel):
    enabled: bool
