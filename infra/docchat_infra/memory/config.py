"""Cấu hình trong bộ nhớ (ConfigStore + ConfigWriter) cho chế độ chạy local và test."""

from __future__ import annotations

from typing import Any


class MemoryConfigStore:
    def __init__(self, values: dict[str, Any] | None = None) -> None:
        self.values: dict[str, Any] = dict(values or {})

    async def load_all(self) -> dict[str, Any]:
        return dict(self.values)

    async def set_value(self, key: str, value: Any) -> None:
        self.values[key] = value
