"""Chạy cục bộ KHÔNG cần Docker, PostgreSQL hay MinIO.

    python -m docchat_api.devserver            # http://localhost:8000
    python -m docchat_api.devserver --port 9000 --no-static

Mọi thứ nằm trong một tiến trình: API + worker ingest (tác vụ nền) + kho dữ liệu/tệp/vector trong bộ
nhớ. DỮ LIỆU MẤT KHI TẮT TIẾN TRÌNH. Mặc định dùng embedding và LLM GIẢ LẬP (không gọi dịch vụ ngoài,
không cần khóa); đặt `LLM_PROVIDER=anthropic` + `LLM_API_KEY` (và/hoặc `EMBEDDING_PROVIDER=http`) để
dùng dịch vụ thật — khi đó nội dung tài liệu sẽ rời máy bạn, chỉ làm với dữ liệu thử đã được phép.

Đăng nhập: POST /api/v1/dev/login (giao diện có form). Không dùng ở staging/production.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from docchat_api.container import Container, assemble
from docchat_api.main import create_app
from docchat_core.application.answering import AnsweringPipeline
from docchat_core.application.ingest import IngestService
from docchat_core.application.retrieval import Retriever
from docchat_core.config import DEFAULTS, AppConfig, Settings, get_settings
from docchat_core.domain import DataNotice
from docchat_infra.auth import JwtAuthProvider
from docchat_infra.embedding import build_embedding
from docchat_infra.llm import build_llm
from docchat_infra.memory import (
    TELEMETRY_ALLOWLIST,
    InMemoryFileStorage,
    MemoryConfigStore,
    MemoryStore,
    MemoryUnitOfWorkFactory,
    MemoryVectorStore,
    MemoryWorkerUnitOfWorkFactory,
)
from docchat_infra.pdf import PypdfExtractor

logger = logging.getLogger("docchat.devserver")

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STATIC = REPO_ROOT / "apps" / "web" / "dist"

NOTICE = DataNotice(
    "dev-1",
    "Bản thử cục bộ: tài liệu và câu hỏi chỉ nằm trong bộ nhớ của máy này và mất khi tắt máy chủ. "
    "Nội dung chính thức do pháp chế duyệt (OQ-012/013).",
)


def build_dev(settings: Settings) -> tuple[Container, IngestService]:
    if settings.environment != "dev":
        raise RuntimeError("devserver chỉ chạy với ENVIRONMENT=dev")
    store = MemoryStore(notice=NOTICE, allowlist=dict(TELEMETRY_ALLOWLIST))
    storage = InMemoryFileStorage()
    values = dict(DEFAULTS)
    values.update(chunk_min_tokens=3)
    if settings.embedding_provider == "fake":
        # Cosine của embedding giả (túi từ băm) giảm theo độ dài chunk: chunk 800 token (cả trang) chỉ
        # đạt ~0,1 dù có đúng từ khóa ⇒ mọi câu hỏi bị "không tìm thấy". Dùng chunk ngắn + ngưỡng thấp.
        values.update(retrieval_min_score=0.05, chunk_tokens=80, chunk_overlap_tokens=15)
    else:
        values.update(retrieval_min_score=0.30)
    cfg = MemoryConfigStore(values)
    config = AppConfig(cfg, ttl_seconds=1.0)
    embedder = build_embedding(settings)
    pipeline = AnsweringPipeline(
        Retriever(embedder, MemoryVectorStore(store), config), build_llm(settings), config
    )
    container = assemble(
        settings,
        config=config,
        uow_factory=MemoryUnitOfWorkFactory(store),
        config_writer=cfg,
        auth=JwtAuthProvider(algorithms=["HS256"], key=settings.jwt_secret.get_secret_value()),
        storage=storage,
        pipeline=pipeline,
    )
    ingest = IngestService(
        MemoryWorkerUnitOfWorkFactory(store), storage, PypdfExtractor(), embedder, config,
        worker_id="local",
    )  # fmt: skip
    return container, ingest


def create_dev_app(static_dir: Path | None = DEFAULT_STATIC) -> FastAPI:
    settings = get_settings()
    container, ingest = build_dev(settings)

    async def ingest_loop(stop: asyncio.Event) -> None:
        await ingest.run_forever(stop, poll_interval=0.3)

    return create_app(container, workers=[ingest_loop], static_dir=static_dir)


def main() -> None:
    for stream in (sys.stdout, sys.stderr):  # Windows: stdout bị chuyển hướng mặc định là cp1252
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-static", action="store_true", help="không phục vụ giao diện đã build")
    args = ap.parse_args()

    static = None if args.no_static else DEFAULT_STATIC
    app = create_dev_app(static)
    if static and static.is_dir():
        web = f"đã build — mở http://{args.host}:{args.port}"
    else:
        web = "CHƯA build — chạy `cd apps/web && pnpm build`, hoặc `pnpm dev` (cổng 5173)"
    logging.getLogger("uvicorn.error").info("Giao diện: %s", web)
    print(f"\n  API:      http://{args.host}:{args.port}/docs\n  Giao diện: {web}\n")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
