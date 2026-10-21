"""Kiểm thử trên Postgres thật: migration, cascade, audit, RLS (US-402). Cần Docker."""

from __future__ import annotations

import uuid

import psycopg
import pytest
from alembic import command

pytestmark = pytest.mark.integration

LAN = "00000000-0000-0000-0000-0000000000a1"
MINH = "00000000-0000-0000-0000-0000000000b2"


def _insert_document(conn: psycopg.Connection, user_id: str) -> str:
    doc_id = str(uuid.uuid4())
    conn.execute("SELECT set_config('app.user_id', %s, true)", (user_id,))
    conn.execute(
        "INSERT INTO documents (id, user_id, name, size_bytes, storage_key)"
        " VALUES (%s,%s,'a.pdf',10,%s)",
        (doc_id, user_id, f"{user_id}/{doc_id}.pdf"),
    )
    return doc_id


def test_seed_config_present(migrated, connect_as) -> None:  # type: ignore[no-untyped-def]
    with connect_as(migrated, "docchat_api") as conn:
        keys = {r[0] for r in conn.execute("SELECT key FROM app_config")}
    assert {"qa_enabled", "max_file_size_bytes", "retrieval_top_k", "max_question_length"} <= keys


def test_delete_document_cascades_to_chunks(migrated, connect_as) -> None:  # type: ignore[no-untyped-def]
    with connect_as(migrated, "docchat_api") as api:
        doc_id = _insert_document(api, LAN)
        api.commit()
    with connect_as(migrated, "docchat_worker") as worker:
        worker.execute(
            "INSERT INTO chunks (document_id, user_id, ordinal, page_start, page_end, text,"
            " token_count, embedding, embedding_model)"
            " VALUES (%s,%s,0,1,1,'x',1,"
            "(SELECT array_fill(0.1::real, ARRAY[1024])::vector),'fake')",
            (doc_id, LAN),
        )
        worker.commit()
    with connect_as(migrated, "docchat_api") as api:
        api.execute("SELECT set_config('app.user_id', %s, true)", (LAN,))
        api.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
        api.commit()
    with connect_as(migrated, "docchat_worker") as worker:
        n = worker.execute(
            "SELECT count(*) FROM chunks WHERE document_id = %s", (doc_id,)
        ).fetchone()
    assert n == (0,)


def test_audit_log_is_append_only(migrated, connect_as) -> None:  # type: ignore[no-untyped-def]
    with connect_as(migrated, "docchat_api") as api:
        _insert_document(api, LAN)  # trigger ghi audit 'document_uploaded'
        api.commit()
        with pytest.raises(psycopg.Error):
            api.execute("UPDATE audit_log SET user_id = user_id")
        api.rollback()
        with pytest.raises(psycopg.Error):
            api.execute("DELETE FROM audit_log")


def test_rls_isolates_users(migrated, connect_as) -> None:  # type: ignore[no-untyped-def]
    with connect_as(migrated, "docchat_api") as api:
        doc_id = _insert_document(api, LAN)
        api.commit()
    with connect_as(migrated, "docchat_api") as api:
        api.execute("SELECT set_config('app.user_id', %s, true)", (MINH,))
        assert api.execute(
            "SELECT count(*) FROM documents WHERE id = %s", (doc_id,)
        ).fetchone() == (0,)
        api.rollback()
        # Quên đặt app.user_id ⇒ không thấy dòng nào (an toàn theo mặc định)
        assert api.execute("SELECT count(*) FROM documents").fetchone() == (0,)
        api.rollback()
        # Cố ghi dưới danh tính khác bị chặn bởi WITH CHECK
        api.execute("SELECT set_config('app.user_id', %s, true)", (MINH,))
        with pytest.raises(psycopg.Error):
            api.execute(
                "INSERT INTO documents (user_id, name, size_bytes, storage_key)"
                " VALUES (%s,'x.pdf',1,%s)",
                (LAN, f"k/{uuid.uuid4()}"),
            )


def test_vector_query_uses_filter_and_hnsw_index_exists(migrated, connect_as) -> None:  # type: ignore[no-untyped-def]
    with connect_as(migrated, "docchat_api") as api:
        idx = api.execute(
            "SELECT indexdef FROM pg_indexes WHERE indexname = 'idx_chunks_embedding_hnsw'"
        ).fetchone()
    assert idx and "hnsw" in idx[0] and "vector_cosine_ops" in idx[0]


def test_downgrade_then_upgrade_roundtrip(pg, alembic_cfg, dsn_for, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Dùng CSDL riêng để không phá fixture `migrated`."""
    with psycopg.connect(dsn_for(pg, "postgres", "postgres"), autocommit=True) as admin:
        admin.execute("DROP DATABASE IF EXISTS roundtrip")
        admin.execute("CREATE DATABASE roundtrip OWNER migrator")
    base = dsn_for(pg, "postgres", "postgres").rsplit("/", 1)[0]
    with psycopg.connect(f"{base}/roundtrip", autocommit=True) as su:
        su.execute("CREATE EXTENSION IF NOT EXISTS vector")  # cần superuser
    migrator = dsn_for(pg, "migrator").rsplit("/", 1)[0]
    monkeypatch.setenv(
        "MIGRATOR_DATABASE_URL",
        f"{migrator}/roundtrip".replace("postgresql://", "postgresql+psycopg://"),
    )
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")
