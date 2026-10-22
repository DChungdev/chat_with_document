"""VectorStorePort trên PostgreSQL + pgvector (D1). Xem Database_Design_VectorDB mục 4.3, 5.

Chế độ A (mặc định MVP): phạm vi lọc `user_id` + ≤ 10 tài liệu chỉ còn vài nghìn vector nên quét
chính xác bằng chỉ mục B-tree (user_id, document_id) cho recall 100%. Khi phạm vi lớn, chỉ mục HNSW
được dùng cùng `hnsw.iterative_scan` (đặt qua `SearchParams` trong giao dịch) để lọc xong vẫn đủ k dòng.
Giao dịch chạy dưới danh tính người dùng nên RLS là lớp bảo vệ thứ hai ngoài điều kiện user_id tường minh.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from docchat_core.ports.retrieval import RetrievedChunk
from docchat_infra.persistence.session import SearchParams, user_transaction
from docchat_infra.persistence.worker import vector_literal

# Đa dạng theo tài liệu (VectorDB 5.2): mỗi tài liệu tối đa :cap chunk tốt nhất, rồi cắt top-k tổng.
SEARCH_SQL = """
WITH ranked AS (
  SELECT c.id, c.document_id, d.name AS document_name, c.ordinal, c.page_start, c.page_end,
         c.text, 1 - (c.embedding <=> CAST(:q AS vector)) AS score,
         row_number() OVER (PARTITION BY c.document_id
                            ORDER BY c.embedding <=> CAST(:q AS vector)) AS rn
    FROM chunks c
    JOIN documents d ON d.id = c.document_id AND d.status = 'ready'
   WHERE c.user_id = :u
     AND c.document_id = ANY(CAST(:ids AS uuid[]))
     AND c.embedding_model = :model
)
SELECT id, document_id, document_name, ordinal, page_start, page_end, text, score
  FROM ranked
 WHERE rn <= :cap AND score >= :min_score
 ORDER BY score DESC
 LIMIT :k
"""


class PgVectorStore:
    def __init__(self, engine: AsyncEngine, params: SearchParams | None = None) -> None:
        self._engine = engine
        self._params = params or SearchParams()

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
        if not document_ids:
            return []
        async with user_transaction(self._engine, user_id, search=self._params) as conn:
            rows = (
                (
                    await conn.execute(
                        text(SEARCH_SQL),
                        {
                            "q": vector_literal(query_vector),
                            "u": user_id,
                            "ids": list(document_ids),
                            "model": model,
                            "cap": per_document_cap,
                            "min_score": min_score,
                            "k": k,
                        },
                    )
                )
                .mappings()
                .all()
            )
        return [
            RetrievedChunk(
                chunk_id=r["id"], document_id=r["document_id"], document_name=r["document_name"],
                ordinal=r["ordinal"], page_start=r["page_start"], page_end=r["page_end"],
                text=r["text"], score=float(r["score"]),
            )
            for r in rows
        ]  # fmt: skip
