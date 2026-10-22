from __future__ import annotations

from docchat_core.config import Settings
from docchat_core.ports.ingest import EmbeddingPort
from docchat_infra.embedding.fake import FakeEmbedding
from docchat_infra.embedding.http import HttpEmbedding
from docchat_infra.embedding.resilience import ResilientEmbedding


def build_embedding(settings: Settings) -> EmbeddingPort:
    if settings.embedding_provider == "http":
        if not settings.embedding_base_url:
            raise RuntimeError("EMBEDDING_PROVIDER=http cần EMBEDDING_BASE_URL")
        key = settings.embedding_api_key.get_secret_value() if settings.embedding_api_key else None
        return ResilientEmbedding(
            HttpEmbedding(
                base_url=settings.embedding_base_url,
                model=settings.embedding_model,
                dimension=settings.embedding_dim,
                api_key=key,
            )
        )
    if settings.environment in {"staging", "prod"}:
        # Vector giả vô nghĩa với dữ liệu thật; chọn nhà cung cấp chờ OQ-012/013.
        raise RuntimeError("EMBEDDING_PROVIDER=fake không được dùng ở staging/production")
    return FakeEmbedding(settings.embedding_dim, settings.embedding_model)
