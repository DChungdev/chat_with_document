"""Helper dùng chung cho test API: adapter trong bộ nhớ, pipeline kịch bản, JWT HS256."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from fastapi.testclient import TestClient

from docchat_api.container import Container, assemble
from docchat_api.main import create_app
from docchat_core.config import AppConfig, Settings
from docchat_core.domain import Chunk, Document, DocumentStatus
from docchat_core.ports import AnswerEvent, CitationRef, Completed, Token
from docchat_infra.auth import JwtAuthProvider
from docchat_infra.memory import InMemoryFileStorage, MemoryStore, MemoryUnitOfWorkFactory

SECRET = "test-secret-test-secret-test-secret-0123456789"
PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"


class DictConfig:
    """ConfigStore + ConfigWriter trong bộ nhớ."""

    def __init__(self, values: dict[str, Any] | None = None) -> None:
        self.values = values or {}

    async def load_all(self) -> dict[str, Any]:
        return dict(self.values)

    async def set_value(self, key: str, value: Any) -> None:
        self.values[key] = value


class ScriptedPipeline:
    """Pipeline giả: phát lần lượt các phần tử của `script`; Exception thì ném."""

    def __init__(self) -> None:
        self.script: list[AnswerEvent | BaseException | float] = []  # float = ngủ (giây)
        self.calls: list[dict[str, Any]] = []

    async def answer(
        self, *, user_id: UUID, question: str, document_ids: Sequence[UUID]
    ) -> AsyncIterator[AnswerEvent]:
        self.calls.append({"user_id": user_id, "question": question, "document_ids": document_ids})
        for item in list(self.script):
            if isinstance(item, BaseException):
                raise item
            if isinstance(item, float):
                await asyncio.sleep(item)
                continue
            yield item


@dataclass
class Env:
    container: Container
    store: MemoryStore
    storage: InMemoryFileStorage
    config: DictConfig
    pipeline: ScriptedPipeline
    client: TestClient
    users: dict[str, str] = field(default_factory=dict)

    # ---- helpers ----
    def token(
        self,
        sub: str = "alice",
        roles: list[str] | None = None,
        expires_in: int = 3600,
    ) -> str:
        claims: dict[str, Any] = {
            "sub": sub,
            "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
        }
        if roles is not None:
            claims["roles"] = roles
        return jwt.encode(claims, SECRET, algorithm="HS256")

    def headers(self, sub: str = "alice", roles: list[str] | None = None) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token(sub, roles)}"}

    def user_id(self, sub: str) -> UUID:
        return next(u.id for u in self.store.users.values() if u.external_subject == sub)

    def accept_notice(self, sub: str = "alice") -> None:
        h = self.headers(sub)
        version = self.client.get("/api/v1/data-notice", headers=h).json()["version"]
        r = self.client.post(
            "/api/v1/data-notice/acceptances", json={"version": version}, headers=h
        )
        assert r.status_code == 201, r.text

    def upload(
        self,
        sub: str = "alice",
        *,
        name: str = "baogia.pdf",
        content: bytes = PDF,
        content_type: str = "application/pdf",
        key: UUID | None = None,
    ) -> Any:
        return self.client.post(
            "/api/v1/documents",
            files={"file": (name, content, content_type)},
            headers={**self.headers(sub), "Idempotency-Key": str(key or uuid4())},
        )

    def seed_ready_document(
        self, sub: str = "alice", name: str = "baogia.pdf", text: str = "Thanh toán trong 30 ngày."
    ) -> tuple[Document, Chunk]:
        """Tạo tài liệu `ready` kèm một chunk (giả lập việc worker đã xử lý xong)."""
        self.client.get("/api/v1/config", headers=self.headers(sub))  # đảm bảo người dùng tồn tại
        uid = self.user_id(sub)
        doc = Document(
            id=uuid4(), user_id=uid, name=name, size_bytes=len(PDF), storage_key=f"{uid}/x.pdf",
            uploaded_at=datetime.now(UTC),
        )  # fmt: skip
        doc.mark_ready(5, datetime.now(UTC))
        chunk = Chunk(uuid4(), doc.id, uid, 0, 4, 4, text, 10)
        self.store.documents[doc.id] = doc
        self.store.chunk_text[chunk.id] = (doc.id, text)
        return doc, chunk

    def conversation(self, sub: str = "alice") -> str:
        r = self.client.post("/api/v1/conversations", headers=self.headers(sub))
        assert r.status_code == 201, r.text
        return str(r.json()["id"])

    def ask(
        self, conv: str, question: str = "Điều khoản thanh toán?", sub: str = "alice", **body: Any
    ) -> Any:
        return self.client.post(
            f"/api/v1/conversations/{conv}/messages",
            json={"question": question, **body},
            headers=self.headers(sub),
        )

    def ref(self, doc: Document, chunk: Chunk, ordinal: int = 1) -> CitationRef:
        return CitationRef(ordinal, chunk.id, doc.id, doc.name, chunk.page_start)


def parse_sse(body: str) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in body.strip().split("\n\n"):
        if not block.strip():
            continue
        name = next(line[7:] for line in block.splitlines() if line.startswith("event: "))
        data = next(line[6:] for line in block.splitlines() if line.startswith("data: "))
        events.append((name, json.loads(data)))
    return events


def make_env(config_values: dict[str, Any] | None = None, **chat_kwargs: Any) -> Iterator[Env]:
    settings = Settings(
        environment="test",
        jwt_secret=SECRET,  # type: ignore[arg-type]
        telemetry_salt="test-salt",  # type: ignore[arg-type]
    )
    store = MemoryStore()
    store.allowlist = {
        "answer_completed": frozenset({"total_ms", "citation_count", "grounded"}),
        "upload_succeeded": frozenset({"file_size", "duration_ms"}),
        "citation_opened": frozenset({"citation_index"}),
        "upload_failed": frozenset({"error_code", "file_size"}),
    }
    storage = InMemoryFileStorage()
    cfg = DictConfig(config_values)
    pipeline = ScriptedPipeline()
    container = assemble(
        settings,
        config=AppConfig(cfg, ttl_seconds=0),
        uow_factory=MemoryUnitOfWorkFactory(store),
        config_writer=cfg,
        auth=JwtAuthProvider(algorithms=["HS256"], key=SECRET),
        storage=storage,
        pipeline=pipeline,
    )
    for k, v in chat_kwargs.items():
        setattr(container.chat, k, v)
    with TestClient(create_app(container), raise_server_exceptions=False) as client:
        yield Env(container, store, storage, cfg, pipeline, client)


def completed(doc: Document, chunk: Chunk, grounded: bool = True) -> Completed:
    return Completed(grounded, [CitationRef(1, chunk.id, doc.id, doc.name, chunk.page_start)])


_ = (Token, DocumentStatus, time)  # re-export cho test
