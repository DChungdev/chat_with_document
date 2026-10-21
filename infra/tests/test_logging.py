import io
import json
import logging

from docchat_infra.observability import hash_user_id, log_safe
from docchat_infra.observability.logging import REDACTED, AllowListJsonFormatter


def _logger() -> tuple[logging.Logger, io.StringIO]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(AllowListJsonFormatter("test"))
    logger = logging.getLogger("t." + str(id(stream)))
    logger.handlers[:] = [handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger, stream


def test_question_field_is_redacted() -> None:
    logger, stream = _logger()
    logger.info("request", extra={"question": "Điều khoản phạt là gì?", "route": "/x"})
    line = json.loads(stream.getvalue())
    assert line["question"] == REDACTED
    assert line["route"] == "/x"
    assert "Điều khoản" not in stream.getvalue()


def test_all_content_like_fields_are_redacted() -> None:
    logger, stream = _logger()
    logger.info(
        "x",
        extra={
            "snippet": "CANARY-S",
            "file_name": "hop-dong.pdf",
            "text": "CANARY-T",
            "body": "CANARY-B",
        },
    )
    out = stream.getvalue()
    for secret in ("CANARY-S", "hop-dong.pdf", "CANARY-T", "CANARY-B"):
        assert secret not in out


def test_exception_message_not_logged_only_type_and_frames() -> None:
    logger, stream = _logger()
    try:
        raise ValueError("nội dung nhạy cảm trong thông điệp lỗi")
    except ValueError:
        logger.exception("failed")
    line = json.loads(stream.getvalue())
    assert line["exc_type"] == "ValueError"
    assert "nhạy cảm" not in stream.getvalue()
    assert line["stack"] and "test_logging.py" in line["stack"][0]


def test_log_safe_drops_unknown_fields_and_warns() -> None:
    logger, stream = _logger()
    log_safe(logger, logging.INFO, "doc_ready", stage="write", question="bí mật")
    out = stream.getvalue()
    assert "bí mật" not in out
    assert '"stage": "write"' in out
    assert "log_safe dropped fields" in out


def test_user_hash_is_stable_salted_and_64_hex() -> None:
    h1 = hash_user_id("u1", "salt-a")
    assert h1 == hash_user_id("u1", "salt-a")
    assert h1 != hash_user_id("u1", "salt-b")
    assert len(h1) == 64 and int(h1, 16) >= 0
    assert "u1" not in h1
