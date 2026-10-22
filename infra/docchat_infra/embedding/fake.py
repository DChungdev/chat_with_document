"""Embedding giả lập, xác định: túi từ băm → vector chuẩn hóa L2.

Văn bản dùng chung nhiều từ thì cosine cao hơn, đủ để test truy xuất có ý nghĩa mà không cần
mô hình thật. KHÔNG dùng cho production.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence

_WORD = re.compile(r"\w+", re.UNICODE)


class FakeEmbedding:
    def __init__(self, dimension: int = 1024, model: str = "fake-bow-v1") -> None:
        self._dim = dimension
        self._model = model

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model(self) -> str:
        return self._model

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for word in _WORD.findall(text.lower()):
            digest = hashlib.blake2b(word.encode(), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self._dim
            vec[index] += 1.0 if digest[4] & 1 else -1.0
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0:  # văn bản không có từ: vector cố định, vẫn chuẩn hóa
            vec[0], norm = 1.0, 1.0
        return [x / norm for x in vec]

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._vector(text)
