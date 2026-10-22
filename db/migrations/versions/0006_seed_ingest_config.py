"""Cấu hình mặc định cho pipeline ingest

Revision ID: 0006
Revises: 0005
"""

import sys
from pathlib import Path

from alembic import op

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runner import run_sql_file  # noqa: E402

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file(op, "V006__seed_ingest_config.sql")


def downgrade() -> None:
    # Chỉ dev/test; production là forward-only (Database_Design_SQL mục 11).
    run_sql_file(op, "V006.down.sql")
