"""C5: EmbeddingPort — giả lập, HTTP tương thích OpenAI, retry + circuit breaker."""

from __future__ import annotations

import json
import math
from typing import Any

import httpx
import pytest

from docchat_core.ports.ingest import EmbeddingError
from docchat_infra.embedding import CircuitBreaker, FakeEmbedding, HttpEmbedding, ResilientEmbedding


def cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


# ---------- Fake ----------
async def test_fake_is_deterministic_normalized_and_right_size() -> None:
    e = FakeEmbedding(128)
    (v1,), (v2,) = await e.embed_documents(["Thanh toán trong 30 ngày"]), await e.embed_documents(
        ["Thanh toán trong 30 ngày"]
    )
    assert v1 == v2 and len(v1) == 128 and e.dimension == 128
    assert math.isclose(math.sqrt(sum(x * x for x in v1)), 1.0, rel_tol=1e-9)


async def test_fake_similar_text_scores_higher_than_unrelated() -> None:
    e = FakeEmbedding(512)
    q = await e.embed_query("thời hạn thanh toán là bao lâu")
    near, far = await e.embed_documents(
        ["thời hạn thanh toán là 30 ngày", "bảo hành thiết bị 12 tháng"]
    )
    assert cos(q, near) > cos(q, far)


async def test_fake_handles_empty_text() -> None:
    (v,) = await FakeEmbedding(16).embed_documents([""])
    assert math.isclose(sum(x * x for x in v), 1.0)


# ---------- HTTP ----------
def http(handler: Any, dim: int = 3) -> HttpEmbedding:
    return HttpEmbedding(
        base_url="https://emb.example/v1/",
        model="m1",
        dimension=dim,
        api_key="sk-test",
        transport=httpx.MockTransport(handler),
    )


async def test_http_sends_openai_style_request_and_orders_by_index() -> None:
    seen: dict[str, Any] = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen.update(
            url=str(req.url), auth=req.headers["authorization"], body=json.loads(req.content)
        )
        return httpx.Response(
            200,
            json={
                "data": [{"index": 1, "embedding": [0, 3, 4]}, {"index": 0, "embedding": [3, 0, 4]}]
            },
        )

    vecs = await http(handler).embed_documents(["a", "b"])
    assert seen["url"] == "https://emb.example/v1/embeddings"
    assert seen["auth"] == "Bearer sk-test"
    assert seen["body"] == {"model": "m1", "input": ["a", "b"]}
    assert vecs[0] == pytest.approx([0.6, 0, 0.8]) and vecs[1] == pytest.approx(
        [0, 0.6, 0.8]
    )  # sắp theo index, chuẩn hóa L2


async def test_http_empty_batch_makes_no_request() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        raise AssertionError("không được gọi")

    assert await http(handler).embed_documents([]) == []


@pytest.mark.parametrize(
    ("status", "retryable"),
    [(429, True), (500, True), (503, True), (400, False), (401, False), (422, False)],
)
async def test_http_status_classification(status: int, retryable: bool) -> None:
    with pytest.raises(EmbeddingError) as ei:
        await http(lambda r: httpx.Response(status)).embed_documents(["x"])
    assert ei.value.retryable is retryable


