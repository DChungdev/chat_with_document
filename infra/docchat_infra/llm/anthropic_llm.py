"""Adapter Claude (Anthropic API) cho `LLMPort` (D4).

Dữ liệu tài liệu của người dùng rời hệ thống khi dùng adapter này, nên CHỈ bật sau khi pháp chế duyệt
nhà cung cấp, vị trí xử lý và điều khoản không-huấn-luyện [TBD: OQ-012/013] — mặc định provider là "fake".
Không log prompt, đoạn trích hay phản hồi; lỗi chỉ mang mã.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Sequence
from typing import Any

import anthropic

from docchat_core.ports.retrieval import ChatTurn, LLMError

logger = logging.getLogger(__name__)

_FALLBACK_BETA = "server-side-fallback-2026-07-01"
# Các mô hình hỗ trợ `fallbacks: "default"` phía server (Claude API): xem tài liệu mô hình.
_FALLBACK_PREFIXES = ("claude-fable-5", "claude-opus-5", "claude-sonnet-5-5")


def map_error(exc: Exception) -> LLMError:
    """Chỉ phân loại theo kiểu lỗi/mã HTTP; không đưa thông điệp của nhà cung cấp ra ngoài."""
    if isinstance(exc, anthropic.APITimeoutError):
        return LLMError("LLM_TIMEOUT", retryable=True)
    if isinstance(exc, anthropic.APIConnectionError):
        return LLMError("LLM_UNAVAILABLE", retryable=True)
    if isinstance(exc, anthropic.RateLimitError):
        return LLMError("LLM_UNAVAILABLE", retryable=True)
    if isinstance(exc, anthropic.APIStatusError):
        return LLMError("LLM_UNAVAILABLE", retryable=exc.status_code >= 500)
    return LLMError("LLM_UNAVAILABLE", retryable=False)


class AnthropicLLM:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "claude-opus-5-5",
        effort: str = "low",
        refusal_fallback: bool = True,
        timeout: float = 60.0,
        client: Any = None,
    ) -> None:
        self._model = model
        self._effort = effort
        # SDK không tự thử lại: ResilientLLM lo retry/backoff/breaker để kiểm soát được độ trễ token đầu.
        self._client = client or anthropic.AsyncAnthropic(
            api_key=api_key, timeout=timeout, max_retries=0
        )
        self._fallback = refusal_fallback and model.startswith(_FALLBACK_PREFIXES)

    def _request(
        self, system: str, user: str, history: Sequence[ChatTurn], max_tokens: int
    ) -> dict[str, Any]:
        messages = [{"role": t.role, "content": t.text} for t in history]
        messages.append({"role": "user", "content": user})
        req: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
            # Hỏi đáp trích xuất từ nguồn không cần suy luận sâu: effort thấp để token đầu về nhanh (≤ 5s p95).
            "output_config": {"effort": self._effort},
        }
        if self._fallback:
            req.update(betas=[_FALLBACK_BETA], fallbacks="default")
        return req

    async def stream(
        self,
        *,
        system: str,
        user: str,
        history: Sequence[ChatTurn] = (),
        max_tokens: int = 1500,
    ) -> AsyncIterator[str]:
        req = self._request(system, user, history, max_tokens)
        api = self._client.beta.messages if self._fallback else self._client.messages
        try:
            async with api.stream(**req) as stream:
                async for text in stream.text_stream:
                    yield text
                final = await stream.get_final_message()
        except LLMError:
            raise
        except Exception as exc:
            raise map_error(exc) from None
        if final.stop_reason == "refusal":
            # Mô hình/bộ lọc an toàn từ chối: thử lại vô ích; hiển thị như lỗi dịch vụ AI.
            raise LLMError("LLM_REFUSED", retryable=False)
        if final.stop_reason == "max_tokens":
            logger.warning("answer truncated by max_tokens", extra={"event": "llm_truncated"})
