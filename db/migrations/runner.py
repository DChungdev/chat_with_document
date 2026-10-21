"""Chạy các tệp SQL của migration, thay biến mẫu `{{NAME}}` bằng cấu hình.

SQL là nguồn sự thật (docs/design/Database_Design_SQL.md); Alembic chỉ chạy và theo dõi phiên bản.
Production là forward-only (SQL design mục 11): các tệp `*.down.sql` chỉ dành cho dev/test.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

SQL_DIR = Path(__file__).parent / "sql"

# Giá trị mặc định; ghi đè bằng biến môi trường cùng tên.
# EMBEDDING_DIM phụ thuộc mô hình embedding đã chọn [TBD: OQ-008, OQ-012].
_DEFAULTS = {"EMBEDDING_DIM": "1024", "HNSW_M": "16", "HNSW_EF_CONSTRUCTION": "64"}

_PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")


def template_values() -> dict[str, str]:
    values = {k: os.environ.get(k, v) for k, v in _DEFAULTS.items()}
    for key, value in values.items():
        if (
            not value.isdigit() or int(value) <= 0
        ):  # chỉ chấp nhận số nguyên dương, tránh SQL injection
            raise ValueError(f"{key} phải là số nguyên dương, nhận được {value!r}")
    return values


def render(sql: str, values: dict[str, str] | None = None) -> str:
    values = values or template_values()

    def sub(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in values:
            raise KeyError(f"biến mẫu chưa định nghĩa: {name}")
        return values[name]

    return _PLACEHOLDER.sub(sub, sql)


def read_sql(name: str) -> str:
    return render((SQL_DIR / name).read_text(encoding="utf-8"))


def run_sql_file(op: Any, name: str) -> None:
    """Chạy nguyên tệp trên kết nối psycopg gốc.

    Không dùng `op.execute`/`exec_driver_sql`: SQL chứa `%I`, `%1$s` (hàm format) và `:=` mà lớp
    SQLAlchemy/psycopg có thể hiểu nhầm là tham số. Gọi `execute` không tham số dùng giao thức
    truy vấn đơn giản, cho phép nhiều câu lệnh trong một lần.
    """
    raw = op.get_bind().connection.driver_connection
    raw.execute(read_sql(name))
