"""Hàm báo cáo MVP và mục tiêu đo lường

Revision ID: 0008
Revises: 0007
"""

import sys
from pathlib import Path

from alembic import op

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runner import run_sql_file  # noqa: E402

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file(op, "V008__mvp_report.sql")


def downgrade() -> None:
    # Chỉ dev/test; production là forward-only (Database_Design_SQL mục 11).
    run_sql_file(op, "V008.down.sql")
