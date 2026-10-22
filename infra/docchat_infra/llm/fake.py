"""LLM giả lập, xác định, theo kiểu TRÍCH XUẤT: chọn câu trong nguồn gần câu hỏi nhất.

Dùng cho dev, test và đánh giá pipeline mà không cần dịch vụ ngoài. Không phải mô hình thật: nó chỉ
chứng minh đường ống (prompt → nhãn nguồn → trích dẫn) hoạt động. KHÔNG dùng cho production.
"""

from __future__ import annotations

import asyncio
import html
import re
from collections.abc import AsyncIterator, Sequence

from docchat_core.application.answering import NOT_FOUND_MESSAGE
from docchat_core.ports.retrieval import ChatTurn

_SOURCE = re.compile(r'<nguon id="S(\d+)"[^>]*>\n(.*?)\n</nguon>', re.DOTALL)
_QUESTION = re.compile(r"<cau_hoi>\n(.*?)\n</cau_hoi>", re.DOTALL)
_WORD = re.compile(r"\w+", re.UNICODE)
_STOP = {"là", "và", "của", "có", "bao", "nhiêu", "gì", "được", "cho", "the", "a", "of", "is"}


def _words(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) > 1}


class FakeLLM:
    def __init__(self, delay: float = 0.0, min_overlap: int = 2) -> None:
        self.delay = delay
        self.min_overlap = min_overlap
        self.calls = 0
        self.last_system = ""
        self.last_user = ""

    async def stream(
        self,
        *,
        system: str,
        user: str,
        history: Sequence[ChatTurn] = (),
        max_tokens: int = 1500,
    ) -> AsyncIterator[str]:
        self.calls += 1
        self.last_system, self.last_user = system, user
        answer = self._answer(user)
        for word in answer.split(" "):
            if self.delay:
                await asyncio.sleep(self.delay)
            yield word + " "

    def _answer(self, user: str) -> str:
        q = _QUESTION.search(user)
        qw = _words(html.unescape(q.group(1))) if q else set()
        best: tuple[int, str, str] = (0, "", "")
        for label, body in _SOURCE.findall(user):
            for sentence in re.split(r"(?<=[.!?…])\s+", html.unescape(body)):
                overlap = len(qw & _words(sentence))
                if overlap > best[0]:
                    best = (overlap, label, sentence.strip())
        if best[0] < self.min_overlap:
            return NOT_FOUND_MESSAGE
        return f"{best[2].rstrip('.')} [S{best[1]}]."
