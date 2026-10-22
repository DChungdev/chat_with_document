from __future__ import annotations

from docchat_core.config import Settings
from docchat_core.ports.retrieval import LLMPort
from docchat_infra.llm.anthropic_llm import AnthropicLLM
from docchat_infra.llm.fake import FakeLLM
from docchat_infra.llm.resilient import ResilientLLM


def build_llm(settings: Settings) -> LLMPort:
    if settings.llm_provider == "anthropic":
        if settings.llm_api_key is None:
            raise RuntimeError("LLM_PROVIDER=anthropic cần LLM_API_KEY")
        return ResilientLLM(
            AnthropicLLM(
                api_key=settings.llm_api_key.get_secret_value(),
                model=settings.llm_model,
                effort=settings.llm_effort,
                refusal_fallback=settings.llm_refusal_fallback,
            ),
            first_token_timeout=settings.llm_first_token_timeout,
        )
    if settings.environment in {"staging", "prod"}:
        raise RuntimeError("LLM_PROVIDER=fake không được dùng ở staging/production")
    return FakeLLM(delay=settings.fake_llm_delay)
