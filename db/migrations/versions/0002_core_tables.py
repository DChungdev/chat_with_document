"""Bảng lõi, chunks + HNSW, telemetry, audit

Revision ID: 0002
Revises: 0001
"""

import sys
from pathlib import Path

from alembic import op

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runner import run_sql_file  # noqa: E402

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file(op, "V002__core_tables.sql")


def downgrade() -> None:
    # Chỉ dev/test; production là forward-only (Database_Design_SQL mục 11).
    run_sql_file(op, "V002.down.sql")