async def test_http_network_errors_are_retryable() -> None:
    def boom(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("hết giờ", request=req)

    with pytest.raises(EmbeddingError) as ei:
        await http(boom).embed_query("x")
    assert ei.value.retryable is True


@pytest.mark.parametrize(
    "payload",
    [
        {"data": [{"index": 0, "embedding": [1, 2]}]},
        {"khong": "co"},
        {"data": []},
        {"data": [{"index": 0}]},
    ],
    ids=["wrong-dim", "no-data-key", "count-mismatch", "no-embedding"],
)
async def test_http_bad_responses_are_permanent(payload: dict[str, Any]) -> None:
    with pytest.raises(EmbeddingError) as ei:
        await http(lambda r: httpx.Response(200, json=payload)).embed_documents(["x"])
    assert ei.value.retryable is False


async def test_http_error_never_contains_text_or_key() -> None:
    with pytest.raises(EmbeddingError) as ei:
        await http(lambda r: httpx.Response(500, text="echo: NOI-DUNG-NHAY-CAM")).embed_documents(
            ["NOI-DUNG-NHAY-CAM"]
        )
    assert "NOI-DUNG" not in str(ei.value) and "sk-test" not in str(ei.value)


async def test_http_query_uses_short_timeout() -> None:
    timeouts: list[Any] = []

    def handler(req: httpx.Request) -> httpx.Response:
        timeouts.append(req.extensions["timeout"])
        return httpx.Response(200, json={"data": [{"index": 0, "embedding": [1, 0, 0]}]})

    e = http(handler)
    await e.embed_query("q")
    await e.embed_documents(["d"])
    assert timeouts[0]["read"] == 3.0 and timeouts[1]["read"] == 30.0


# ---------- Resilient ----------
class Scripted:
    dimension = 2
    model = "scripted"

    def __init__(self, outcomes: list[Any]) -> None:
        self.outcomes, self.calls = outcomes, 0

    async def embed_documents(self, texts: Any) -> list[list[float]]:
        self.calls += 1
        out = self.outcomes.pop(0) if self.outcomes else [[1.0, 0.0]]
        if isinstance(out, Exception):
            raise out
        return [[1.0, 0.0] for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return (await self.embed_documents([text]))[0]


def resilient(inner: Scripted, **kw: Any) -> tuple[ResilientEmbedding, list[float]]:
    sleeps: list[float] = []

    async def sleep(s: float) -> None:
        sleeps.append(s)

    return ResilientEmbedding(inner, sleep=sleep, jitter=lambda: 0.5, **kw), sleeps


async def test_resilient_retries_transient_errors_with_exponential_backoff() -> None:
    inner = Scripted([EmbeddingError("x"), EmbeddingError("x")])
    r, sleeps = resilient(inner, base_delay=1.0)
    assert await r.embed_documents(["a"]) == [[1.0, 0.0]]
    assert inner.calls == 3 and sleeps == [1.0, 2.0]


async def test_resilient_gives_up_after_retries() -> None:
    inner = Scripted([EmbeddingError("x")] * 10)
    r, _ = resilient(inner, retries=2)
    with pytest.raises(EmbeddingError):
        await r.embed_documents(["a"])
    assert inner.calls == 3


async def test_resilient_does_not_retry_permanent_errors() -> None:
    inner = Scripted([EmbeddingError("x", retryable=False)])
    r, sleeps = resilient(inner)
    with pytest.raises(EmbeddingError):
        await r.embed_documents(["a"])
    assert inner.calls == 1 and sleeps == []


async def test_circuit_breaker_opens_then_fails_fast_then_recovers() -> None:
    now = [0.0]
    inner = Scripted([EmbeddingError("x")] * 100)
    breaker = CircuitBreaker(failure_threshold=2, reset_seconds=30, clock=lambda: now[0])
    r, _ = resilient(inner, retries=0, breaker=breaker)
    for _ in range(2):
        with pytest.raises(EmbeddingError):
            await r.embed_documents(["a"])
    assert inner.calls == 2 and breaker.is_open

    with pytest.raises(EmbeddingError, match="circuit open"):
        await r.embed_documents(["a"])
    assert inner.calls == 2  # không gọi dịch vụ đang lỗi

    now[0] = 31.0  # half-open: cho thử lại
    inner.outcomes = []
    assert await r.embed_documents(["a"]) == [[1.0, 0.0]]
    assert not breaker.is_open


async def test_success_resets_failure_count() -> None:
    breaker = CircuitBreaker(failure_threshold=2)
    r, _ = resilient(
        Scripted([EmbeddingError("x"), [1], EmbeddingError("x")]), retries=0, breaker=breaker
    )
    with pytest.raises(EmbeddingError):
        await r.embed_documents(["a"])
    await r.embed_documents(["a"])
    with pytest.raises(EmbeddingError):
        await r.embed_documents(["a"])
    assert not breaker.is_open  # hai lỗi không liên tiếp
