"""Lớp cơ sở cho repository trong bộ nhớ."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from docchat_infra.memory.store import MemoryStore


class _Repo:
    def __init__(self, store: MemoryStore, user_id: UUID | None) -> None:
        self.s = store
        self._uid = user_id

    @property
    def uid(self) -> UUID:
        if self._uid is None:  # UoW `system()` không được chạm dữ liệu của người dùng
            raise PermissionError("no user bound to this unit of work")
        return self._uid
