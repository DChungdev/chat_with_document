from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

Clock = Callable[[], datetime]
IdFactory = Callable[[], UUID]


def utc_now() -> datetime:
    return datetime.now(UTC)


new_id: IdFactory = uuid4


class ChatMetrics(Protocol):
    """Cổng đo lường để lõi không phụ thuộc prometheus_client."""

    def first_token(self, seconds: float) -> None: ...
    def answer_finished(self, grounded: bool) -> None: ...
    def stage_error(self, stage: str) -> None: ...


class NoMetrics:
    def first_token(self, seconds: float) -> None:
        pass

    def answer_finished(self, grounded: bool) -> None:
        pass

    def stage_error(self, stage: str) -> None:
        pass
