"""Adapter trong bộ nhớ: dùng cho unit test và chạy thử không cần hạ tầng. KHÔNG dùng cho production."""

from docchat_infra.memory.config import MemoryConfigStore
from docchat_infra.memory.defaults import TELEMETRY_ALLOWLIST
from docchat_infra.memory.storage import InMemoryFileStorage
from docchat_infra.memory.store import MemoryStore, MemoryUnitOfWorkFactory
from docchat_infra.memory.vector import MemoryVectorStore
from docchat_infra.memory.worker import MemoryWorkerUnitOfWorkFactory

__all__ = [
    "TELEMETRY_ALLOWLIST",
    "InMemoryFileStorage",
    "MemoryConfigStore",
    "MemoryStore",
    "MemoryUnitOfWorkFactory",
    "MemoryVectorStore",
    "MemoryWorkerUnitOfWorkFactory",
]
