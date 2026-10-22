from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from types import TracebackType
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from docchat_infra.persistence.repositories import (
    PgCitations,
    PgConversations,
    PgDocuments,
    PgFeedback,
    PgIdempotency,
    PgJobs,
    PgMessages,
    PgNotices,
    PgReports,
    PgTelemetry,
    PgUsers,
)
from docchat_infra.persistence.session import system_transaction, user_transaction


class PgUnitOfWork:
    """Một giao dịch PostgreSQL. Có `user_id` ⇒ đặt `app.user_id` để RLS áp dụng (ADR-07)."""

    users: PgUsers
    documents: PgDocuments
    jobs: PgJobs
    idempotency: PgIdempotency
    conversations: PgConversations
    messages: PgMessages
    citations: PgCitations
    notices: PgNotices
    telemetry: PgTelemetry
    feedback: PgFeedback
    reports: PgReports

    def __init__(self, engine: AsyncEngine, user_id: UUID | None) -> None:
        self._engine = engine
        self._uid = user_id
        self._cm: AbstractAsyncContextManager[AsyncConnection] | None = None

    async def __aenter__(self) -> PgUnitOfWork:
        self._cm = (
            user_transaction(self._engine, self._uid)
            if self._uid is not None
            else system_transaction(self._engine)
        )
        conn = await self._cm.__aenter__()
        self.users = PgUsers(conn, self._uid)
        self.documents = PgDocuments(conn, self._uid)
        self.jobs = PgJobs(conn, self._uid)
        self.idempotency = PgIdempotency(conn, self._uid)
        self.conversations = PgConversations(conn, self._uid)
        self.messages = PgMessages(conn, self._uid)
        self.citations = PgCitations(conn, self._uid)
        self.notices = PgNotices(conn, self._uid)
        self.telemetry = PgTelemetry(conn, self._uid)
        self.feedback = PgFeedback(conn, self._uid)
        self.reports = PgReports(conn, self._uid)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._cm is not None
        await self._cm.__aexit__(exc_type, exc, tb)  # commit nếu không có ngoại lệ


class PgUnitOfWorkFactory:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    def for_user(self, user_id: UUID) -> PgUnitOfWork:
        return PgUnitOfWork(self._engine, user_id)

    def system(self) -> PgUnitOfWork:
        return PgUnitOfWork(self._engine, None)
