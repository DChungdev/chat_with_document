"""Truy xuất: câu hỏi → các đoạn nguồn đủ liên quan, có nhãn [S1]…[Sn] (D2, VectorDB mục 5)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from docchat_core.application.chunking import estimate_tokens
from docchat_core.config import AppConfig
from docchat_core.domain.errors import AnswerFailed
from docchat_core.ports.ingest import EmbeddingError, EmbeddingPort
from docchat_core.ports.retrieval import RetrievedChunk, VectorStorePort


@dataclass(frozen=True)
class SourceChunk:
    label: int  # S1 = 1: nguồn có điểm cao nhất
    chunk: RetrievedChunk


@dataclass(frozen=True)
class RetrievalResult:
    sources: list[SourceChunk]

    @property
    def labels(self) -> set[int]:
        return {s.label for s in self.sources}

    def by_label(self, label: int) -> SourceChunk | None:
        return next((s for s in self.sources if s.label == label), None)


class Retriever:
    def __init__(self, embedder: EmbeddingPort, store: VectorStorePort, config: AppConfig) -> None:
        self._embedder = embedder
        self._store = store
        self._config = config

    async def retrieve(
        self, user_id: UUID, question: str, document_ids: Sequence[UUID]
    ) -> RetrievalResult:
        """Rỗng nghĩa là KHÔNG có căn cứ — người gọi trả “không tìm thấy”, không gọi LLM (ADR-04)."""
        k = int(await self._config.get("retrieval_top_k"))
        min_score = float(await self._config.get("retrieval_min_score"))
        cap = int(await self._config.get("retrieval_per_doc_cap"))
        budget = int(await self._config.get("context_token_budget"))

        try:
            vector = await self._embedder.embed_query(question)  # chỉ nằm trong bộ nhớ, không lưu
        except EmbeddingError as exc:
            raise AnswerFailed("EMBEDDING_UNAVAILABLE", "retrieve", exc.retryable) from None

        found = await self._store.search(
            user_id=user_id,
            document_ids=document_ids,
            query_vector=vector,
            model=self._embedder.model,
            k=k,
            per_document_cap=cap,
            min_score=min_score,
        )
        # Kiểm lại ngoài adapter: ngưỡng là quy tắc nghiệp vụ, không được phụ thuộc vào adapter.
        ranked = sorted((c for c in found if c.score >= min_score), key=lambda c: -c.score)[:k]

        kept: list[RetrievedChunk] = []
        used = 0
        for chunk in ranked:  # cắt từ chunk điểm thấp nhất khi vượt ngân sách ngữ cảnh
            tokens = estimate_tokens(chunk.text)
            if kept and used + tokens > budget:
                break
            kept.append(chunk)
            used += tokens
        return RetrievalResult([SourceChunk(i, c) for i, c in enumerate(kept, start=1)])
