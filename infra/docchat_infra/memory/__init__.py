"""Adapter trong bộ nhớ: dùng cho unit test và chạy thử không cần hạ tầng. KHÔNG dùng cho production."""

from docchat_infra.memory.storage import InMemoryFileStorage
from docchat_infra.memory.store import MemoryStore, MemoryUnitOfWorkFactory

__all__ = ["InMemoryFileStorage", "MemoryStore", "MemoryUnitOfWorkFactory"]
