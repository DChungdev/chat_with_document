"""Cấu hình mặc định cho retrieval / trả lời

Revision ID: 0007
Revises: 0006
"""

import sys
from pathlib import Path

from alembic import op

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runner import run_sql_file  # noqa: E402

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file(op, "V007__seed_retrieval_config.sql")


def downgrade() -> None:
    # Chỉ dev/test; production là forward-only (Database_Design_SQL mục 11).
    run_sql_file(op, "V007.down.sql")
