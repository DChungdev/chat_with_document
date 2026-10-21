from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from docchat_infra.persistence import SearchParams, system_transaction, user_transaction

UID = UUID("00000000-0000-0000-0000-0000000000a1")


class FakeConn:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def execute(self, stmt: Any, params: dict[str, Any] | None = None) -> None:
        self.calls.append((str(stmt), params or {}))


class FakeEngine:
    def __init__(self) -> None:
        self.conn = FakeConn()

    @asynccontextmanager
    async def begin(self):  # type: ignore[no-untyped-def]
        yield self.conn


async def test_user_transaction_sets_app_user_id_first() -> None:
    engine = FakeEngine()
    async with user_transaction(engine, UID) as conn:  # type: ignore[arg-type]
        assert conn is engine.conn
    sql, params = engine.conn.calls[0]
    assert "set_config" in sql and ", true)" in sql  # is_local = true ⇒ tương đương SET LOCAL
    assert params == {"name": "app.user_id", "value": str(UID)}
    assert len(engine.conn.calls) == 1


async def test_user_transaction_sets_hnsw_params() -> None:
    engine = FakeEngine()
    async with user_transaction(engine, UID, search=SearchParams(ef_search=64)):  # type: ignore[arg-type]
        pass
    names = {p["name"]: p["value"] for _, p in engine.conn.calls}
    assert names["hnsw.ef_search"] == "64"
    assert names["hnsw.iterative_scan"] == "relaxed_order"
    assert names["app.user_id"] == str(UID)


async def test_system_transaction_sets_no_identity() -> None:
    engine = FakeEngine()
    async with system_transaction(engine):  # type: ignore[arg-type]
        pass
    assert engine.conn.calls == []
