"""Retry (chỉ trước khi có token đầu), timeout token đầu và circuit breaker cho LLM (D4)."""

from __future__ import annotations

import asyncio
import random
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence

from docchat_core.ports.retrieval import ChatTurn, LLMError, LLMPort
from docchat_infra.embedding.resilience import CircuitBreaker


class ResilientLLM:
    """Không bao giờ thử lại SAU khi đã phát token: người dùng đã thấy một phần câu trả lời, thử lại
    sẽ lặp/đứt mạch. Lỗi giữa chừng được báo lên để B7 đánh dấu `interrupted`."""

    def __init__(
        self,
        inner: LLMPort,
        *,
        retries: int = 2,
        base_delay: float = 0.5,
        first_token_timeout: float = 20.0,
        breaker: CircuitBreaker | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        jitter: Callable[[], float] = random.random,
    ) -> None:
        self._inner = inner
        self._retries = retries
        self._base = base_delay
        self._first_token_timeout = first_token_timeout
        self._breaker = breaker or CircuitBreaker()
        self._sleep = sleep
        self._jitter = jitter

    async def stream(
        self,
        *,
        system: str,
        user: str,
        history: Sequence[ChatTurn] = (),
        max_tokens: int = 1500,
    ) -> AsyncIterator[str]:
        if self._breaker.is_open:
            raise LLMError(
                "LLM_UNAVAILABLE", retryable=True
            )  # fail fast, không gọi dịch vụ đang lỗi
        last: LLMError | None = None
        for attempt in range(self._retries + 1):
            inner = self._inner.stream(
                system=system, user=user, history=history, max_tokens=max_tokens
            )
            emitted = False
            try:
                while True:
                    try:
                        if emitted:
                            piece = await anext(inner)
                        else:
                            piece = await asyncio.wait_for(anext(inner), self._first_token_timeout)
                    except StopAsyncIteration:
                        self._breaker.success()
                        return
                    except TimeoutError:
                        raise LLMError("LLM_TIMEOUT", retryable=True) from None
                    emitted = True
                    yield piece
            except LLMError as exc:
                if emitted or not exc.retryable:
                    if exc.retryable:
                        self._breaker.failure()
                    raise
                last = exc
            finally:
                if aclose := getattr(inner, "aclose", None):
                    await aclose()  # dừng lời gọi nhà cung cấp khi bị hủy
            if attempt < self._retries:
                await self._sleep(self._base * 2**attempt * (0.5 + self._jitter()))
        self._breaker.failure()
        assert last is not None
        raise last
