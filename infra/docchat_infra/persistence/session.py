"""Giao dịch gắn danh tính cho Row-Level Security (ADR-07).

Mỗi giao dịch của API phải bắt đầu bằng `SET LOCAL app.user_id`. Quên đặt ⇒ `fn_app_user_id()`
trả NULL ⇒ không thấy dòng nào (an toàn theo mặc định).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine


@dataclass(frozen=True)
class SearchParams:
    """Tham số truy vấn HNSW (Database_Design_VectorDB mục 4.3); giá trị lấy từ cấu hình."""

    ef_search: int = 100
    iterative_scan: str = "relaxed_order"
    max_scan_tuples: int = 20000


async def _set_local(conn: AsyncConnection, name: str, value: str) -> None:
    # set_config(..., is_local => true) tương đương SET LOCAL nhưng nhận tham số ràng buộc.
    await conn.execute(
        text("SELECT set_config(:name, :value, true)"), {"name": name, "value": value}
    )


@asynccontextmanager
async def user_transaction(
    engine: AsyncEngine,
    user_id: UUID,
    *,
    search: SearchParams | None = None,
) -> AsyncIterator[AsyncConnection]:
    """Giao dịch dưới danh tính `user_id` (RLS áp dụng cho vai trò app_api)."""
    async with engine.begin() as conn:
        await _set_local(conn, "app.user_id", str(user_id))
        if search is not None:
            await _set_local(conn, "hnsw.ef_search", str(search.ef_search))
            await _set_local(conn, "hnsw.iterative_scan", search.iterative_scan)
            await _set_local(conn, "hnsw.max_scan_tuples", str(search.max_scan_tuples))
        yield conn


@asynccontextmanager
async def system_transaction(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    """Giao dịch không gắn người dùng — cho worker (chính sách riêng) và bảng không có RLS."""
    async with engine.begin() as conn:
        yield conn
