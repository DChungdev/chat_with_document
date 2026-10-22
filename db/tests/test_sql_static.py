"""Kiểm tĩnh các tệp migration — chạy không cần Docker."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "migrations"))
import runner  # noqa: E402

pglast = pytest.importorskip("pglast")

SQL_FILES = sorted(p.name for p in runner.SQL_DIR.glob("V*.sql"))


def test_all_expected_files_exist() -> None:
    for i in range(1, 9):
        assert any(n.startswith(f"V00{i}__") for n in SQL_FILES)
        assert f"V00{i}.down.sql" in SQL_FILES


@pytest.mark.parametrize("name", SQL_FILES)
def test_sql_parses(name: str) -> None:
    rendered = runner.read_sql(name)
    assert "{{" not in rendered, "còn biến mẫu chưa thay"
    pglast.parse_sql(rendered)


def test_embedding_dim_is_parameterised(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_DIM", "768")
    assert "vector(768)" in runner.read_sql("V002__core_tables.sql")
    assert "vector(768)" in runner.read_sql("V004__views_functions_triggers.sql")
    assert "vector(1024)" not in runner.read_sql("V002__core_tables.sql")


def test_template_rejects_non_numeric(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_DIM", "1024); DROP TABLE users;--")
    with pytest.raises(ValueError):
        runner.template_values()


def test_rls_enabled_for_every_user_scoped_table() -> None:
    sql = runner.read_sql("V003__rls_roles.sql")
    tables = re.search(r"ARRAY\[([^\]]+)\]", sql)
    assert tables
    names = set(re.findall(r"'(\w+)'", tables.group(1)))
    # Mọi bảng có cột user_id và chứa dữ liệu người dùng phải nằm trong danh sách RLS.
    assert {"documents", "chunks", "conversations", "messages", "citations"} <= names
    assert "FORCE ROW LEVEL SECURITY" in sql
