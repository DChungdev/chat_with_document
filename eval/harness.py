"""Chạy toàn pipeline trên bộ câu hỏi chuẩn và tính chỉ số (D7).

Đường đi giống production: PDF → pypdf → làm sạch/chunk → embedding → kho vector → truy xuất → prompt
→ LLM → bóc nhãn → trích dẫn. Chỉ khác ở adapter (bộ nhớ thay vì PostgreSQL/S3); embedding và LLM
tùy ý cắm (giả lập hoặc thật qua cấu hình môi trường).
"""

from __future__ import annotations

import statistics
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from dataset import DOCS, OUT_OF_SCOPE, doc_pages
from docchat_core.application.answering import AnsweringPipeline
from docchat_core.application.ingest import IngestService
from docchat_core.application.retrieval import RetrievalResult, Retriever
from docchat_core.config import AppConfig
from docchat_core.domain import Document
from docchat_core.ports import Completed, Token
from docchat_core.ports.ingest import EmbeddingPort
from docchat_core.ports.retrieval import LLMPort
from docchat_infra.memory import (
    InMemoryFileStorage,
    MemoryStore,
    MemoryUnitOfWorkFactory,
    MemoryVectorStore,
    MemoryWorkerUnitOfWorkFactory,
)
from docchat_infra.pdf import PypdfExtractor
from docchat_infra.pdf.synthetic import make_pdf

# Ngưỡng nghiệm thu đề xuất (VectorDB mục 10) — chờ PO chốt [TBD: OQ-009]
TARGET_HIT = 0.90
TARGET_CITATION = 0.90
TARGET_OOS = 0.90


@dataclass(frozen=True)
class Params:
    """Tham số cần hiệu chỉnh (D8). Đổi chunking ⇒ phải ingest lại."""

    chunk_tokens: int = 800
    chunk_overlap: int = 100
    chunk_min_tokens: int = 5
    page_span: int = 1
    top_k: int = 8
    min_score: float = 0.30
    per_doc_cap: int = 3

    def chunk_key(self) -> tuple[int, int, int, int]:
        return (self.chunk_tokens, self.chunk_overlap, self.chunk_min_tokens, self.page_span)

    def config(self) -> dict[str, Any]:
        return {
            "chunk_tokens": self.chunk_tokens, "chunk_overlap_tokens": self.chunk_overlap,
            "chunk_min_tokens": self.chunk_min_tokens, "chunk_max_page_span": self.page_span,
            "retrieval_top_k": self.top_k, "retrieval_min_score": self.min_score,
            "retrieval_per_doc_cap": self.per_doc_cap,
        }  # fmt: skip


@dataclass
class CaseResult:
    question: str
    in_scope: bool
    expected: str  # "tệp:trang" hoặc "-"
    retrieved: list[str]
    hit: bool
    grounded: bool
    cited: list[str]
    citation_ok: bool
    keyword_ok: bool
    answer: str


@dataclass
class Metrics:
    params: Params
    cases: list[CaseResult] = field(default_factory=list)
    retrieval_ms: list[float] = field(default_factory=list)
    chunks: int = 0

    def _mean(self, flags: Sequence[bool]) -> float:
        return sum(flags) / len(flags) if flags else 0.0

    @property
    def hit_at_k(self) -> float:
        return self._mean([c.hit for c in self.cases if c.in_scope])

    @property
    def citation_acc(self) -> float:
        return self._mean([c.citation_ok for c in self.cases if c.in_scope])

    @property
    def answer_acc(self) -> float:
        return self._mean([c.keyword_ok for c in self.cases if c.in_scope])

    @property
    def oos_rejected(self) -> float:
        return self._mean([not c.grounded for c in self.cases if not c.in_scope])

    @property
    def false_not_found(self) -> float:
        return self._mean([not c.grounded for c in self.cases if c.in_scope])

    @property
    def retrieval_p95_ms(self) -> float:
        xs = sorted(self.retrieval_ms)
        return xs[min(len(xs) - 1, round(0.95 * (len(xs) - 1)))] if xs else 0.0

    @property
    def score(self) -> float:
        """Mục tiêu hiệu chỉnh: cân bằng bỏ sót (in-scope) và bịa đặt (out-of-scope)."""
        return (self.hit_at_k + self.citation_acc + self.oos_rejected) / 3

    def passes(self) -> bool:
        return (
            self.hit_at_k >= TARGET_HIT
            and self.citation_acc >= TARGET_CITATION
            and self.oos_rejected >= TARGET_OOS
        )


class _Recording(Retriever):
    last: RetrievalResult | None = None

    async def retrieve(
        self, user_id: UUID, question: str, document_ids: Sequence[UUID]
    ) -> RetrievalResult:
        t = time.perf_counter()
        self.last = await super().retrieve(user_id, question, document_ids)
        self.elapsed_ms = (time.perf_counter() - t) * 1000
        return self.last


