"""Lắp ráp phụ thuộc (composition root). Tests truyền `Container` dựng bằng adapter trong bộ nhớ."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncEngine

from docchat_core.application.chat import ChatService
from docchat_core.application.citations import CitationService
from docchat_core.application.compliance import ComplianceService
from docchat_core.application.documents import DocumentsService
from docchat_core.application.flags import FlagService
from docchat_core.application.telemetry import TelemetryService
from docchat_core.config import AppConfig, Settings
from docchat_core.domain.errors import AnswerFailed
from docchat_core.ports import (
    AnswerEvent,
    AnswerPipeline,
    AuthProvider,
    ConfigWriter,
    FileStoragePort,
    RateLimiter,
    UnitOfWorkFactory,
)
from docchat_infra.auth import JwtAuthProvider, OidcKeyResolver
from docchat_infra.memory import InMemoryFileStorage
from docchat_infra.observability import hash_user_id, inject_trace_context
from docchat_infra.observability.metrics import PrometheusChatMetrics
from docchat_infra.persistence import (
    PgUnitOfWorkFactory,
    PostgresConfigStore,
    create_engine,
)
from docchat_infra.ratelimit import InMemoryRateLimiter

logger = logging.getLogger("docchat.api")


class UnavailablePipeline:
    """Giữ chỗ cho tới khi workstream D (retrieval + LLM) được nối vào: luôn báo lỗi rõ ràng."""

    async def answer(
        self, *, user_id: UUID, question: str, document_ids: Sequence[UUID]
    ) -> AsyncIterator[AnswerEvent]:
        raise AnswerFailed("LLM_UNAVAILABLE", "generate", True)
        yield  # pragma: no cover  (biến hàm thành async generator)


@dataclass
class Container:
    settings: Settings
    config: AppConfig
    uow_factory: UnitOfWorkFactory
    auth: AuthProvider
    limiter: RateLimiter
    documents: DocumentsService
    chat: ChatService
    compliance: ComplianceService
    citations: CitationService
    telemetry: TelemetryService
    flags: FlagService
    engine: AsyncEngine | None = None


def build_auth(settings: Settings) -> AuthProvider:
    if settings.auth_provider == "oidc":
        if not (settings.oidc_jwks_url and settings.oidc_issuer and settings.oidc_audience):
            raise RuntimeError("AUTH_PROVIDER=oidc cần OIDC_JWKS_URL, OIDC_ISSUER, OIDC_AUDIENCE")
        return JwtAuthProvider(
            algorithms=["RS256", "ES256"],
            key_resolver=OidcKeyResolver(settings.oidc_jwks_url),
            issuer=settings.oidc_issuer,
            audience=settings.oidc_audience,
        )
    if settings.environment in {"staging", "prod"}:
        raise RuntimeError("AUTH_PROVIDER=dev không được dùng ở staging/production")
    return JwtAuthProvider(algorithms=["HS256"], key=settings.jwt_secret.get_secret_value())


def build_storage(settings: Settings) -> FileStoragePort:
    if settings.storage_backend == "s3":
        raise RuntimeError("Adapter S3 thuộc task C1, chưa được triển khai")
    if settings.environment in {"staging", "prod"}:
        raise RuntimeError("STORAGE_BACKEND=memory không được dùng ở staging/production")
    logger.warning("using in-memory file storage", extra={"event": "storage_memory"})
    return InMemoryFileStorage()


def assemble(
    settings: Settings,
    *,
    config: AppConfig,
    uow_factory: UnitOfWorkFactory,
    config_writer: ConfigWriter,
    auth: AuthProvider,
    storage: FileStoragePort,
    pipeline: AnswerPipeline,
    limiter: RateLimiter | None = None,
    engine: AsyncEngine | None = None,
) -> Container:
    limiter = limiter or InMemoryRateLimiter()
    salt = settings.telemetry_salt.get_secret_value()
    return Container(
        settings=settings,
        config=config,
        uow_factory=uow_factory,
        auth=auth,
        limiter=limiter,
        documents=DocumentsService(
            uow_factory, storage, config, limiter, trace_context=inject_trace_context
        ),
        chat=ChatService(uow_factory, pipeline, config, limiter, metrics=PrometheusChatMetrics()),
        compliance=ComplianceService(uow_factory),
        citations=CitationService(uow_factory, config),
        telemetry=TelemetryService(uow_factory, lambda uid: hash_user_id(uid, salt)),
        flags=FlagService(config_writer, config),
        engine=engine,
    )


def build_container(settings: Settings) -> Container:
    engine = create_engine(settings.database_url.get_secret_value())
    store = PostgresConfigStore(engine)
    config = AppConfig(store, ttl_seconds=settings.app_config_ttl_seconds)
    return assemble(
        settings,
        config=config,
        uow_factory=PgUnitOfWorkFactory(engine),
        config_writer=store,
        auth=build_auth(settings),
        storage=build_storage(settings),
        pipeline=UnavailablePipeline(),
        engine=engine,
    )
