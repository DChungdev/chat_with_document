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
    s3_sse: str = ""  # "AES256" ở staging/prod; để trống với MinIO dev (không có KMS)

    # Nhà cung cấp ngoài: chọn sau khi OQ-012/013 được chốt. Mặc định dùng adapter giả lập.
    llm_provider: Literal["fake", "anthropic"] = "fake"
    llm_model: str = "claude-opus-5-5"  # mô hình cụ thể + vị trí xử lý dữ liệu [TBD: OQ-012/013]
    llm_effort: Literal["low", "medium", "high", "xhigh", "max"] = (
        "low"  # hỏi đáp trích xuất: ưu tiên token đầu nhanh
    )
    llm_refusal_fallback: bool = True  # bật fallbacks phía server khi mô hình từ chối (Claude API)
    llm_first_token_timeout: float = Field(default=20.0, gt=0)
    fake_llm_delay: float = Field(
        default=0.0, ge=0
    )  # giây/từ của LLM giả: để thấy streaming và thử nút Dừng khi dev
    embedding_provider: Literal["fake", "http"] = "fake"
    embedding_base_url: str | None = None  # dịch vụ tương thích OpenAI /embeddings
    embedding_model: str = "fake-bow-v1"
    embedding_dim: int = Field(default=1024, ge=1)
    llm_api_key: SecretStr | None = None
    embedding_api_key: SecretStr | None = None

    # Xác thực [TBD: OQ-014]: "dev" (HS256, khóa chung) hoặc "oidc" (JWKS của IdP)
    auth_provider: Literal["dev", "oidc"] = "dev"
    jwt_secret: SecretStr = SecretStr("dev-only-change-me-0123456789-abcdef")
    oidc_jwks_url: str | None = None
    oidc_issuer: str | None = None
    oidc_audience: str | None = None

    # Lưu tệp: "s3" cần adapter của task C1; "memory" chỉ để dev/test (mất dữ liệu khi khởi động lại)
    storage_backend: Literal["memory", "s3"] = "memory"

    # Origin của SPA khi khác origin với API (danh sách phân tách bằng dấu phẩy). Rỗng = không CORS.
    cors_origins: str = ""

    # Quan sát
    otel_exporter_otlp_endpoint: str | None = None
    telemetry_salt: SecretStr = SecretStr("dev-only-change-me-0123456789-abcdef")

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