class Harness:
    def __init__(self, embedder: EmbeddingPort, llm: LLMPort) -> None:
        self.embedder, self.llm = embedder, llm
        self._cache_key: tuple[int, int, int, int] | None = None
        self.store = MemoryStore()
        self.user = uuid4()
        self.doc_ids: dict[str, UUID] = {}

    async def _ingest(self, p: Params) -> int:
        """Ingest lại toàn bộ tài liệu với tham số chunking (chỉ khi chunking thay đổi)."""
        if self._cache_key == p.chunk_key():
            return len(self.store.chunk_rows)
        self.store, self.doc_ids = MemoryStore(), {}
        storage = InMemoryFileStorage()
        api = MemoryUnitOfWorkFactory(self.store)
        for doc in DOCS:
            data = make_pdf(doc_pages(doc))
            did = uuid4()
            key = f"{self.user}/{did}.pdf"
            storage.objects[key] = data
            async with api.for_user(self.user) as uow:
                await uow.documents.add(
                    Document(did, self.user, doc.name, len(data), key, datetime.now(UTC))
                )
                await uow.jobs.enqueue(did, {})
            self.doc_ids[doc.name] = did
        config = AppConfig(_Cfg(p.config()), ttl_seconds=0)
        service = IngestService(
            MemoryWorkerUnitOfWorkFactory(self.store),
            storage,
            PypdfExtractor(),
            self.embedder,
            config,
        )
        while await service.process_next():
            pass
        failed = [d.name for d in self.store.documents.values() if d.status.value != "ready"]
        if failed:
            raise RuntimeError(f"ingest thất bại: {failed}")
        self._cache_key = p.chunk_key()
        return len(self.store.chunk_rows)

    async def run(self, p: Params) -> Metrics:
        m = Metrics(p)
        m.chunks = await self._ingest(p)
        config = AppConfig(_Cfg(p.config()), ttl_seconds=0)
        retriever = _Recording(self.embedder, MemoryVectorStore(self.store), config)
        pipeline = AnsweringPipeline(retriever, self.llm, config)
        scope = list(self.doc_ids.values())
        name_of = {v: k for k, v in self.doc_ids.items()}

        cases = [(f.question, d.name, f.page, f.keyword) for d in DOCS for f in d.facts]
        cases += [(q, "", 0, "") for q in OUT_OF_SCOPE]
        for question, doc_name, page, keyword in cases:
            events = [
                e
                async for e in pipeline.answer(
                    user_id=self.user, question=question, document_ids=scope
                )
            ]
            m.retrieval_ms.append(retriever.elapsed_ms)
            text = "".join(e.text for e in events if isinstance(e, Token))
            done = next(e for e in events if isinstance(e, Completed))
            sources = retriever.last.sources if retriever.last else []
            retrieved = [f"{s.chunk.document_name}:{s.chunk.page_start}" for s in sources]
            cited = [f"{c.document_name}:{c.page}" for c in done.citations]
            in_scope = bool(doc_name)
            expected = f"{doc_name}:{page}" if in_scope else "-"
            m.cases.append(
                CaseResult(
                    question=question, in_scope=in_scope, expected=expected, retrieved=retrieved,
                    hit=expected in retrieved, grounded=done.grounded, cited=cited,
                    citation_ok=done.grounded and expected in cited,
                    keyword_ok=in_scope and keyword.lower() in text.lower(), answer=text,
                )  # fmt: skip
            )
        _ = name_of
        return m


class _Cfg:
    def __init__(self, values: dict[str, Any]) -> None:
        self.values = values

    async def load_all(self) -> dict[str, Any]:
        return dict(self.values)


def summary_table(rows: list[tuple[str, Metrics]]) -> str:
    head = (
        "| Cấu hình | Chunk | hit@k | Trích dẫn đúng | Câu trả lời đúng | Ngoài phạm vi bị loại | "
        "“Không tìm thấy” sai | p95 truy xuất (ms) | Đạt |\n|---|---|---|---|---|---|---|---|---|\n"
    )
    pct = lambda x: f"{100 * x:.0f}%"  # noqa: E731
    body = "\n".join(
        f"| {label} | {m.chunks} | {pct(m.hit_at_k)} | {pct(m.citation_acc)} | {pct(m.answer_acc)} | "
        f"{pct(m.oos_rejected)} | {pct(m.false_not_found)} | {m.retrieval_p95_ms:.1f} | "
        f"{'✔' if m.passes() else '✘'} |"
        for label, m in rows
    )
    return head + body


_ = statistics
