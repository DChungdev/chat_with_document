"""Fixture tích hợp: Postgres + pgvector thật trong container (cần Docker, `-m integration`)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "docchat_dev"


def _dsn(container, user: str, password: str = PASSWORD) -> str:  # type: ignore[no-untyped-def]
    host = container.get_container_host_ip()
    port = container.get_exposed_port(5432)
    return f"postgresql://{user}:{password}@{host}:{port}/docchat"


@pytest.fixture(scope="session")
def pg() -> Iterator[object]:
    testcontainers = pytest.importorskip("testcontainers.postgres")
    try:
        container = testcontainers.PostgresContainer(
            "pgvector/pgvector:pg16", username="postgres", password="postgres", dbname="docchat"
        )
        container.start()
    except Exception as exc:  # Docker không có / không chạy
        pytest.skip(f"Docker không khả dụng: {exc}")
    try:
        with psycopg.connect(_dsn(container, "postgres", "postgres"), autocommit=True) as conn:
            conn.execute((ROOT / "db/init/01-roles.sql").read_text(encoding="utf-8"))
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="session")
def migrated(pg) -> object:  # type: ignore[no-untyped-def]
    url = _dsn(pg, "migrator").replace("postgresql://", "postgresql+psycopg://")
    os.environ["MIGRATOR_DATABASE_URL"] = url
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "db/migrations"))
    command.upgrade(cfg, "head")
    with psycopg.connect(_dsn(pg, "postgres", "postgres"), autocommit=True) as conn:
        conn.execute((ROOT / "db/seed/dev_users.sql").read_text(encoding="utf-8"))
    return pg


@pytest.fixture()
def alembic_cfg() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "db/migrations"))
    return cfg


@pytest.fixture()
def connect_as() -> object:
    """Trả hàm mở kết nối dưới một vai trò: connect_as(container, "docchat_api")."""

    def _open(container, user: str) -> psycopg.Connection:  # type: ignore[no-untyped-def]
        return psycopg.connect(_dsn(container, user), autocommit=False)

    return _open


@pytest.fixture()
def dsn_for() -> object:
    return _dsn
