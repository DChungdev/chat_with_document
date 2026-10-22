"""Truy xuất vector trên PostgreSQL + pgvector thật (cần Docker; chạy trong CI bằng `-m integration`)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from docchat_core.domain import Document, UserRole
from docchat_core.ports.ingest import NewChunk
from docchat_infra.embedding import FakeEmbedding
from docchat_infra.persistence import (
    PgUnitOfWorkFactory,
    PgVectorStore,
    PgWorkerUnitOfWorkFactory,
    create_engine,
)

pytestmark = pytest.mark.integration

DIM = 1024
EMB = FakeEmbedding(DIM)


@pytest_asyncio.fixture()
async def rig(migrated: Any, dsn_for: Any) -> AsyncIterator[dict[str, Any]]:
    def url(role: str) -> str:
        return dsn_for(migrated, role).replace("postgresql://", "postgresql+psycopg://")

    api, worker = create_engine(url("docchat_api"), pool_size=2), create_engine(
        url("docchat_worker"), pool_size=2
    )
    yield {
        "api_engine": api,
        "api": PgUnitOfWorkFactory(api),
        "worker": PgWorkerUnitOfWorkFactory(worker),
    }
    await api.dispose()
    await worker.dispose()


async def new_user(rig: dict[str, Any]) -> UUID:
    async with rig["api"].system() as uow:
        return (await uow.users.upsert_by_subject(f"it|{uuid4()}", UserRole.USER)).id


async def make_doc(
    rig: dict[str, Any],
    user: UUID,
    texts: list[str],
    name: str = "a.pdf",
    ready: bool = True,
    model: str = "fake-bow-v1",
) -> Document:
    did = uuid4()
    doc = Document(did, user, name, 10, f"{user}/{did}.pdf", datetime.now(UTC))
    async with rig["api"].for_user(user) as uow:
        await uow.documents.add(doc)
    vecs = await EMB.embed_documents(texts)
    chunks = [
        NewChunk(i, i + 1, i + 1, t, 5, v) for i, (t, v) in enumerate(zip(texts, vecs, strict=True))
    ]
    async with rig["worker"].begin() as uow:
        await uow.chunks.replace(did, user, model, chunks)
        if ready:
            await uow.documents.mark_ready(did, len(texts), datetime.now(UTC))
    return doc


async def search(
    rig: dict[str, Any], user: UUID, docs: list[Document], q: str, **kw: Any
) -> list[Any]:
    params: dict[str, Any] = {
        "model": "fake-bow-v1",
        "k": 8,
        "per_document_cap": 3,
        "min_score": 0.0,
    }
    params.update(kw)
    return await PgVectorStore(rig["api_engine"]).search(
        user_id=user,
        document_ids=[d.id for d in docs],
        query_vector=await EMB.embed_query(q),
        **params,
    )


async def test_returns_best_chunk_first_with_page_and_name(rig: dict[str, Any]) -> None:
    u = await new_user(rig)
    d = await make_doc(
        rig,
        u,
        ["bảo hành thiết bị 12 tháng", "thời hạn thanh toán 30 ngày", "địa điểm giao hàng"],
        "baogia.pdf",
    )
    res = await search(rig, u, [d], "thời hạn thanh toán là bao lâu")
    assert res[0].text == "thời hạn thanh toán 30 ngày" and res[0].page_start == 2
    assert res[0].document_name == "baogia.pdf" and res[0].score > res[-1].score


async def test_rls_and_user_filter_block_other_users(rig: dict[str, Any]) -> None:
    alice, bob = await new_user(rig), await new_user(rig)
    d = await make_doc(rig, alice, ["thời hạn thanh toán 30 ngày"])
    assert (
        await search(rig, bob, [d], "thời hạn thanh toán") == []
    )  # biết document_id vẫn không lấy được
    assert len(await search(rig, alice, [d], "thời hạn thanh toán")) == 1


async def test_only_ready_documents_and_same_embedding_model(rig: dict[str, Any]) -> None:
    u = await new_user(rig)
    ready = await make_doc(rig, u, ["thanh toán 30 ngày"], "r.pdf")
    pending = await make_doc(rig, u, ["thanh toán 45 ngày"], "p.pdf", ready=False)
    old = await make_doc(rig, u, ["thanh toán 60 ngày"], "o.pdf", model="old-model")
    res = await search(rig, u, [ready, pending, old], "thanh toán")
    assert {r.document_id for r in res} == {ready.id}


async def test_per_document_cap_min_score_and_k(rig: dict[str, Any]) -> None:
    u = await new_user(rig)
    long_doc = await make_doc(rig, u, [f"thanh toán điều khoản {i}" for i in range(10)], "dai.pdf")
    other = await make_doc(rig, u, ["thanh toán chậm bị phạt lãi"], "ngan.pdf")
    res = await search(rig, u, [long_doc, other], "thanh toán điều khoản", k=5, per_document_cap=2)
    ids = [r.document_id for r in res]
    assert ids.count(long_doc.id) <= 2 and other.id in ids and len(res) <= 5
    assert await search(rig, u, [long_doc], "xyz hoàn toàn khác", min_score=0.5) == []


async def test_deleted_document_is_not_searchable(rig: dict[str, Any]) -> None:
    u = await new_user(rig)
    d = await make_doc(rig, u, ["thanh toán 30 ngày"])
    async with rig["api"].for_user(u) as uow:
        await uow.documents.delete(d.id)
    assert await search(rig, u, [d], "thanh toán") == []
