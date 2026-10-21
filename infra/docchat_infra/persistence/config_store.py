from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


class PostgresConfigStore:
    """Đọc toàn bộ `app_config` (bảng nhỏ, không có RLS)."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def load_all(self) -> dict[str, Any]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(text("SELECT key, value FROM app_config"))
            return {k: v for k, v in rows}
