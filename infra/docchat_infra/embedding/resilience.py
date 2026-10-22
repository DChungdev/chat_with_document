"""Retry có backoff + circuit breaker cho dịch vụ ngoài (SAD 3.1, 5.2). Dùng cho embedding và LLM."""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

from docchat_core.ports.ingest import EmbeddingError, EmbeddingPort

T = TypeVar("T")


class CircuitBreaker:
    """Mở sau `failure_threshold` lần lỗi liên tiếp; sau `reset_seconds` cho thử lại (half-open)."""

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_seconds: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._threshold = failure_threshold
        self._reset = reset_seconds
        self._clock = clock
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if self._clock() - self._opened_at >= self._reset:
            return False  # half-open: cho một lượt thử
        return True

    def success(self) -> None:
        self._failures, self._opened_at = 0, None

    def failure(self) -> None:
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = self._clock()


class ResilientEmbedding:
    """Bọc một `EmbeddingPort`: timeout do adapter bên trong lo; ở đây là retry + circuit breaker."""

    def __init__(
        self,
        inner: EmbeddingPort,
        *,
        retries: int = 3,
        base_delay: float = 0.5,
        breaker: CircuitBreaker | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        jitter: Callable[[], float] = random.random,
    ) -> None:
        self._inner = inner
        self._retries = retries
        self._base = base_delay
        self._breaker = breaker or CircuitBreaker()
        self._sleep = sleep
        self._jitter = jitter

    @property
    def dimension(self) -> int:
        return self._inner.dimension

    @property
    def model(self) -> str:
        return self._inner.model

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return await self._call(lambda: self._inner.embed_documents(texts))

    async def embed_query(self, text: str) -> list[float]:
        return await self._call(lambda: self._inner.embed_query(text))

    async def _call(self, fn: Callable[[], Awaitable[T]]) -> T:
        if self._breaker.is_open:
            raise EmbeddingError("circuit open", retryable=True)
        last: EmbeddingError | None = None
        for attempt in range(self._retries + 1):
            try:
                result = await fn()
            except EmbeddingError as exc:
                if not exc.retryable:
                    raise  # lỗi do đầu vào: thử lại vô ích và không tính vào breaker
                last = exc
                if attempt < self._retries:
                    await self._sleep(self._base * 2**attempt * (0.5 + self._jitter()))
            else:
                self._breaker.success()
                return result
        self._breaker.failure()
        assert last is not None
        raise last
