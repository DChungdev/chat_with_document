"""View, hàm, trigger

Revision ID: 0004
Revises: 0003
"""

import sys
from pathlib import Path

from alembic import op

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runner import run_sql_file  # noqa: E402

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    run_sql_file(op, "V004__views_functions_triggers.sql")


def downgrade() -> None:
    # Chỉ dev/test; production là forward-only (Database_Design_SQL mục 11).
    run_sql_file(op, "V004.down.sql")
