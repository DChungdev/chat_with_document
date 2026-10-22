"""Cổng cho truy xuất vector và LLM (workstream D)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    document_name: str
    ordinal: int
    page_start: int
    page_end: int
    text: str
    score: float  # 1 - khoảng cách cosine, trong [-1, 1]


class VectorStorePort(Protocol):
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
        """Top-k chunk gần nhất, điểm cao trước.

        Bắt buộc: chỉ chunk của `user_id`, thuộc `document_ids`, tài liệu `ready`, cùng
        `embedding_model` với `model` (không trộn vector của hai mô hình). Mỗi tài liệu tối đa
        `per_document_cap` chunk (một tệp dài không chiếm hết top-k — US-203) và điểm ≥ `min_score`.
        """
        ...


class LLMError(Exception):
    """Lỗi từ dịch vụ LLM. Thông điệp chỉ là mã — không chứa prompt hay nội dung."""

    def __init__(self, code: str = "LLM_UNAVAILABLE", *, retryable: bool = True) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class ChatTurn:
    role: str  # "user" | "assistant"
    text: str


class LLMPort(Protocol):
    def stream(
        self,
        *,
        system: str,
        user: str,
        history: Sequence[ChatTurn] = (),
        max_tokens: int = 1500,
    ) -> AsyncIterator[str]:
        """Phát từng mảnh văn bản. Ném `LLMError`. Hủy (aclose/cancel) phải dừng lời gọi nhà cung cấp."""
        ...
