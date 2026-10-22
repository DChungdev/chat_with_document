"""D1: VectorStorePort — bản trong bộ nhớ (ngữ nghĩa chuẩn) và kiểm cú pháp SQL pgvector."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from docchat_core.domain import Document
from docchat_core.ports.ingest import NewChunk
from docchat_infra.embedding import FakeEmbedding
from docchat_infra.memory import (
    MemoryStore,
    MemoryVectorStore,
    MemoryWorkerUnitOfWorkFactory,
)
from docchat_infra.persistence import vector_store as vs

EMB = FakeEmbedding(256)


class Rig:
    def __init__(self) -> None:
        self.store = MemoryStore()
        self.vec = MemoryVectorStore(self.store)
        self.worker = MemoryWorkerUnitOfWorkFactory(self.store)

    async def doc(
        self,
        user: UUID,
        texts: list[str],
        name: str = "a.pdf",
        ready: bool = True,
        model: str | None = None,
    ) -> Document:
        doc = Document(uuid4(), user, name, 1, "k", datetime.now(UTC))
        self.store.documents[doc.id] = doc
        vecs = await EMB.embed_documents(texts)
        chunks = [
            NewChunk(i, i + 1, i + 1, t, 5, v)
            for i, (t, v) in enumerate(zip(texts, vecs, strict=True))
        ]
        async with self.worker.begin() as uow:
            await uow.chunks.replace(doc.id, user, model or EMB.model, chunks)
        if ready:
            doc.mark_ready(len(texts), datetime.now(UTC))
        return doc

    async def search(self, user: UUID, docs: list[Document], q: str, **kw: Any) -> list[Any]:
        params: dict[str, Any] = {
            "model": EMB.model,
            "k": 8,
            "per_document_cap": 3,
            "min_score": 0.0,
        }
        params.update(kw)
        return await self.vec.search(
            user_id=user, document_ids=[d.id for d in docs],
            query_vector=await EMB.embed_query(q), **params,
        )  # fmt: skip


@pytest.fixture()
def rig() -> Rig:
    return Rig()


async def test_returns_best_match_first_with_pages_and_name(rig: Rig) -> None:
    u = uuid4()
    d = await rig.doc(
        u,
        ["bảo hành thiết bị 12 tháng", "thời hạn thanh toán 30 ngày", "địa điểm giao hàng"],
        "baogia.pdf",
    )
    res = await rig.search(u, [d], "thời hạn thanh toán là bao lâu")
    assert res[0].text == "thời hạn thanh toán 30 ngày" and res[0].page_start == 2
    assert res[0].document_name == "baogia.pdf" and res[0].document_id == d.id
    assert [r.score for r in res] == sorted((r.score for r in res), reverse=True)


async def test_other_users_chunks_never_returned(rig: Rig) -> None:
    alice, bob = uuid4(), uuid4()
    d = await rig.doc(alice, ["thời hạn thanh toán 30 ngày"])
    assert await rig.search(bob, [d], "thời hạn thanh toán") == []  # dù biết document_id


async def test_only_requested_documents_and_only_ready(rig: Rig) -> None:
    u = uuid4()
    a = await rig.doc(u, ["thanh toán 30 ngày"], "a.pdf")
    b = await rig.doc(u, ["thanh toán 45 ngày"], "b.pdf")
    c = await rig.doc(u, ["thanh toán 60 ngày"], "c.pdf", ready=False)
    assert {r.document_id for r in await rig.search(u, [a], "thanh toán")} == {a.id}
    assert {r.document_id for r in await rig.search(u, [a, b, c], "thanh toán")} == {a.id, b.id}


async def test_vectors_from_other_embedding_model_are_ignored(rig: Rig) -> None:
    u = uuid4()
    d = await rig.doc(u, ["thanh toán 30 ngày"], model="old-model")
    assert await rig.search(u, [d], "thanh toán") == []
    assert len(await rig.search(u, [d], "thanh toán", model="old-model")) == 1


async def test_per_document_cap_keeps_a_long_file_from_taking_every_slot(rig: Rig) -> None:
    u = uuid4()
    long_doc = await rig.doc(u, [f"thanh toán điều khoản {i}" for i in range(10)], "dai.pdf")
    other = await rig.doc(u, ["thanh toán chậm bị phạt lãi"], "ngan.pdf")
    res = await rig.search(u, [long_doc, other], "thanh toán điều khoản", k=5, per_document_cap=2)
    ids = [r.document_id for r in res]
    assert ids.count(long_doc.id) <= 2 and other.id in ids  # US-203: có chunk từ cả hai tài liệu


async def test_min_score_and_k(rig: Rig) -> None:
    u = uuid4()
    d = await rig.doc(u, ["thanh toán 30 ngày", "bảo hành 12 tháng", "giao hàng tại kho"])
    assert await rig.search(u, [d], "xyz không liên quan", min_score=0.2) == []
    assert len(await rig.search(u, [d], "thanh toán bảo hành giao hàng", k=2)) == 2


async def test_deleted_document_leaves_nothing_to_find(rig: Rig) -> None:
    u = uuid4()
    d = await rig.doc(u, ["thanh toán 30 ngày"])
    del rig.store.documents[d.id]
    assert await rig.search(u, [d], "thanh toán") == []


# ---------- SQL pgvector (cú pháp + bất biến an toàn) ----------
pglast = pytest.importorskip("pglast")


def to_pg(sql: str) -> str:
    n = 0

    def sub(m: re.Match[str]) -> str:
        nonlocal n
        n += 1
        return f"${n}"

    return re.sub(r"(?<!:):(\w+)", sub, sql)


def test_search_sql_parses_and_contains_the_safety_filters() -> None:
    pglast.parse_sql(to_pg(vs.SEARCH_SQL))
    sql = " ".join(vs.SEARCH_SQL.split())
    assert "c.user_id = :u" in sql  # lọc người dùng tường minh (ngoài RLS)
    assert "c.document_id = ANY(CAST(:ids AS uuid[]))" in sql
    assert "d.status = 'ready'" in sql
    assert "c.embedding_model = :model" in sql  # không so sánh vector khác mô hình
    assert "PARTITION BY c.document_id" in sql and "rn <= :cap" in sql  # đa dạng theo tài liệu
    assert "score >= :min_score" in sql and "LIMIT :k" in sql
    assert "<=>" in sql  # khoảng cách cosine


async def test_pg_store_sets_user_identity_and_hnsw_params() -> None:
    from contextlib import asynccontextmanager

    calls: list[tuple[str, Any]] = []

    class Result:
        def mappings(self) -> Result:
            return self

        def all(self) -> list[Any]:
            return []

    class Conn:
        async def execute(self, stmt: Any, params: Any = None) -> Result:
            calls.append((str(stmt), params))
            return Result()

    class Engine:
        @asynccontextmanager
        async def begin(self):  # type: ignore[no-untyped-def]
            yield Conn()

    store = vs.PgVectorStore(Engine())  # type: ignore[arg-type]
    uid = uuid4()
    out = await store.search(
        user_id=uid,
        document_ids=[uuid4()],
        query_vector=[0.5, 0.5],
        model="m",
        k=8,
        per_document_cap=3,
        min_score=0.3,
    )
    assert out == []
    names = [p["name"] for s, p in calls if "set_config" in s]
    assert names[0] == "app.user_id" and "hnsw.ef_search" in names
    search = calls[-1][1]
    assert search["q"] == "[0.5,0.5]" and search["u"] == uid and search["model"] == "m"
    assert search["cap"] == 3 and search["k"] == 8 and search["min_score"] == 0.3


async def test_pg_store_short_circuits_without_documents() -> None:
    class Boom:
        def begin(self) -> None:
            raise AssertionError("không được mở giao dịch")

    store = vs.PgVectorStore(Boom())  # type: ignore[arg-type]
    assert (
        await store.search(
            user_id=uuid4(),
            document_ids=[],
            query_vector=[1.0],
            model="m",
            k=1,
            per_document_cap=1,
            min_score=0,
        )
        == []
    )
