"""Repository/UoW PostgreSQL trên CSDL thật (cần Docker; chạy trong CI bằng `-m integration`).

Kiểm các điều mà bản trong bộ nhớ chỉ mô phỏng: RLS, cascade, trigger audit, FK SET NULL,
ràng buộc CHECK, kiểu enum/jsonb/uuid[] và phân trang keyset.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import psycopg
import pytest
import pytest_asyncio

from docchat_core.domain import (
    Citation,
    Conversation,
    Document,
    DocumentStatus,
    Message,
    TelemetryEvent,
    UserRole,
)
from docchat_infra.persistence import PgUnitOfWorkFactory, PostgresConfigStore, create_engine

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture()
async def factory(migrated: Any, dsn_for: Any) -> AsyncIterator[PgUnitOfWorkFactory]:
    url = dsn_for(migrated, "docchat_api").replace("postgresql://", "postgresql+psycopg://")
    engine = create_engine(url, pool_size=2)
    yield PgUnitOfWorkFactory(engine)
    await engine.dispose()


async def new_user(f: PgUnitOfWorkFactory) -> Any:
    async with f.system() as uow:
        return await uow.users.upsert_by_subject(f"it|{uuid4()}", UserRole.USER)


def make_doc(user_id: Any, minutes: int = 0) -> Document:
    did = uuid4()
    return Document(
        did, user_id, "baogia.pdf", 1234, f"{user_id}/{did}.pdf",
        datetime.now(UTC) + timedelta(minutes=minutes), content_sha256="a" * 64,
    )  # fmt: skip


def worker_sql(migrated: Any, dsn_for: Any, sql: str, params: tuple[Any, ...] = ()) -> None:
    with psycopg.connect(dsn_for(migrated, "docchat_worker")) as conn:
        conn.execute(sql, params)


async def test_user_upsert_is_stable_per_subject(factory: PgUnitOfWorkFactory) -> None:
    subject = f"it|{uuid4()}"
    async with factory.system() as uow:
        a = await uow.users.upsert_by_subject(subject, UserRole.USER)
        b = await uow.users.upsert_by_subject(subject, UserRole.OPS)
    assert a.id == b.id and b.role is UserRole.USER  # vai trò không bị ghi đè bởi lần sau


async def test_document_roundtrip_enqueue_and_idempotency(factory: PgUnitOfWorkFactory) -> None:
    user = await new_user(factory)
    doc, key = make_doc(user.id), uuid4()
    async with factory.for_user(user.id) as uow:
        await uow.documents.add(doc)
        await uow.jobs.enqueue(doc.id, {"traceparent": "00-abc-def-01"})
        await uow.idempotency.put("document_upload", key, doc.id)
    async with factory.for_user(user.id) as uow:
        got = await uow.documents.get(doc.id)
        assert got is not None
        assert (got.name, got.size_bytes, got.status) == (
            "baogia.pdf",
            1234,
            DocumentStatus.PROCESSING,
        )
        assert await uow.idempotency.get("document_upload", key) == doc.id
        assert await uow.documents.count() == 1
        assert await uow.documents.get_many([doc.id, uuid4()]) == [got]


async def test_rls_blocks_cross_user_access_through_repositories(
    factory: PgUnitOfWorkFactory,
) -> None:
    a, b = await new_user(factory), await new_user(factory)
    doc = make_doc(a.id)
    async with factory.for_user(a.id) as uow:
        await uow.documents.add(doc)
    async with factory.for_user(b.id) as uow:
        assert await uow.documents.get(doc.id) is None
        assert await uow.documents.get_many([doc.id]) == []
        assert await uow.documents.count() == 0
        assert await uow.documents.delete(doc.id) is False  # không xóa được tài liệu người khác
    async with factory.for_user(a.id) as uow:
        assert await uow.documents.get(doc.id) is not None


async def test_list_page_uses_keyset_pagination_newest_first(factory: PgUnitOfWorkFactory) -> None:
    user = await new_user(factory)
    docs = [make_doc(user.id, minutes=i) for i in range(5)]
    async with factory.for_user(user.id) as uow:
        for d in docs:
            await uow.documents.add(d)
    seen: list[Any] = []
    cursor = None
    async with factory.for_user(user.id) as uow:
        while True:
            page, cursor = await uow.documents.list_page(2, cursor)
            seen += [d.id for d in page]
            if cursor is None:
                break
    assert seen == [d.id for d in reversed(docs)]


async def test_delete_cascades_and_invalidates_citations(
    factory: PgUnitOfWorkFactory, migrated: Any, dsn_for: Any
) -> None:
    user = await new_user(factory)
    doc = make_doc(user.id)
    conv_id, chunk_id = uuid4(), uuid4()
    now = datetime.now(UTC)
    async with factory.for_user(user.id) as uow:
        await uow.documents.add(doc)
        await uow.jobs.enqueue(doc.id, {})
    worker_sql(
        migrated, dsn_for,
        "INSERT INTO chunks (id, document_id, user_id, ordinal, page_start, page_end, text,"
        " token_count, embedding, embedding_model)"
        " VALUES (%s,%s,%s,0,4,4,'Thanh toán trong 30 ngày.',5,"
        " (SELECT array_fill(0.1::real, ARRAY[1024])::vector),'fake')",
        (chunk_id, doc.id, user.id),
    )  # fmt: skip
    ai_id = uuid4()
    async with factory.for_user(user.id) as uow:
        await uow.conversations.add(Conversation(conv_id, user.id, now, now))
        q = Message.new_user(uuid4(), conv_id, user.id, "Hỏi?", now)
        await uow.messages.add(q)
        ai = Message.new_ai(ai_id, conv_id, user.id, q.id, now)
        ai.start_streaming()
        await uow.messages.add(ai)
        ai.append("Trong 30 ngày.")
        ai.complete(True, now)
        await uow.messages.update(ai)
        cit = Citation(uuid4(), ai_id, user.id, 1, 4, doc.id, chunk_id, doc.name)
        await uow.citations.add_many([cit])
    async with factory.for_user(user.id) as uow:
        view = await uow.citations.get_view(cit.id)
        assert view and view.snippet == "Thanh toán trong 30 ngày." and view.citation.valid
        assert len(await uow.citations.for_message(ai_id)) == 1

    async with factory.for_user(user.id) as uow:
        assert await uow.documents.delete(doc.id) is True
    async with factory.for_user(user.id) as uow:
        view = await uow.citations.get_view(cit.id)
        assert view is not None and view.snippet is None  # chunk đã bị cascade
        c = view.citation
        assert (c.valid, c.document_id, c.document_name) == (
            False,
            None,
            None,
        )  # FK SET NULL + trigger
    with psycopg.connect(dsn_for(migrated, "docchat_worker")) as conn:
        assert conn.execute(
            "SELECT count(*) FROM chunks WHERE document_id=%s", (doc.id,)
        ).fetchone() == (0,)
    with psycopg.connect(dsn_for(migrated, "postgres", "postgres")) as su:
        actions = {
            r[0]
            for r in su.execute(
                "SELECT action::text FROM docchat.audit_log WHERE entity_id=%s", (doc.id,)
            )
        }
    assert actions == {"document_uploaded", "document_deleted"}  # trigger ghi, không do ứng dụng


async def test_messages_lookup_by_client_id_and_reply(factory: PgUnitOfWorkFactory) -> None:
    user = await new_user(factory)
    conv_id, cmid, now = uuid4(), uuid4(), datetime.now(UTC)
    async with factory.for_user(user.id) as uow:
        await uow.conversations.add(Conversation(conv_id, user.id, now, now))
        q = Message.new_user(uuid4(), conv_id, user.id, "Hỏi?", now, cmid)
        await uow.messages.add(q)
        ai = Message.new_ai(uuid4(), conv_id, user.id, q.id, now)
        ai.start_streaming()
        await uow.messages.add(ai)
    async with factory.for_user(user.id) as uow:
        assert (await uow.messages.find_user_message_by_client_id(conv_id, cmid)).id == q.id  # type: ignore[union-attr]
        assert (await uow.messages.find_reply(q.id)).id == ai.id  # type: ignore[union-attr]
        assert await uow.messages.find_user_message_by_client_id(conv_id, uuid4()) is None


async def test_message_text_is_capped_to_db_limit(factory: PgUnitOfWorkFactory) -> None:
    user = await new_user(factory)
    conv_id, now = uuid4(), datetime.now(UTC)
    async with factory.for_user(user.id) as uow:
        await uow.conversations.add(Conversation(conv_id, user.id, now, now))
        q = Message.new_user(uuid4(), conv_id, user.id, "x" * 25000, now)
        await uow.messages.add(q)  # ck_messages_text_len = 20000: repo cắt, không lỗi
        stored = await uow.messages.get(q.id)
    assert stored is not None and len(stored.text) == 20000


async def test_notice_accept_is_idempotent_and_audited_once(
    factory: PgUnitOfWorkFactory, migrated: Any, dsn_for: Any
) -> None:
    user = await new_user(factory)
    async with factory.for_user(user.id) as uow:
        notice = await uow.notices.current()
        assert notice is not None and await uow.notices.has_accepted(notice.version) is False
        await uow.notices.accept(notice.version)
        await uow.notices.accept(notice.version)
        assert await uow.notices.has_accepted(notice.version) is True
    with psycopg.connect(dsn_for(migrated, "postgres", "postgres")) as su:
        n = su.execute(
            "SELECT count(*) FROM docchat.audit_log WHERE user_id=%s AND action='notice_accepted'",
            (user.id,),
        ).fetchone()
    assert n == (1,)


async def test_telemetry_allowlist_and_trigger(
    factory: PgUnitOfWorkFactory, migrated: Any, dsn_for: Any
) -> None:
    user = await new_user(factory)
    async with factory.for_user(user.id) as uow:
        allow = await uow.telemetry.allowlist()
        assert "total_ms" in allow["answer_completed"]
        ev = TelemetryEvent(datetime.now(UTC), "answer_completed", "h" * 64, uuid4(), "0.1.0",
                            {"total_ms": 42, "grounded": True})  # fmt: skip
        await uow.telemetry.add_many([ev])
    with psycopg.connect(dsn_for(migrated, "postgres", "postgres")) as su:
        props = su.execute(
            "SELECT props FROM docchat.telemetry_events WHERE session_id=%s", (ev.session_id,)
        ).fetchone()
    assert props is not None and props[0] == {"total_ms": 42, "grounded": True}

    bad = TelemetryEvent(datetime.now(UTC), "answer_completed", "h" * 64, uuid4(), "0.1.0",
                         {"question": "lọt vào"})  # fmt: skip
    with pytest.raises(Exception, match="not allowed"):  # trigger CSDL là lớp phòng thủ thứ hai
        async with factory.for_user(user.id) as uow:
            await uow.telemetry.add_many([bad])


async def test_config_store_reads_and_updates_kill_switch(
    factory: PgUnitOfWorkFactory, migrated: Any, dsn_for: Any
) -> None:
    url = dsn_for(migrated, "docchat_api").replace("postgresql://", "postgresql+psycopg://")
    engine = create_engine(url, pool_size=1)
    try:
        store = PostgresConfigStore(engine)
        assert (await store.load_all())["qa_enabled"] is True
        await store.set_value("qa_enabled", False)
        assert (await store.load_all())["qa_enabled"] is False
        await store.set_value("qa_enabled", True)
        with pytest.raises(LookupError):
            await store.set_value("khong_ton_tai", 1)
    finally:
        await engine.dispose()


async def test_trace_context_is_persisted_for_worker(
    factory: PgUnitOfWorkFactory, migrated: Any, dsn_for: Any
) -> None:
    user = await new_user(factory)
    doc = make_doc(user.id)
    async with factory.for_user(user.id) as uow:
        await uow.documents.add(doc)
        await uow.jobs.enqueue(
            doc.id, {"traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"}
        )
    with psycopg.connect(dsn_for(migrated, "docchat_worker")) as conn:
        row = conn.execute(
            "SELECT trace_context FROM ingest_jobs WHERE document_id=%s", (doc.id,)
        ).fetchone()
    assert row is not None and json.loads(json.dumps(row[0]))["traceparent"].startswith("00-0af7")
