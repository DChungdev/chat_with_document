"""Repository PostgreSQL (SQLAlchemy Core + SQL tường minh).

Mọi truy vấn lọc `user_id` của UoW một cách TƯỜNG MINH, ngoài lớp bảo vệ RLS (phòng thủ nhiều lớp,
ADR-07). Tham số luôn được ràng buộc, không nội suy chuỗi.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from docchat_core.domain import (
    Citation,
    CitationView,
    Conversation,
    DataNotice,
    Document,
    DocumentStatus,
    Message,
    MessageRole,
    MessageStatus,
    TelemetryEvent,
    User,
    UserRole,
)

MAX_MESSAGE_CHARS = 20000  # ck_messages_text_len


class _Repo:
    def __init__(self, conn: AsyncConnection, user_id: UUID | None) -> None:
        self.conn = conn
        self.uid = user_id

    async def _all(self, sql: str, params: dict[str, Any]) -> list[Any]:
        return list((await self.conn.execute(text(sql), params)).mappings().all())

    async def _one(self, sql: str, params: dict[str, Any]) -> Any:
        return (await self.conn.execute(text(sql), params)).mappings().first()


class PgUsers(_Repo):
    async def upsert_by_subject(self, subject: str, role: UserRole) -> User:
        row = await self._one(
            "INSERT INTO users (external_subject, role) VALUES (:s, CAST(:r AS user_role)) "
            "ON CONFLICT (external_subject) DO UPDATE SET last_seen_at = now() "
            "RETURNING id, external_subject, role",
            {"s": subject, "r": role.value},
        )
        return User(row["id"], row["external_subject"], UserRole(row["role"]))


_DOC_COLS = (
    "id, user_id, name, size_bytes, page_count, status, error_code, storage_key, "
    "content_sha256, uploaded_at, processed_at"
)


def _doc(r: Any) -> Document:
    return Document(
        id=r["id"],
        user_id=r["user_id"],
        name=r["name"],
        size_bytes=r["size_bytes"],
        storage_key=r["storage_key"],
        uploaded_at=r["uploaded_at"],
        status=DocumentStatus(r["status"]),
        page_count=r["page_count"],
        error_code=r["error_code"],
        content_sha256=r["content_sha256"],
        processed_at=r["processed_at"],
    )


def _encode_cursor(ts: datetime, doc_id: UUID) -> str:
    return base64.urlsafe_b64encode(f"{ts.isoformat()}|{doc_id}".encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    ts, _, did = base64.urlsafe_b64decode(cursor.encode()).decode().partition("|")
    return datetime.fromisoformat(ts), UUID(did)


class PgDocuments(_Repo):
    async def add(self, doc: Document) -> None:
        await self.conn.execute(
            text(
                "INSERT INTO documents (id, user_id, name, size_bytes, status, storage_key, "
                "content_sha256, uploaded_at) VALUES (:id, :u, :n, :sz, CAST(:st AS document_status), "
                ":k, :h, :at)"
            ),
            {
                "id": doc.id,
                "u": doc.user_id,
                "n": doc.name,
                "sz": doc.size_bytes,
                "st": doc.status.value,
                "k": doc.storage_key,
                "h": doc.content_sha256,
                "at": doc.uploaded_at,
            },
        )

    async def get(self, document_id: UUID) -> Document | None:
        r = await self._one(
            f"SELECT {_DOC_COLS} FROM documents WHERE id = :id AND user_id = :u",
            {"id": document_id, "u": self.uid},
        )
        return _doc(r) if r else None

    async def get_many(self, document_ids: Sequence[UUID]) -> list[Document]:
        rows = await self._all(
            f"SELECT {_DOC_COLS} FROM documents "
            "WHERE user_id = :u AND id = ANY(CAST(:ids AS uuid[]))",
            {"u": self.uid, "ids": list(document_ids)},
        )
        return [_doc(r) for r in rows]

    async def list_page(self, limit: int, cursor: str | None) -> tuple[list[Document], str | None]:
        params: dict[str, Any] = {"u": self.uid, "n": limit + 1}
        after = ""
        if cursor:
            params["ts"], params["cid"] = _decode_cursor(cursor)
            after = "AND (uploaded_at, id) < (CAST(:ts AS timestamptz), CAST(:cid AS uuid)) "
        rows = await self._all(
            f"SELECT {_DOC_COLS} FROM documents WHERE user_id = :u {after}"
            "ORDER BY uploaded_at DESC, id DESC LIMIT :n",
            params,
        )
        docs = [_doc(r) for r in rows]
        if len(docs) > limit:
            docs = docs[:limit]
            return docs, _encode_cursor(docs[-1].uploaded_at, docs[-1].id)
        return docs, None

    async def list_ready_ids(self, limit: int) -> list[UUID]:
        rows = await self._all(
            "SELECT id FROM documents WHERE user_id = :u AND status = 'ready' "
            "ORDER BY uploaded_at DESC LIMIT :n",
            {"u": self.uid, "n": limit},
        )
        return [r["id"] for r in rows]

    async def count(self) -> int:
        r = await self._one(
            "SELECT count(*) AS n FROM documents WHERE user_id = :u", {"u": self.uid}
        )
        return int(r["n"])

    async def delete(self, document_id: UUID) -> bool:
        res = await self.conn.execute(
            text("DELETE FROM documents WHERE id = :id AND user_id = :u"),
            {"id": document_id, "u": self.uid},
        )
        return bool(res.rowcount)


class PgJobs(_Repo):
    async def enqueue(self, document_id: UUID, trace_context: dict[str, str]) -> None:
        await self.conn.execute(
            text(
                "INSERT INTO ingest_jobs (document_id, trace_context) "
                "VALUES (:d, CAST(:tc AS jsonb)) ON CONFLICT (document_id) DO NOTHING"
            ),
            {"d": document_id, "tc": json.dumps(trace_context)},
        )


class PgIdempotency(_Repo):
    async def get(self, scope: str, key: UUID) -> UUID | None:
        r = await self._one(
            "SELECT resource_id FROM idempotency_keys WHERE user_id = :u AND scope = :s AND key = :k",
            {"u": self.uid, "s": scope, "k": key},
        )
        return r["resource_id"] if r else None

    async def put(self, scope: str, key: UUID, resource_id: UUID) -> None:
        await self.conn.execute(
            text(
                "INSERT INTO idempotency_keys (user_id, scope, key, resource_id) "
                "VALUES (:u, :s, :k, :r) ON CONFLICT DO NOTHING"
            ),
            {"u": self.uid, "s": scope, "k": key, "r": resource_id},
        )


class PgConversations(_Repo):
    async def add(self, conversation: Conversation) -> None:
        await self.conn.execute(
            text(
                "INSERT INTO conversations (id, user_id, created_at, last_activity_at) "
                "VALUES (:id, :u, :c, :l)"
            ),
            {
                "id": conversation.id,
                "u": conversation.user_id,
                "c": conversation.created_at,
                "l": conversation.last_activity_at,
            },
        )

    async def get(self, conversation_id: UUID) -> Conversation | None:
        r = await self._one(
            "SELECT id, user_id, created_at, last_activity_at FROM conversations "
            "WHERE id = :id AND user_id = :u",
            {"id": conversation_id, "u": self.uid},
        )
        return (
            Conversation(r["id"], r["user_id"], r["created_at"], r["last_activity_at"])
            if r
            else None
        )


_MSG_COLS = (
    "id, conversation_id, user_id, role, text, status, grounded, parent_message_id, "
    "client_message_id, error_code, created_at, completed_at"
)


def _msg(r: Any) -> Message:
    return Message(
        id=r["id"],
        conversation_id=r["conversation_id"],
        user_id=r["user_id"],
        role=MessageRole(r["role"]),
        status=MessageStatus(r["status"]),
        created_at=r["created_at"],
        text=r["text"],
        grounded=r["grounded"],
        parent_message_id=r["parent_message_id"],
        client_message_id=r["client_message_id"],
        error_code=r["error_code"],
        completed_at=r["completed_at"],
    )


class PgMessages(_Repo):
    async def add(self, message: Message) -> None:
        await self.conn.execute(
            text(
                "INSERT INTO messages (id, conversation_id, user_id, role, text, status, grounded, "
                "parent_message_id, client_message_id, error_code, created_at, completed_at) "
                "VALUES (:id, :cv, :u, CAST(:role AS message_role), :t, CAST(:st AS message_status), "
                ":g, :p, :cm, :e, :c, :done)"
            ),
            self._params(message),
        )

    async def update(self, message: Message) -> None:
        res = await self.conn.execute(
            text(
                "UPDATE messages SET text = :t, status = CAST(:st AS message_status), grounded = :g, "
                "error_code = :e, completed_at = :done WHERE id = :id AND user_id = :u"
            ),
            self._params(message),
        )
        if not res.rowcount:
            raise LookupError("message not found")

    @staticmethod
    def _params(m: Message) -> dict[str, Any]:
        return {
            "id": m.id,
            "cv": m.conversation_id,
            "u": m.user_id,
            "role": m.role.value,
            "t": m.text[:MAX_MESSAGE_CHARS],
            "st": m.status.value,
            "g": m.grounded,
            "p": m.parent_message_id,
            "cm": m.client_message_id,
            "e": m.error_code,
            "c": m.created_at,
            "done": m.completed_at,
        }

    async def get(self, message_id: UUID) -> Message | None:
        r = await self._one(
            f"SELECT {_MSG_COLS} FROM messages WHERE id = :id AND user_id = :u",
            {"id": message_id, "u": self.uid},
        )
        return _msg(r) if r else None

    async def find_user_message_by_client_id(
        self, conversation_id: UUID, client_message_id: UUID
    ) -> Message | None:
        r = await self._one(
            f"SELECT {_MSG_COLS} FROM messages WHERE conversation_id = :cv AND user_id = :u "
            "AND client_message_id = :cm AND role = 'user'",
            {"cv": conversation_id, "u": self.uid, "cm": client_message_id},
        )
        return _msg(r) if r else None

    async def find_reply(self, parent_message_id: UUID) -> Message | None:
        r = await self._one(
            f"SELECT {_MSG_COLS} FROM messages WHERE parent_message_id = :p AND user_id = :u "
            "ORDER BY created_at DESC LIMIT 1",
            {"p": parent_message_id, "u": self.uid},
        )
        return _msg(r) if r else None

    async def set_documents(self, message_id: UUID, document_ids: Sequence[UUID]) -> None:
        if not document_ids:
            return
        await self.conn.execute(
            text(
                "INSERT INTO message_documents (message_id, document_id, user_id) "
                "VALUES (:m, :d, :u)"
            ),
            [{"m": message_id, "d": d, "u": self.uid} for d in document_ids],
        )


_CIT_SELECT = (
    "SELECT c.id, c.message_id, c.user_id, c.ordinal, c.page, c.document_id, c.chunk_id, "
    "c.document_name, ch.text AS snippet FROM citations c "
    "LEFT JOIN chunks ch ON ch.id = c.chunk_id "
)


def _cit(r: Any) -> CitationView:
    return CitationView(
        Citation(
            id=r["id"],
            message_id=r["message_id"],
            user_id=r["user_id"],
            ordinal=r["ordinal"],
            page=r["page"],
            document_id=r["document_id"],
            chunk_id=r["chunk_id"],
            document_name=r["document_name"],
        ),
        r["snippet"],
    )


class PgCitations(_Repo):
    async def add_many(self, citations: Sequence[Citation]) -> None:
        if not citations:
            return
        await self.conn.execute(
            text(
                "INSERT INTO citations (id, message_id, user_id, ordinal, document_id, chunk_id, "
                "document_name, page) VALUES (:id, :m, :u, :o, :d, :ch, :n, :p)"
            ),
            [
                {
                    "id": c.id,
                    "m": c.message_id,
                    "u": c.user_id,
                    "o": c.ordinal,
                    "d": c.document_id,
                    "ch": c.chunk_id,
                    "n": c.document_name,
                    "p": c.page,
                }
                for c in citations
            ],
        )

    async def get_view(self, citation_id: UUID) -> CitationView | None:
        r = await self._one(
            _CIT_SELECT + "WHERE c.id = :id AND c.user_id = :u", {"id": citation_id, "u": self.uid}
        )
        return _cit(r) if r else None

    async def for_message(self, message_id: UUID) -> list[CitationView]:
        rows = await self._all(
            _CIT_SELECT + "WHERE c.message_id = :m AND c.user_id = :u ORDER BY c.ordinal",
            {"m": message_id, "u": self.uid},
        )
        return [_cit(r) for r in rows]


class PgNotices(_Repo):
    async def current(self) -> DataNotice | None:
        r = await self._one(
            "SELECT version, content FROM data_notice_versions WHERE is_current", {}
        )
        return DataNotice(r["version"], r["content"]) if r else None

    async def has_accepted(self, version: str) -> bool:
        r = await self._one(
            "SELECT 1 AS ok FROM data_notice_acceptances WHERE user_id = :u AND version = :v",
            {"u": self.uid, "v": version},
        )
        return r is not None

    async def accept(self, version: str) -> None:
        await self.conn.execute(
            text(
                "INSERT INTO data_notice_acceptances (user_id, version) VALUES (:u, :v) "
                "ON CONFLICT DO NOTHING"
            ),
            {"u": self.uid, "v": version},
        )


class PgTelemetry(_Repo):
    async def allowlist(self) -> dict[str, frozenset[str]]:
        rows = await self._all("SELECT name, allowed_props FROM telemetry_event_types", {})
        return {r["name"]: frozenset(r["allowed_props"]) for r in rows}

    async def add_many(self, events: Sequence[TelemetryEvent]) -> None:
        if not events:
            return
        await self.conn.execute(
            text(
                "INSERT INTO telemetry_events (ts, name, user_hash, session_id, app_version, props) "
                "VALUES (:ts, :n, :h, :s, :v, CAST(:p AS jsonb))"
            ),
            [
                {
                    "ts": e.ts,
                    "n": e.name,
                    "h": e.user_hash,
                    "s": e.session_id,
                    "v": e.app_version,
                    "p": json.dumps(e.props),
                }
                for e in events
            ],
        )
