"""Adapter embedding qua HTTP theo giao thức tương thích OpenAI (`POST {base}/embeddings`).

Nhiều dịch vụ (kể cả tự host như vLLM/TEI) nói giao thức này, nên đây là adapter TRUNG LẬP nhà
cung cấp. Việc CHỌN nhà cung cấp và vị trí xử lý dữ liệu vẫn chờ pháp chế duyệt [TBD: OQ-012/013];
không gửi dữ liệu thật tới dịch vụ ngoài trước khi có quyết định đó.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import httpx

from docchat_core.ports.ingest import EmbeddingError


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    return vec if norm == 0 else [x / norm for x in vec]


class HttpEmbedding:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        dimension: int,
        api_key: str | None = None,
        timeout: float = 30.0,
        query_timeout: float = 3.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._model = model
        self._dim = dimension
        self._timeout = timeout
        self._query_timeout = query_timeout
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"), headers=headers, transport=transport
        )

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model(self) -> str:
        return self._model

    async def aclose(self) -> None:
        await self._client.aclose()

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return await self._embed(list(texts), self._timeout)

    async def embed_query(self, text: str) -> list[float]:
        return (await self._embed([text], self._query_timeout))[0]

    async def _embed(self, texts: list[str], timeout: float) -> list[list[float]]:
        if not texts:
            return []
        try:
            resp = await self._client.post(
                "/embeddings", json={"model": self._model, "input": texts}, timeout=timeout
            )
        except httpx.HTTPError as exc:  # timeout, mất kết nối...
            raise EmbeddingError(type(exc).__name__, retryable=True) from None
        if resp.status_code == 429 or resp.status_code >= 500:
            raise EmbeddingError(f"http {resp.status_code}", retryable=True)
        if resp.status_code >= 400:
            # 4xx khác (đầu vào quá dài, sai khóa, sai mô hình): thử lại vô ích.
            raise EmbeddingError(f"http {resp.status_code}", retryable=False)
        try:
            data: list[dict[str, Any]] = sorted(resp.json()["data"], key=lambda d: d["index"])
            vectors = [[float(x) for x in d["embedding"]] for d in data]
        except (KeyError, TypeError, ValueError):
            raise EmbeddingError("bad response", retryable=False) from None
        if len(vectors) != len(texts) or any(len(v) != self._dim for v in vectors):
            raise EmbeddingError("dimension mismatch", retryable=False)
        return [_normalize(v) for v in vectors]
