"""Log JSON có cấu trúc với allow-list trường (PRD 5.2, SAD DC-06).

Quy tắc: KHÔNG bao giờ log `question`, `snippet`, nội dung PDF, tên tệp. Trường ngoài allow-list
bị thay giá trị bằng "[redacted]" (giữ tên trường để dễ phát hiện lỗi lập trình).
Thông điệp (`message`) do lập trình viên viết cố định; không nội suy dữ liệu người dùng vào đó.
"""

from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import UTC, datetime
from typing import Any

REDACTED = "[redacted]"

ALLOWED_FIELDS: frozenset[str] = frozenset(
    {
        "ts",
        "level",
        "logger",
        "message",
        "trace_id",
        "span_id",
        "request_id",
        "route",
        "method",
        "status",
        "duration_ms",
        "user_hash",
        "stage",
        "error_code",
        "exc_type",
        "stack",
        "config_key",
        "event",
        "service",
        "job_id",
        "document_id",
        "attempt",
        "count",
    }
)

# Thuộc tính có sẵn của LogRecord — không phải trường do người dùng thêm qua `extra`.
_STD_ATTRS = frozenset(
    set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime", "taskName"}
)


def _stack(exc: BaseException) -> list[str]:
    """Chỉ file:dòng:hàm — không có giá trị biến hay thông điệp ngoại lệ (có thể chứa nội dung)."""
    return [f"{f.filename}:{f.lineno}:{f.name}" for f in traceback.extract_tb(exc.__traceback__)]


class AllowListJsonFormatter(logging.Formatter):
    def __init__(self, service: str = "docchat") -> None:
        super().__init__()
        self._service = service

    def format(self, record: logging.LogRecord) -> str:
        out: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self._service,
        }
        for key, value in record.__dict__.items():
            if key in _STD_ATTRS or key in out:
                continue
            out[key] = value if key in ALLOWED_FIELDS else REDACTED
        if record.exc_info and record.exc_info[1] is not None:
            out["exc_type"] = type(record.exc_info[1]).__name__
            out["stack"] = _stack(record.exc_info[1])
        return json.dumps(out, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO", service: str = "docchat") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(AllowListJsonFormatter(service))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    # Log truy cập mặc định của uvicorn chứa đường dẫn đầy đủ — thay bằng log của middleware.
    logging.getLogger("uvicorn.access").disabled = True


def log_safe(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Ghi log chỉ với các trường trong allow-list; trường lạ bị loại và báo bằng cảnh báo."""
    safe = {k: v for k, v in fields.items() if k in ALLOWED_FIELDS}
    dropped = set(fields) - set(safe)
    logger.log(level, event, extra={"event": event, **safe})
    if dropped:
        logger.warning("log_safe dropped fields", extra={"count": len(dropped)})
