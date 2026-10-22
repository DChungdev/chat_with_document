from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from docchat_api.container import Container, build_container
from docchat_api.errors import install_error_handlers
from docchat_api.routers import config_notice, conversations, documents, misc
from docchat_core.config import get_settings
from docchat_infra.observability import configure_logging, current_trace_id, setup_tracing
from docchat_infra.observability.metrics import HTTP_REQUEST_SECONDS

logger = logging.getLogger("docchat.api")

API_PREFIX = "/api/v1"

# Header do reverse proxy thêm vào: yêu cầu có header này đi từ Internet, không phải mạng nội bộ.
_PROXY_HEADERS = ("x-forwarded-for", "x-forwarded-host", "forwarded")


def create_app(container: Container | None = None) -> FastAPI:
    settings = container.settings if container else get_settings()
    configure_logging(settings.log_level, service="api")
    setup_tracing("docchat-api", settings.otel_exporter_otlp_endpoint)
    container = container or build_container(settings)
    engine = container.engine

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> Any:
        yield
        if engine is not None:
            await engine.dispose()

    app = FastAPI(title="Chat với tài liệu — API", version="0.1.0", lifespan=lifespan)
    app.state.container = container
    install_error_handlers(app)

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    if origins:  # chỉ origin của SPA, không bao giờ "*" (API_Design 2.4)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-Id"],
            expose_headers=["Location", "Retry-After", "X-Request-Id"],
        )

    @app.middleware("http")
    async def observe(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
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
            extra: dict[str, Any] = {
                "request_id": request_id,
                "trace_id": current_trace_id(),
                "method": request.method,
                "route": route,
                "status": status,
                "duration_ms": round(elapsed * 1000, 1),
            }
            if user_hash := getattr(request.state, "user_hash", None):
                extra["user_hash"] = user_hash
            logger.info("request", extra=extra)

    app.include_router(config_notice.router, prefix=API_PREFIX)
    app.include_router(documents.router, prefix=API_PREFIX)
    app.include_router(conversations.router, prefix=API_PREFIX)
    app.include_router(misc.router, prefix=API_PREFIX)

    @app.get("/health", include_in_schema=False)
    @app.get(f"{API_PREFIX}/health/live", include_in_schema=False)
    async def health() -> dict[str, str]:
        """Liveness: tiến trình còn sống."""
        return {"status": "ok"}

    @app.get("/ready", include_in_schema=False)
    @app.get(f"{API_PREFIX}/health/ready", include_in_schema=False)
    async def ready() -> JSONResponse:
        """Readiness: kết nối được CSDL."""
        try:
            if engine is None:
                raise RuntimeError("no engine")
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
