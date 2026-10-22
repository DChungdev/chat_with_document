"""Môi trường hỏi đáp đầu-cuối: ingest PDF thật → retrieval → LLM giả, mọi thứ trên adapter bộ nhớ."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from typing import Any

from api_helpers import SECRET, DictConfig, Env, ScriptedPipeline
from fastapi.testclient import TestClient

from docchat_api.container import assemble
from docchat_api.main import create_app
from docchat_core.application.answering import AnsweringPipeline
from docchat_core.application.ingest import IngestService
from docchat_core.application.retrieval import Retriever
from docchat_core.config import AppConfig, Settings
from docchat_infra.auth import JwtAuthProvider
from docchat_infra.embedding import FakeEmbedding
from docchat_infra.llm import FakeLLM
from docchat_infra.memory import (
    InMemoryFileStorage,
    MemoryStore,
    MemoryUnitOfWorkFactory,
    MemoryVectorStore,
    MemoryWorkerUnitOfWorkFactory,
)
from docchat_infra.pdf import PypdfExtractor


class QaEnv(Env):
    ingest: IngestService
    llm: FakeLLM

    def run_ingest(self) -> None:
        async def drain() -> None:
            while await self.ingest.process_next():
                pass

        asyncio.run(drain())


def make_qa_env(config_values: dict[str, Any] | None = None) -> Iterator[QaEnv]:
    settings = Settings(
        environment="test",
        jwt_secret=SECRET,  # type: ignore[arg-type]
        telemetry_salt="test-salt",  # type: ignore[arg-type]
    )
    store, storage = MemoryStore(), InMemoryFileStorage()
    cfg = DictConfig({"retrieval_min_score": 0.12, "chunk_min_tokens": 3, **(config_values or {})})
    config = AppConfig(cfg, ttl_seconds=0)
    embedder, llm = FakeEmbedding(256), FakeLLM()
    pipeline = AnsweringPipeline(Retriever(embedder, MemoryVectorStore(store), config), llm, config)
    container = assemble(
        settings,
        config=config,
        uow_factory=MemoryUnitOfWorkFactory(store),
        config_writer=cfg,
        auth=JwtAuthProvider(algorithms=["HS256"], key=SECRET),
        storage=storage,
        pipeline=pipeline,
    )
    ingest = IngestService(
        MemoryWorkerUnitOfWorkFactory(store), storage, PypdfExtractor(), embedder, config
    )
    with TestClient(create_app(container), raise_server_exceptions=False) as client:
        env = QaEnv(container, store, storage, cfg, ScriptedPipeline(), client)
        env.ingest, env.llm = ingest, llm
        yield env
