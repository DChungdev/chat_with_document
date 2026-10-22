"""VectorStorePort trong bộ nhớ: cùng ngữ nghĩa với bản pgvector (test và đánh giá pipeline)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from uuid import UUID

from docchat_core.domain import DocumentStatus
from docchat_core.ports.retrieval import RetrievedChunk
from docchat_infra.memory.store import MemoryStore


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


class MemoryVectorStore:
    """Vector đã chuẩn hóa L2 nên tích vô hướng = cosine."""

    def __init__(self, store: MemoryStore) -> None:
        self._s = store

    async def search(
        self,
        *,
        user_id: UUID,
        document_ids: Sequence[UUID],
        query_vector: Sequence[float],
        model: str,
        k: int,
        per_document_cap: int,
        min_score: float,
    ) -> list[RetrievedChunk]:
        scope = set(document_ids)
        scored: list[RetrievedChunk] = []
        for row in self._s.chunk_rows.values():
            doc = self._s.documents.get(row["document_id"])
            if (
                row["user_id"] != user_id
                or row["document_id"] not in scope
                or row["model"] != model
                or doc is None
                or doc.status is not DocumentStatus.READY
                or len(row["embedding"]) != len(query_vector)
            ):
                continue
            scored.append(
                RetrievedChunk(
                    row["id"], doc.id, doc.name, row["ordinal"], row["page_start"],
                    row["page_end"], row["text"], _dot(query_vector, row["embedding"]),
                )  # fmt: skip
            )
        per_doc: dict[UUID, int] = defaultdict(int)
        out: list[RetrievedChunk] = []
        for chunk in sorted(scored, key=lambda c: (-c.score, str(c.chunk_id))):
            if chunk.score < min_score or per_doc[chunk.document_id] >= per_document_cap:
                continue
            per_doc[chunk.document_id] += 1
            out.append(chunk)
            if len(out) >= k:
                break
        return out
