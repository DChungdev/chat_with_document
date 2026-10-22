"""Ingestion worker: nhận job từ hàng đợi PostgreSQL và biến PDF thành chỉ mục tìm kiếm."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import socket

from prometheus_client import start_http_server

from docchat_core.application.ingest import IngestService
from docchat_core.config import AppConfig, Settings, get_settings
from docchat_infra.embedding import build_embedding
from docchat_infra.observability import configure_logging, setup_tracing
from docchat_infra.observability.metrics import PrometheusIngestMetrics
from docchat_infra.pdf import PypdfExtractor
from docchat_infra.persistence import PgWorkerUnitOfWorkFactory, PostgresConfigStore, create_engine
from docchat_infra.storage import build_storage

logger = logging.getLogger("docchat.worker")

METRICS_PORT = 9101


def build_service(settings: Settings) -> tuple[IngestService, AppConfig, object]:
    if settings.storage_backend != "s3":
        # Worker và API là hai tiến trình: bộ nhớ riêng không thể chia sẻ tệp giữa chúng.
        raise RuntimeError("Worker cần STORAGE_BACKEND=s3 (API và worker phải dùng chung kho tệp)")
    engine = create_engine(settings.database_url.get_secret_value(), pool_size=4)
    config = AppConfig(PostgresConfigStore(engine), ttl_seconds=settings.app_config_ttl_seconds)
    service = IngestService(
        PgWorkerUnitOfWorkFactory(engine),
        build_storage(settings),
        PypdfExtractor(),
        build_embedding(settings),
        config,
        worker_id=f"{socket.gethostname()}-{os.getpid()}",
        metrics=PrometheusIngestMetrics(),
    )
    return service, config, engine


async def run(stop: asyncio.Event, poll_interval: float = 2.0) -> None:
    """Vòng đời tối thiểu (không CSDL): dùng cho test khung worker."""
    logger.info("worker started", extra={"event": "worker_started"})
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=poll_interval)
        except TimeoutError:
            continue
    logger.info("worker stopped", extra={"event": "worker_stopped"})


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, service="worker")
    setup_tracing("docchat-worker", settings.otel_exporter_otlp_endpoint)
    start_http_server(METRICS_PORT)  # /metrics, chỉ mạng nội bộ

    async def _main() -> None:
        service, _, engine = build_service(settings)
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop.set)
            except NotImplementedError:  # Windows
                signal.signal(sig, lambda *_: loop.call_soon_threadsafe(stop.set))
        logger.info("worker started", extra={"event": "worker_started"})
        try:
            await service.run_forever(stop)
        finally:
            await engine.dispose()  # type: ignore[attr-defined]
            logger.info("worker stopped", extra={"event": "worker_stopped"})

    asyncio.run(_main())


if __name__ == "__main__":
    main()
