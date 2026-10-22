from datetime import UTC, datetime
from uuid import uuid4

import pytest

from docchat_core.domain import (
    Chunk,
    Citation,
    Document,
    DocumentStatus,
    Message,
    MessageStatus,
)
from docchat_core.domain.errors import InvalidTransition

NOW = datetime(2026, 10, 22, tzinfo=UTC)


def doc() -> Document:
    return Document(uuid4(), uuid4(), "a.pdf", 10, "k", NOW)


def ai() -> Message:
    m = Message.new_ai(uuid4(), uuid4(), uuid4(), uuid4(), NOW)
    m.start_streaming()
    return m


# ---- Document ----
def test_document_starts_processing() -> None:
    assert doc().status is DocumentStatus.PROCESSING


def test_mark_ready_sets_pages_and_time() -> None:
    d = doc()
    d.mark_ready(7, NOW)
    assert (d.status, d.page_count, d.processed_at) == (DocumentStatus.READY, 7, NOW)


def test_mark_error_requires_code() -> None:
    d = doc()
    with pytest.raises(InvalidTransition):
        d.mark_error("", NOW)
    d.mark_error("PDF_CORRUPT", NOW)
    assert d.status is DocumentStatus.ERROR and d.error_code == "PDF_CORRUPT"


@pytest.mark.parametrize("first", ["ready", "error"])
def test_document_terminal_states_do_not_change(first: str) -> None:
    d = doc()
    d.mark_ready(1, NOW) if first == "ready" else d.mark_error("X", NOW)
    with pytest.raises(InvalidTransition):
        d.mark_ready(1, NOW)
    with pytest.raises(InvalidTransition):
        d.mark_error("Y", NOW)


def test_ready_needs_positive_pages() -> None:
    with pytest.raises(InvalidTransition):
        doc().mark_ready(0, NOW)


# ---- Message ----
def test_user_message_is_complete_immediately() -> None:
    m = Message.new_user(uuid4(), uuid4(), uuid4(), "hỏi?", NOW)
    assert m.status is MessageStatus.COMPLETE and m.completed_at == NOW


def test_ai_message_lifecycle_complete() -> None:
    m = ai()
    m.append("Xin ")
    m.append("chào")
    m.complete(True, NOW)
    assert (m.status, m.text, m.grounded, m.completed_at) == (
        MessageStatus.COMPLETE, "Xin chào", True, NOW,
    )  # fmt: skip


@pytest.mark.parametrize("action", ["interrupt", "stop"])
def test_ai_message_terminal_via_interrupt_or_stop(action: str) -> None:
    m = ai()
    m.append("dở")
    getattr(m, action)(NOW)
    assert m.text == "dở" and m.completed_at == NOW  # giữ phần đã nhận


def test_fail_records_error_code() -> None:
    m = ai()
    m.fail("LLM_TIMEOUT", NOW)
    assert m.status is MessageStatus.FAILED and m.error_code == "LLM_TIMEOUT"


def test_sending_can_fail_or_start_but_not_complete() -> None:
    m = Message.new_ai(uuid4(), uuid4(), uuid4(), uuid4(), NOW)
    with pytest.raises(InvalidTransition):
        m.complete(True, NOW)
    m.fail("X", NOW)


@pytest.mark.parametrize("terminal", ["complete", "interrupt", "stop", "fail"])
def test_terminal_message_is_final(terminal: str) -> None:
    m = ai()
    {"complete": lambda: m.complete(True, NOW), "interrupt": lambda: m.interrupt(NOW),
     "stop": lambda: m.stop(NOW), "fail": lambda: m.fail("X", NOW)}[terminal]()  # fmt: skip
    for again in (lambda: m.complete(True, NOW), lambda: m.interrupt(NOW), lambda: m.append("x")):
        with pytest.raises(InvalidTransition):
            again()


def test_cannot_append_before_streaming() -> None:
    m = Message.new_ai(uuid4(), uuid4(), uuid4(), uuid4(), NOW)
    with pytest.raises(InvalidTransition):
        m.append("x")


# ---- Citation / Chunk ----
def test_citation_validity_follows_chunk_presence() -> None:
    base = dict(id=uuid4(), message_id=uuid4(), user_id=uuid4(), ordinal=1, page=3)
    assert Citation(**base, chunk_id=uuid4()).valid is True  # type: ignore[arg-type]
    assert Citation(**base, chunk_id=None).valid is False  # type: ignore[arg-type]


def test_chunk_page_range_validated() -> None:
    with pytest.raises(ValueError):
        Chunk(uuid4(), uuid4(), uuid4(), 0, 3, 2, "x", 1)
    with pytest.raises(ValueError):
        Chunk(uuid4(), uuid4(), uuid4(), 0, 0, 1, "x", 1)
    assert Chunk(uuid4(), uuid4(), uuid4(), 0, 3, 4, "x", 1).page_end == 4
