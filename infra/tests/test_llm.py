"""D4: adapter LLM — giả lập, Claude (client giả), retry/timeout/circuit breaker."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import anthropic
import httpx2
import pytest

from docchat_core.application.answering import NOT_FOUND_MESSAGE, SYSTEM_PROMPT, build_user_prompt
from docchat_core.application.retrieval import RetrievalResult, SourceChunk
from docchat_core.config import Settings
from docchat_core.ports.retrieval import ChatTurn, LLMError, RetrievedChunk
from docchat_infra.embedding import CircuitBreaker
from docchat_infra.llm import AnthropicLLM, FakeLLM, ResilientLLM, build_llm
from docchat_infra.llm.anthropic_llm import map_error


def prompt(*texts: str, question: str = "Thời hạn thanh toán là bao lâu?") -> str:
    chunks = [RetrievedChunk(uuid4(), uuid4(), "a.pdf", 0, 3, 3, t, 0.9) for t in texts]
    return build_user_prompt(
        RetrievalResult([SourceChunk(i, c) for i, c in enumerate(chunks, 1)]), question
    )


async def collect(it: AsyncIterator[str]) -> str:
    return "".join([p async for p in it])


# ---------- FakeLLM ----------
async def test_fake_llm_extracts_best_sentence_with_label() -> None:
    llm = FakeLLM()
    out = await collect(
        llm.stream(
            system=SYSTEM_PROMPT,
            user=prompt("Bảo hành 12 tháng.", "Thời hạn thanh toán là 30 ngày kể từ hóa đơn."),
        )
    )
    assert out.strip() == "Thời hạn thanh toán là 30 ngày kể từ hóa đơn [S2]."


async def test_fake_llm_says_not_found_when_nothing_overlaps() -> None:
    out = await collect(
        FakeLLM().stream(system="s", user=prompt("Bảo hành 12 tháng.", question="Thời tiết?"))
    )
    assert out.strip() == NOT_FOUND_MESSAGE


async def test_fake_llm_reads_escaped_prompt_back_correctly() -> None:
    out = await collect(
        FakeLLM().stream(
            system="s", user=prompt("Giá <5 triệu> & rẻ.", question="Giá bao nhiêu triệu?")
        )
    )
    assert "<5 triệu> & rẻ" in out


# ---------- Claude adapter (client giả) ----------
class FakeStream:
    def __init__(
        self, pieces: list[str], stop_reason: str = "end_turn", error: Exception | None = None
    ) -> None:
        self.pieces, self.stop_reason, self.error = pieces, stop_reason, error

    async def __aenter__(self) -> FakeStream:
        return self

    async def __aexit__(self, *a: object) -> None:
        return None

    @property
    def text_stream(self) -> AsyncIterator[str]:
        async def gen() -> AsyncIterator[str]:
            for p in self.pieces:
                yield p
            if self.error:
                raise self.error

        return gen()

    async def get_final_message(self) -> Any:
        return SimpleNamespace(stop_reason=self.stop_reason)


class FakeClient:
    def __init__(self, stream: FakeStream) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        outer = self

        class Api:
            def __init__(self, name: str) -> None:
                self.name = name

            def stream(self, **kw: Any) -> FakeStream:
                outer.calls.append((self.name, kw))
                return stream

        self.messages, self.beta = SimpleNamespace(stream=Api("messages").stream), SimpleNamespace(
            messages=SimpleNamespace(stream=Api("beta").stream)
        )


async def test_claude_request_shape_with_server_side_fallback() -> None:
    client = FakeClient(FakeStream(["Xin ", "chào"]))
    llm = AnthropicLLM(api_key="k", model="claude-opus-5-5", effort="low", client=client)
    out = await collect(
        llm.stream(
            system="SYS",
            user="USR",
            history=[ChatTurn("user", "trước"), ChatTurn("assistant", "đáp")],
            max_tokens=777,
        )
    )
    assert out == "Xin chào"
    api, kw = client.calls[0]
    assert api == "beta"
    assert kw["model"] == "claude-opus-5-5" and kw["max_tokens"] == 777 and kw["system"] == "SYS"
    assert kw["output_config"] == {"effort": "low"}
    assert kw["betas"] == ["server-side-fallback-2026-07-01"] and kw["fallbacks"] == "default"
    assert [m["role"] for m in kw["messages"]] == ["user", "assistant", "user"]
    assert kw["messages"][-1] == {"role": "user", "content": "USR"}
    assert "thinking" not in kw and "temperature" not in kw  # tham số đã bị gỡ ở mô hình mới → 400


async def test_claude_without_fallback_uses_plain_messages_api() -> None:
    client = FakeClient(FakeStream(["x"]))
    llm = AnthropicLLM(api_key="k", model="claude-haiku-5-5", client=client)
    await collect(llm.stream(system="s", user="u"))
    api, kw = client.calls[0]
    assert api == "messages" and "betas" not in kw and "fallbacks" not in kw


async def test_claude_fallback_can_be_disabled() -> None:
    client = FakeClient(FakeStream(["x"]))
    await collect(
        AnthropicLLM(api_key="k", refusal_fallback=False, client=client).stream(
            system="s", user="u"
        )
    )
    assert client.calls[0][0] == "messages"


async def test_claude_refusal_is_a_non_retryable_error() -> None:
    llm = AnthropicLLM(
        api_key="k", client=FakeClient(FakeStream(["một phần"], stop_reason="refusal"))
    )
    with pytest.raises(LLMError) as ei:
        await collect(llm.stream(system="s", user="u"))
    assert ei.value.code == "LLM_REFUSED" and ei.value.retryable is False


_REQ = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


@pytest.mark.parametrize(
    ("exc", "code", "retryable"),
    [
        (anthropic.APITimeoutError(request=_REQ), "LLM_TIMEOUT", True),
        (anthropic.APIConnectionError(request=_REQ), "LLM_UNAVAILABLE", True),
        (
            anthropic.RateLimitError("x", response=httpx2.Response(429, request=_REQ), body=None),
            "LLM_UNAVAILABLE",
            True,
        ),
        (
            anthropic.InternalServerError(
                "x", response=httpx2.Response(500, request=_REQ), body=None
            ),
            "LLM_UNAVAILABLE",
            True,
        ),
        (
            anthropic.AuthenticationError(
                "x", response=httpx2.Response(401, request=_REQ), body=None
            ),
            "LLM_UNAVAILABLE",
            False,
        ),
        (
            anthropic.BadRequestError("x", response=httpx2.Response(400, request=_REQ), body=None),
            "LLM_UNAVAILABLE",
            False,
        ),
        (RuntimeError("lạ"), "LLM_UNAVAILABLE", False),
    ],
)
def test_error_mapping(exc: Exception, code: str, retryable: bool) -> None:
    mapped = map_error(exc)
    assert (mapped.code, mapped.retryable) == (code, retryable)


async def test_claude_stream_error_is_mapped_without_leaking_details() -> None:
    secret = "NOI-DUNG-NHAY-CAM"
    llm = AnthropicLLM(
        api_key="k",
        client=FakeClient(
            FakeStream(["a"], error=anthropic.APIConnectionError(message=secret, request=_REQ))
        ),
    )
    with pytest.raises(LLMError) as ei:
        await collect(llm.stream(system="s", user="u"))
    assert secret not in str(ei.value) and ei.value.retryable


def test_factory_rules() -> None:
    assert isinstance(build_llm(Settings(environment="dev")), FakeLLM)
    with pytest.raises(RuntimeError, match="staging/production"):
        build_llm(Settings(environment="staging"))
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        build_llm(Settings(llm_provider="anthropic"))
    llm = build_llm(Settings(llm_provider="anthropic", llm_api_key="sk-x", environment="prod"))  # type: ignore[arg-type]
    assert isinstance(llm, ResilientLLM)


# ---------- Resilient ----------
class Scripted:
    """Mỗi lần stream() lấy một kịch bản: list[str | Exception]."""

    def __init__(self, scripts: list[list[Any]]) -> None:
        self.scripts, self.calls, self.closed = scripts, 0, 0

    def stream(
        self, *, system: str, user: str, history: Sequence[ChatTurn] = (), max_tokens: int = 1500
    ) -> AsyncIterator[str]:
        script = self.scripts[min(self.calls, len(self.scripts) - 1)]
        self.calls += 1
        outer = self

        async def gen() -> AsyncIterator[str]:
            try:
                for item in script:
                    if isinstance(item, Exception):
                        raise item
                    if isinstance(item, float):
                        await asyncio.sleep(item)
                        continue
                    yield item
            finally:
                outer.closed += 1

        return gen()


def resilient(inner: Scripted, **kw: Any) -> tuple[ResilientLLM, list[float]]:
    sleeps: list[float] = []

    async def sleep(s: float) -> None:
        sleeps.append(s)

    return ResilientLLM(inner, sleep=sleep, jitter=lambda: 0.5, **kw), sleeps  # type: ignore[arg-type]


async def test_retries_before_first_token_with_backoff() -> None:
    inner = Scripted([[LLMError("LLM_UNAVAILABLE")], [LLMError("LLM_UNAVAILABLE")], ["ok"]])
    r, sleeps = resilient(inner, base_delay=1.0)
    assert await collect(r.stream(system="s", user="u")) == "ok"
    assert inner.calls == 3 and sleeps == [1.0, 2.0]


async def test_never_retries_after_a_token_was_emitted() -> None:
    inner = Scripted([["một ", LLMError("LLM_TIMEOUT")], ["lặp lại"]])
    r, _ = resilient(inner)
    got: list[str] = []
    with pytest.raises(LLMError):
        async for p in r.stream(system="s", user="u"):
            got.append(p)
    assert got == ["một "] and inner.calls == 1  # không phát lại phần đầu cho người dùng


async def test_non_retryable_error_is_not_retried() -> None:
    inner = Scripted([[LLMError("LLM_REFUSED", retryable=False)]])
    r, sleeps = resilient(inner)
    with pytest.raises(LLMError):
        await collect(r.stream(system="s", user="u"))
    assert inner.calls == 1 and sleeps == []


async def test_first_token_timeout_raises_llm_timeout() -> None:
    inner = Scripted([[10.0, "muộn"]])
    r, _ = resilient(inner, first_token_timeout=0.05, retries=0)
    with pytest.raises(LLMError) as ei:
        await collect(r.stream(system="s", user="u"))
    assert ei.value.code == "LLM_TIMEOUT" and inner.closed == 1  # lời gọi bị đóng, không treo


async def test_gives_up_after_retries_and_opens_circuit() -> None:
    now = [0.0]
    inner = Scripted([[LLMError("LLM_UNAVAILABLE")]] * 20)
    breaker = CircuitBreaker(failure_threshold=2, reset_seconds=30, clock=lambda: now[0])
    r, _ = resilient(inner, retries=1, breaker=breaker)
    for _ in range(2):
        with pytest.raises(LLMError):
            await collect(r.stream(system="s", user="u"))
    calls = inner.calls
    with pytest.raises(LLMError):
        await collect(r.stream(system="s", user="u"))
    assert inner.calls == calls  # mạch mở: báo lỗi ngay, không gọi dịch vụ đang hỏng

    now[0] = 31.0
    inner.scripts = [["hồi phục"]]
    inner.calls = 0
    assert await collect(r.stream(system="s", user="u")) == "hồi phục" and not breaker.is_open


async def test_closing_the_stream_early_closes_the_provider_call() -> None:
    inner = Scripted([["a", "b", "c"]])
    r, _ = resilient(inner)
    stream = r.stream(system="s", user="u")
    assert await anext(stream) == "a"
    await stream.aclose()  # người dùng bấm Dừng
    assert inner.closed == 1
