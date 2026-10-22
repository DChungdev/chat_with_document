import json
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

    async def set_value(self, key: str, value: Any) -> None:
        """Cập nhật một khóa đã tồn tại (app_api chỉ có quyền UPDATE trên app_config)."""
        async with self._engine.begin() as conn:
            res = await conn.execute(
                text("UPDATE app_config SET value = CAST(:v AS jsonb) WHERE key = :k"),
                {"k": key, "v": json.dumps(value)},
            )
            if not res.rowcount:
                raise LookupError(f"app_config key not found: {key}")
