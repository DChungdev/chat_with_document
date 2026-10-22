"""Triển khai trong bộ nhớ của các cổng lưu trữ, mô phỏng đủ hành vi CSDL mà use case dựa vào:
lọc theo người dùng (như RLS), cascade khi xóa tài liệu, citation về valid=false, rollback giao dịch.
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from types import TracebackType
from typing import Any
from uuid import UUID, uuid4

from docchat_core.domain import (
    Citation,
    CitationView,
    Conversation,
    DataNotice,
    Document,
    DocumentStatus,
    Message,
    MessageRole,
    TelemetryEvent,
    User,
    UserRole,
)
from docchat_infra.memory.base import _Repo
from docchat_infra.memory.reports import MemFeedback, MemReports


@dataclass
class MemoryStore:
    users: dict[UUID, User] = field(default_factory=dict)
    documents: dict[UUID, Document] = field(default_factory=dict)
    jobs: dict[UUID, dict[str, str]] = field(default_factory=dict)
    idempotency: dict[tuple[UUID, str, UUID], UUID] = field(default_factory=dict)
    conversations: dict[UUID, Conversation] = field(default_factory=dict)
    messages: dict[UUID, Message] = field(default_factory=dict)
    message_documents: dict[UUID, list[UUID]] = field(default_factory=dict)
    citations: dict[UUID, Citation] = field(default_factory=dict)
    chunk_text: dict[UUID, tuple[UUID, str]] = field(default_factory=dict)  # chunk_id → (doc, text)
    # Chunk đầy đủ do worker ghi (kèm embedding) — để test ingest và truy xuất trong bộ nhớ.
    chunk_rows: dict[UUID, dict[str, Any]] = field(default_factory=dict)  # chunk_id → hàng
    job_rows: dict[UUID, dict[str, Any]] = field(default_factory=dict)  # document_id → hàng job
    job_seq: int = 0
    notice: DataNotice | None = DataNotice("draft-0", "Thông báo dữ liệu (nháp).")
    acceptances: set[tuple[UUID, str]] = field(default_factory=set)
    telemetry: list[TelemetryEvent] = field(default_factory=list)
    allowlist: dict[str, frozenset[str]] = field(default_factory=dict)
    audit: list[tuple[UUID, str, UUID | None]] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    feedback: dict[UUID, tuple[str, str | None]] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return copy.deepcopy(self.__dict__)

    def restore(self, snap: dict[str, Any]) -> None:
        self.__dict__.clear()
        self.__dict__.update(snap)


class MemUsers(_Repo):
    async def upsert_by_subject(self, subject: str, role: UserRole) -> User:
        for u in self.s.users.values():
            if u.external_subject == subject:
                return u
        user = User(uuid4(), subject, role)
        self.s.users[user.id] = user
        return user


class MemDocuments(_Repo):
    def _mine(self) -> list[Document]:
        return [d for d in self.s.documents.values() if d.user_id == self.uid]

    async def add(self, doc: Document) -> None:
        self.s.documents[doc.id] = copy.copy(doc)
        self.s.audit.append((doc.user_id, "document_uploaded", doc.id))

    async def get(self, document_id: UUID) -> Document | None:
        d = self.s.documents.get(document_id)
        return copy.copy(d) if d and d.user_id == self.uid else None

    async def get_many(self, document_ids: Sequence[UUID]) -> list[Document]:
        return [copy.copy(d) for d in self._mine() if d.id in set(document_ids)]

    async def list_page(self, limit: int, cursor: str | None) -> tuple[list[Document], str | None]:
        ordered = sorted(self._mine(), key=lambda d: (d.uploaded_at, str(d.id)), reverse=True)
        start = int(cursor) if cursor else 0
        page = ordered[start : start + limit]
        nxt = str(start + limit) if start + limit < len(ordered) else None
        return [copy.copy(d) for d in page], nxt

    async def list_ready_ids(self, limit: int) -> list[UUID]:
        ready = [d for d in self._mine() if d.status is DocumentStatus.READY]
        ready.sort(key=lambda d: d.uploaded_at, reverse=True)
        return [d.id for d in ready[:limit]]

    async def count(self) -> int:
        return len(self._mine())

    async def delete(self, document_id: UUID) -> bool:
        doc = self.s.documents.get(document_id)
        if doc is None or doc.user_id != self.uid:
            return False
        del self.s.documents[document_id]
        self.s.jobs.pop(document_id, None)
        for cid in [c for c, (d, _) in self.s.chunk_text.items() if d == document_id]:
            del self.s.chunk_text[cid]
        self.s.chunk_rows = {
            c: r for c, r in self.s.chunk_rows.items() if r["document_id"] != document_id
        }
        self.s.job_rows.pop(document_id, None)
        for cit_id, c in list(self.s.citations.items()):
            if c.document_id == document_id:  # FK SET NULL ⇒ valid=false; trigger xóa tên tệp
                self.s.citations[cit_id] = replace(
                    c, document_id=None, chunk_id=None, document_name=None
                )
        self.s.audit.append((doc.user_id, "document_deleted", document_id))
        return True


class MemJobs(_Repo):
    async def enqueue(self, document_id: UUID, trace_context: dict[str, str]) -> None:
        self.s.jobs[document_id] = dict(trace_context)
        if document_id not in self.s.job_rows:
            self.s.job_seq += 1
            self.s.job_rows[document_id] = {
                "id": self.s.job_seq,
                "status": "queued",
                "attempts": 0,
                "run_after": None,
                "locked_at": None,
                "last_error": None,
                "trace_context": dict(trace_context),
            }


class MemIdempotency(_Repo):
    async def get(self, scope: str, key: UUID) -> UUID | None:
        return self.s.idempotency.get((self.uid, scope, key))

    async def put(self, scope: str, key: UUID, resource_id: UUID) -> None:
        self.s.idempotency[(self.uid, scope, key)] = resource_id


class MemConversations(_Repo):
    async def add(self, conversation: Conversation) -> None:
        self.s.conversations[conversation.id] = copy.copy(conversation)

    async def get(self, conversation_id: UUID) -> Conversation | None:
        c = self.s.conversations.get(conversation_id)
        return copy.copy(c) if c and c.user_id == self.uid else None


class MemMessages(_Repo):
    async def add(self, message: Message) -> None:
        self.s.messages[message.id] = copy.copy(message)

    async def update(self, message: Message) -> None:
        if message.id not in self.s.messages:
            raise KeyError("message")
        self.s.messages[message.id] = copy.copy(message)

    async def get(self, message_id: UUID) -> Message | None:
        m = self.s.messages.get(message_id)
        return copy.copy(m) if m and m.user_id == self.uid else None

    async def find_user_message_by_client_id(
        self, conversation_id: UUID, client_message_id: UUID
    ) -> Message | None:
        for m in self.s.messages.values():
            if (
                m.user_id == self.uid
                and m.conversation_id == conversation_id
                and m.client_message_id == client_message_id
                and m.role is MessageRole.USER
            ):
                return copy.copy(m)
        return None

    async def find_reply(self, parent_message_id: UUID) -> Message | None:
        for m in self.s.messages.values():
            if m.user_id == self.uid and m.parent_message_id == parent_message_id:
                return copy.copy(m)
        return None

    async def set_documents(self, message_id: UUID, document_ids: Sequence[UUID]) -> None:
        self.s.message_documents[message_id] = list(document_ids)

    async def get_documents(self, message_id: UUID) -> list[UUID]:
        msg = self.s.messages.get(message_id)
        if msg is None or msg.user_id != self.uid:
            return []
        return list(self.s.message_documents.get(message_id, []))


class MemCitations(_Repo):
    async def add_many(self, citations: Sequence[Citation]) -> None:
        for c in citations:
            self.s.citations[c.id] = c

    def _view(self, c: Citation) -> CitationView:
        found = self.s.chunk_text.get(c.chunk_id) if c.chunk_id else None
        return CitationView(c, found[1] if found else None)

    async def get_view(self, citation_id: UUID) -> CitationView | None:
        c = self.s.citations.get(citation_id)
        return self._view(c) if c and c.user_id == self.uid else None

    async def for_message(self, message_id: UUID) -> list[CitationView]:
        found = [
            c
            for c in self.s.citations.values()
            if c.message_id == message_id and c.user_id == self.uid
        ]
        return [self._view(c) for c in sorted(found, key=lambda c: c.ordinal)]


class MemNotices(_Repo):
    async def current(self) -> DataNotice | None:
        return self.s.notice

    async def has_accepted(self, version: str) -> bool:
        return (self.uid, version) in self.s.acceptances

    async def accept(self, version: str) -> None:
        key = (self.uid, version)
        if key not in self.s.acceptances:
            self.s.acceptances.add(key)
            self.s.audit.append((self.uid, "notice_accepted", None))


class MemTelemetry(_Repo):
    async def allowlist(self) -> dict[str, frozenset[str]]:
        return dict(self.s.allowlist)

    async def add_many(self, events: Sequence[TelemetryEvent]) -> None:
        self.s.telemetry.extend(events)


class MemoryUnitOfWork:
    def __init__(self, store: MemoryStore, user_id: UUID | None) -> None:
        self._store = store
        self._snap: dict[str, Any] | None = None
        self.users = MemUsers(store, user_id)
        self.documents = MemDocuments(store, user_id)
        self.jobs = MemJobs(store, user_id)
        self.idempotency = MemIdempotency(store, user_id)
        self.conversations = MemConversations(store, user_id)
        self.messages = MemMessages(store, user_id)
        self.citations = MemCitations(store, user_id)
        self.notices = MemNotices(store, user_id)
        self.telemetry = MemTelemetry(store, user_id)
        self.feedback = MemFeedback(store, user_id)
        self.reports = MemReports(store, user_id)

    async def __aenter__(self) -> MemoryUnitOfWork:
        self._snap = self._store.snapshot()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None and self._snap is not None:
            self._store.restore(self._snap)  # rollback
        self._snap = None


class MemoryUnitOfWorkFactory:
    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def for_user(self, user_id: UUID) -> MemoryUnitOfWork:
        return MemoryUnitOfWork(self.store, user_id)

    def system(self) -> MemoryUnitOfWork:
        return MemoryUnitOfWork(self.store, None)
