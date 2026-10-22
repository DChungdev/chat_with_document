"""D2: Retriever — ngưỡng, nhãn, ngân sách ngữ cảnh, lỗi embedding."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID, uuid4

import pytest

from docchat_core.application.retrieval import Retriever
from docchat_core.config import AppConfig
from docchat_core.domain.errors import AnswerFailed
from docchat_core.ports.ingest import EmbeddingError
from docchat_core.ports.retrieval import RetrievedChunk


class Cfg:
    def __init__(self, **v: Any) -> None:
        self.v = v

    async def load_all(self) -> dict[str, Any]:
        return dict(self.v)


class Embedder:
    dimension = 3
    model = "m-1"

    def __init__(self, fail: EmbeddingError | None = None) -> None:
        self.fail, self.queries = fail, []

    async def embed_query(self, text: str) -> list[float]:
        if self.fail:
            raise self.fail
        self.queries.append(text)
        return [1.0, 0.0, 0.0]

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        raise AssertionError


class Store:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks, self.kwargs = chunks, {}

    async def search(self, **kwargs: Any) -> list[RetrievedChunk]:
        self.kwargs = kwargs
        return list(self.chunks)


def rc(score: float, text: str = "nội dung", doc: UUID | None = None) -> RetrievedChunk:
    return RetrievedChunk(uuid4(), doc or uuid4(), "a.pdf", 0, 1, 1, text, score)


def make(chunks: list[RetrievedChunk], **cfg: Any) -> tuple[Retriever, Store, Embedder]:
    store, emb = Store(chunks), Embedder()
    return Retriever(emb, store, AppConfig(Cfg(**cfg), ttl_seconds=0)), store, emb  # type: ignore[arg-type]


async def test_passes_scope_model_and_config_to_store() -> None:
    r, store, emb = make([], retrieval_top_k=5, retrieval_min_score=0.4, retrieval_per_doc_cap=2)
    uid, docs = uuid4(), [uuid4(), uuid4()]
    result = await r.retrieve(uid, "Hạn thanh toán?", docs)
    assert result.sources == [] and emb.queries == ["Hạn thanh toán?"]
    assert store.kwargs == {
        "user_id": uid, "document_ids": docs, "query_vector": [1.0, 0.0, 0.0], "model": "m-1",
        "k": 5, "per_document_cap": 2, "min_score": 0.4,
    }  # fmt: skip


async def test_labels_follow_descending_score_starting_at_one() -> None:
    low, high, mid = rc(0.5), rc(0.9), rc(0.7)
    r, *_ = make([low, high, mid], retrieval_min_score=0.3)
    res = await r.retrieve(uuid4(), "q", [uuid4()])
    assert [(s.label, s.chunk.chunk_id) for s in res.sources] == [
        (1, high.chunk_id), (2, mid.chunk_id), (3, low.chunk_id),
    ]  # fmt: skip
    assert res.by_label(2) is not None and res.by_label(9) is None and res.labels == {1, 2, 3}


async def test_threshold_enforced_even_if_adapter_returns_low_scores() -> None:
    r, *_ = make([rc(0.29), rc(0.30), rc(0.8)], retrieval_min_score=0.30)
    res = await r.retrieve(uuid4(), "q", [uuid4()])
    assert [round(s.chunk.score, 2) for s in res.sources] == [0.8, 0.3]


async def test_nothing_above_threshold_means_no_sources() -> None:
    r, *_ = make([rc(0.1), rc(0.2)], retrieval_min_score=0.3)
    assert (await r.retrieve(uuid4(), "q", [uuid4()])).sources == []


async def test_top_k_cap() -> None:
    r, *_ = make([rc(0.9 - i / 100) for i in range(10)], retrieval_top_k=3, retrieval_min_score=0.1)
    assert len((await r.retrieve(uuid4(), "q", [uuid4()])).sources) == 3


async def test_context_budget_drops_lowest_scoring_chunks_first() -> None:
    big = "x" * 4000  # ≈ 1000 token
    chunks = [rc(0.9, big), rc(0.8, big), rc(0.7, big)]
    r, *_ = make(chunks, context_token_budget=2100, retrieval_min_score=0.1)
    res = await r.retrieve(uuid4(), "q", [uuid4()])
    assert [s.chunk.score for s in res.sources] == [0.9, 0.8]


async def test_always_keeps_at_least_the_best_chunk_even_if_over_budget() -> None:
    r, *_ = make([rc(0.9, "x" * 40000)], context_token_budget=100, retrieval_min_score=0.1)
    assert len((await r.retrieve(uuid4(), "q", [uuid4()])).sources) == 1


@pytest.mark.parametrize(("retryable",), [(True,), (False,)])
async def test_embedding_failure_becomes_answer_failed_at_retrieve_stage(retryable: bool) -> None:
    store, emb = Store([]), Embedder(EmbeddingError("x", retryable=retryable))
    r = Retriever(emb, store, AppConfig(Cfg(), ttl_seconds=0))  # type: ignore[arg-type]
    with pytest.raises(AnswerFailed) as ei:
        await r.retrieve(uuid4(), "q", [uuid4()])
    assert (ei.value.code, ei.value.stage, ei.value.retryable) == (
        "EMBEDDING_UNAVAILABLE",
        "retrieve",
        retryable,
    )
    assert store.kwargs == {}  # không truy vấn kho khi không có vector
