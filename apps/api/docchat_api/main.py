from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Awaitable, Callable, Coroutine, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from docchat_api.container import Container, build_container
from docchat_api.errors import install_error_handlers
from docchat_api.routers import config_notice, conversations, dev, documents, misc
from docchat_core.config import get_settings
from docchat_infra.observability import configure_logging, current_trace_id, setup_tracing
from docchat_infra.observability.metrics import HTTP_REQUEST_SECONDS

logger = logging.getLogger("docchat.api")

API_PREFIX = "/api/v1"

# CSP cho SPA (cùng nguồn gốc, không script/style nội tuyến). Nginx đặt cùng giá trị cho môi trường container.
SPA_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; "
    "form-action 'self'; frame-ancestors 'none'"
)
API_CSP = "default-src 'none'; frame-ancestors 'none'"
_DOC_PATHS = ("/docs", "/redoc", "/openapi.json")


def _security_headers(path: str, response: Response) -> None:
    h = response.headers
    h.setdefault("X-Content-Type-Options", "nosniff")
    h.setdefault("Referrer-Policy", "no-referrer")
    h.setdefault("X-Frame-Options", "DENY")
    if path.startswith(API_PREFIX):
        h.setdefault("Cache-Control", "no-store")  # dữ liệu người dùng không được cache trung gian
        h.setdefault("Content-Security-Policy", API_CSP)
    elif not path.startswith(_DOC_PATHS):
        h.setdefault("Content-Security-Policy", SPA_CSP)


# Header do reverse proxy thêm vào: yêu cầu có header này đi từ Internet, không phải mạng nội bộ.
_PROXY_HEADERS = ("x-forwarded-for", "x-forwarded-host", "forwarded")


Worker = Callable[[asyncio.Event], Coroutine[Any, Any, None]]


def create_app(
    container: Container | None = None,
    *,
    workers: Sequence[Worker] = (),
    static_dir: Path | None = None,
) -> FastAPI:
    """`workers`: tác vụ nền chạy cùng tiến trình (chế độ local: worker ingest). `static_dir`: thư mục
    giao diện đã build để phục vụ cùng cổng (chế độ local)."""
    settings = container.settings if container else get_settings()
    configure_logging(settings.log_level, service="api")
    setup_tracing("docchat-api", settings.otel_exporter_otlp_endpoint)
    container = container or build_container(settings)
    engine = container.engine

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> Any:
        stop = asyncio.Event()
        tasks = [asyncio.create_task(w(stop)) for w in workers]
        try:
            yield
        finally:
            stop.set()
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
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
            _security_headers(request.url.path, response)
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
    if settings.environment == "dev" and settings.auth_provider == "dev":
        app.include_router(dev.router, prefix=API_PREFIX)  # đăng nhập giả: CHỈ dev

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

    if static_dir is not None and static_dir.is_dir():
        from fastapi.staticfiles import StaticFiles

        # Gắn CUỐI CÙNG để không che /api, /health, /metrics đã khai báo ở trên.
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="web")

    return app


def app_factory() -> FastAPI:
    """Điểm vào cho uvicorn: `uvicorn docchat_api.main:app_factory --factory`."""
    return create_app()
