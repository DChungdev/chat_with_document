"""Vòng đời worker. Logic ingest thật được thêm ở workstream C; ở đây chỉ có khung chạy được."""

from __future__ import annotations

import asyncio
import logging
import signal

from prometheus_client import start_http_server

from docchat_core.config import get_settings
from docchat_infra.observability import configure_logging, setup_tracing

logger = logging.getLogger("docchat.worker")

METRICS_PORT = 9101


async def run(stop: asyncio.Event, poll_interval: float = 2.0) -> None:
    logger.info("worker started", extra={"event": "worker_started"})
    while not stop.is_set():
        # TODO(C2/C6): nhận job bằng fn_claim_ingest_job rồi chạy pipeline ingest.
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
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop.set)
            except NotImplementedError:  # Windows
                signal.signal(sig, lambda *_: loop.call_soon_threadsafe(stop.set))
        await run(stop)

    asyncio.run(_main())


if __name__ == "__main__":
    main()
