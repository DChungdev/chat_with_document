from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from docchat_core.config import AppConfig, get_settings
from docchat_infra.observability import configure_logging, current_trace_id, setup_tracing
from docchat_infra.observability.metrics import HTTP_REQUEST_SECONDS
from docchat_infra.persistence import PostgresConfigStore, create_engine

logger = logging.getLogger("docchat.api")

# Header do reverse proxy thêm vào: yêu cầu có header này đi từ Internet, không phải mạng nội bộ.
_PROXY_HEADERS = ("x-forwarded-for", "x-forwarded-host", "forwarded")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, service="api")
    setup_tracing("docchat-api", settings.otel_exporter_otlp_endpoint)
    engine = create_engine(settings.database_url.get_secret_value())
    app_config = AppConfig(PostgresConfigStore(engine), ttl_seconds=settings.app_config_ttl_seconds)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> Any:
        yield
        await engine.dispose()

    app = FastAPI(title="Chat với tài liệu — API", version="0.1.0", lifespan=lifespan)
    app.state.engine = engine
    app.state.app_config = app_config

    @app.middleware("http")
    async def observe(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["x-request-id"] = request_id
            return response
        finally:
            elapsed = time.perf_counter() - start
            route_obj = request.scope.get("route")
            # Dùng mẫu đường dẫn (/documents/{id}) chứ không phải đường dẫn thật.
            route = getattr(route_obj, "path", "unmatched")
            HTTP_REQUEST_SECONDS.labels(request.method, route, str(status)).observe(elapsed)
            logger.info(
                "request",
                extra={
                    "request_id": request_id,
                    "trace_id": current_trace_id(),
                    "method": request.method,
                    "route": route,
                    "status": status,
                    "duration_ms": round(elapsed * 1000, 1),
                },
            )

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        """Liveness: tiến trình còn sống."""
        return {"status": "ok"}

    @app.get("/ready", include_in_schema=False)
    async def ready() -> JSONResponse:
        """Readiness: kết nối được CSDL."""
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            logger.warning("readiness check failed", extra={"error_code": "DB_UNAVAILABLE"})
            return JSONResponse({"status": "unavailable"}, status_code=503)
        return JSONResponse({"status": "ready"})

    @app.get("/metrics", include_in_schema=False)
    async def metrics(request: Request) -> Response:
        """Chỉ mạng nội bộ: proxy luôn thêm X-Forwarded-*, nên yêu cầu qua proxy bị từ chối."""
        if any(h in request.headers for h in _PROXY_HEADERS):
            return Response(status_code=404)
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


def app_factory() -> FastAPI:
    """Điểm vào cho uvicorn: `uvicorn docchat_api.main:app_factory --factory`."""
    return create_app()
