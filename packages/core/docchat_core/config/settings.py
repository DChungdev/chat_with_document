"""Cấu hình triển khai: endpoint và secret lấy từ biến môi trường / secret manager.

Giới hạn nghiệp vụ (kích thước tệp, top-k, ...) KHÔNG nằm ở đây mà ở bảng `app_config`
(xem `AppConfig`), để đổi được mà không cần deploy.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_REDACTED = "***"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    environment: Literal["dev", "staging", "prod", "test"] = "dev"
    log_level: str = "INFO"

    # CSDL: ứng dụng dùng vai trò app_api / app_worker; migration dùng migrator.
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://docchat_api:docchat_dev@localhost:5432/docchat"
    )
    migrator_database_url: SecretStr = SecretStr(
        "postgresql+psycopg://migrator:docchat_dev@localhost:5432/docchat"
    )

    # Object storage (S3-compatible)
    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_bucket: str = "docchat-documents"
    s3_access_key: SecretStr = SecretStr("minioadmin")
    s3_secret_key: SecretStr = SecretStr("minioadmin")
    s3_region: str = "us-east-1"

    # Nhà cung cấp ngoài: chọn sau khi OQ-012/013 được chốt. Mặc định dùng adapter giả lập.
    llm_provider: str = "fake"
    embedding_provider: str = "fake"
    embedding_dim: int = Field(default=1024, ge=1)
    llm_api_key: SecretStr | None = None
    embedding_api_key: SecretStr | None = None

    # Xác thực [TBD: OQ-014]
    auth_provider: str = "dev"
    jwt_secret: SecretStr = SecretStr("dev-only-change-me")

    # Quan sát
    otel_exporter_otlp_endpoint: str | None = None
    telemetry_salt: SecretStr = SecretStr("dev-only-change-me")

    # Cache giá trị app_config (giây)
    app_config_ttl_seconds: float = Field(default=30.0, ge=0)

    def safe_dump(self) -> dict[str, Any]:
        """Bản dùng để log/debug: mọi secret bị che."""
        out: dict[str, Any] = {}
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, SecretStr):
                out[name] = _REDACTED
            elif name.endswith("_url") and isinstance(value, str) and "@" in value:
                out[name] = _REDACTED
            else:
                out[name] = value
        return out


@lru_cache
def get_settings() -> Settings:
    return Settings()
