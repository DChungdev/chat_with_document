from __future__ import annotations

import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).parent))  # để import runner

# Bảng phiên bản ở `public`: V001 (downgrade) xóa cả schema docchat, không được kéo theo nó.
VERSION_SCHEMA = "public"


def _url() -> str:
    # Ưu tiên: -x url=...  >  MIGRATOR_DATABASE_URL  >  mặc định dev
    x = context.get_x_argument(as_dictionary=True)
    return (
        x.get("url")
        or os.environ.get("MIGRATOR_DATABASE_URL")
        or "postgresql+psycopg://migrator:docchat_dev@localhost:5432/docchat"
    )


def run_migrations_online() -> None:
    engine = create_engine(_url(), future=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None,
            version_table_schema=VERSION_SCHEMA,
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("Chế độ offline không được hỗ trợ: SQL cần chạy trên kết nối thật.")
run_migrations_online()
