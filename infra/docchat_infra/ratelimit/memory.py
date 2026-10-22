"""Giới hạn tần suất cửa sổ trượt, đếm trong bộ nhớ tiến trình (MVP, không thêm Redis — B5).

Hạn chế đã biết: với N bản sao API, mỗi bản đếm riêng nên hạn mức hiệu dụng tối đa N lần. Chấp nhận
được cho thử nghiệm vài chục người dùng; nếu cần chính xác, chuyển sang bộ đếm trong PostgreSQL.
"""

from __future__ import annotations

import asyncio
import math
import time
from collections import defaultdict, deque
from collections.abc import Callable
from uuid import UUID

from docchat_core.domain.errors import RateLimited


class InMemoryRateLimiter:
    def __init__(self, *, monotonic: Callable[[], float] = time.monotonic) -> None:
        self._hits: dict[tuple[UUID, str], deque[float]] = defaultdict(deque)
        self._mono = monotonic
        self._lock = asyncio.Lock()

    async def hit(self, user_id: UUID, bucket: str, limit: int, window_seconds: int) -> None:
        async with self._lock:
            now = self._mono()
            q = self._hits[(user_id, bucket)]
            while q and now - q[0] >= window_seconds:
                q.popleft()
            if len(q) >= limit:
                raise RateLimited(math.ceil(window_seconds - (now - q[0])))
            q.append(now)
