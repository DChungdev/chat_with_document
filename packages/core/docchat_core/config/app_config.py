"""Cấu hình nghiệp vụ đọc từ bảng `app_config` kèm cache TTL và feature flag `qa_enabled`.

Mọi giới hạn bị chặn bởi OQ-008/OQ-011/OQ-012 (kích thước PDF, độ dài câu hỏi, ...) phải đọc qua
lớp này, không hard-code (SAD mục 6).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, Protocol, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Giá trị mặc định khi `app_config` thiếu khóa. Khớp seed ở V005 (Database_Design_SQL mục 10).
DEFAULTS: dict[str, Any] = {
    "qa_enabled": True,
    "max_file_size_bytes": 20 * 1024 * 1024,  # [TBD: OQ-008]
    "max_files_per_user": 50,  # [TBD: OQ-008]
    "max_question_length": 2000,  # [TBD]
    "max_documents_per_question": 10,
    "accepted_types": ["application/pdf"],
    "retrieval_top_k": 8,
    "retrieval_min_score": 0.30,  # hiệu chỉnh bằng bộ câu hỏi chuẩn [TBD: OQ-009]
    "retention_days": None,  # [TBD: OQ-012]
}


class ConfigStore(Protocol):
    """Nguồn đọc `app_config` (adapter PostgreSQL nằm ở infra)."""

    async def load_all(self) -> dict[str, Any]: ...


class AppConfig:
    def __init__(
        self,
        store: ConfigStore,
        *,
        ttl_seconds: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
        defaults: dict[str, Any] | None = None,
    ) -> None:
        self._store = store
        self._ttl = ttl_seconds
        self._clock = clock
        self._defaults = dict(DEFAULTS if defaults is None else defaults)
        self._cache: dict[str, Any] | None = None
        self._loaded_at = 0.0
        self._warned: set[str] = set()

    def invalidate(self) -> None:
        self._cache = None

    async def _snapshot(self) -> dict[str, Any]:
        fresh = self._cache is not None and (self._clock() - self._loaded_at) < self._ttl
        if fresh:
            assert self._cache is not None
            return self._cache
        try:
            self._cache = await self._store.load_all()
            self._loaded_at = self._clock()
        except Exception:
            if self._cache is None:
                raise
            # Giữ giá trị cũ khi DB chập chờn; thử lại ở lần gọi sau.
            logger.warning("app_config reload failed; serving stale values", exc_info=True)
        assert self._cache is not None
        return self._cache

    async def get(self, key: str, default: T | None = None) -> Any:
        values = await self._snapshot()
        if key in values:
            return values[key]
        fallback = self._defaults.get(key, default)
        if key not in self._warned:
            self._warned.add(key)
            logger.warning("app_config key missing; using default", extra={"config_key": key})
        return fallback

    # --- truy cập có kiểu cho các khóa hay dùng ---
    async def qa_enabled(self) -> bool:
        """Kill switch hỏi đáp (PRD 5.1)."""
        return bool(await self.get("qa_enabled", True))

    async def max_file_size_bytes(self) -> int:
        return int(await self.get("max_file_size_bytes"))

    async def max_files_per_user(self) -> int:
        return int(await self.get("max_files_per_user"))

    async def max_question_length(self) -> int:
        return int(await self.get("max_question_length"))

    async def max_documents_per_question(self) -> int:
        return int(await self.get("max_documents_per_question"))

    async def retrieval_top_k(self) -> int:
        return int(await self.get("retrieval_top_k"))

    async def retrieval_min_score(self) -> float:
        return float(await self.get("retrieval_min_score"))
