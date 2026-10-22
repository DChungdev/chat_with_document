from __future__ import annotations

import logging

from docchat_core.config import Settings
from docchat_core.ports import FileStoragePort
from docchat_infra.memory import InMemoryFileStorage
from docchat_infra.storage.s3 import S3FileStorage

logger = logging.getLogger(__name__)


def build_storage(settings: Settings) -> FileStoragePort:
    if settings.storage_backend == "s3":
        return S3FileStorage(
            bucket=settings.s3_bucket,
            endpoint_url=settings.s3_endpoint_url,
            access_key=settings.s3_access_key.get_secret_value(),
            secret_key=settings.s3_secret_key.get_secret_value(),
            region=settings.s3_region,
            sse=settings.s3_sse,
        )
    if settings.environment in {"staging", "prod"}:
        raise RuntimeError("STORAGE_BACKEND=memory không được dùng ở staging/production")
    logger.warning("using in-memory file storage", extra={"event": "storage_memory"})
    return InMemoryFileStorage()
