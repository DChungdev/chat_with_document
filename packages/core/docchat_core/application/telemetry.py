"""Nhận sự kiện đo lường theo allow-list (PRD 5.2, ADR-10). Không bao giờ lưu nội dung."""

from __future__ import annotations

import logging
import math
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from docchat_core.domain import TelemetryEvent
from docchat_core.ports import UnitOfWorkFactory

logger = logging.getLogger(__name__)

MAX_BATCH = 50
MAX_STRING_PROP = 64
_SAFE_STRING = re.compile(r"^[\w.\-:]+$")  # định danh/mã lỗi/phiên bản, không phải văn bản tự do
_ALLOWLIST_TTL = 300.0
# Tên thuộc tính gợi ý nội dung người dùng: sự kiện bị TỪ CHỐI cả khối (không chỉ bỏ thuộc tính).
CONTENT_LIKE_KEYS = frozenset(
    {
        "question",
        "answer",
        "text",
        "snippet",
        "content",
        "message",
        "prompt",
        "response",
        "file_name",
        "filename",
        "document_name",
    }
)


def to_snake(key: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()


@dataclass(frozen=True)
class RawEvent:
    name: str
    ts: datetime
    session_id: UUID
    app_version: str
    props: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IngestResult:
    accepted: int
    rejected: int
    dropped_props: int


@dataclass(frozen=True)
class Checked:
    valid: list[TelemetryEvent]
    result: IngestResult


class TelemetryService:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        hasher: Callable[[UUID], str],
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._uow = uow_factory
        self._hash = hasher  # băm một chiều có muối của user_id (client không bao giờ gửi user_id)
        self._monotonic = monotonic
        self._allow: dict[str, frozenset[str]] | None = None
        self._allow_at = 0.0

    async def _allowlist(self, user_id: UUID) -> dict[str, frozenset[str]]:
        now = self._monotonic()
        if self._allow is None or now - self._allow_at > _ALLOWLIST_TTL:
            async with self._uow.for_user(user_id) as uow:
                self._allow = await uow.telemetry.allowlist()
            self._allow_at = now
        return self._allow

    def validate(
        self, events: Sequence[RawEvent], allow: dict[str, frozenset[str]], user_hash: str
    ) -> tuple[list[TelemetryEvent], int, int]:
        """Trả (hợp lệ, số bị từ chối, số thuộc tính bị loại)."""
        valid: list[TelemetryEvent] = []
        rejected = dropped = 0
        for ev in events:
            allowed_props = allow.get(ev.name)
            snake = {to_snake(k): v for k, v in ev.props.items()}
            if (
                allowed_props is None
                or len(ev.app_version) > 32
                or any(k in CONTENT_LIKE_KEYS for k in snake)
            ):
                rejected += 1
                continue
            props: dict[str, object] = {}
            for key, value in snake.items():
                if key in allowed_props and _safe_value(value):
                    props[key] = value
                else:
                    dropped += 1
            valid.append(
                TelemetryEvent(ev.ts, ev.name, user_hash, ev.session_id, ev.app_version, props)
            )
        return valid, rejected, dropped

    async def check(self, user_id: UUID, events: Sequence[RawEvent]) -> Checked:
        """Lọc theo allow-list (đồng bộ, rẻ). Việc ghi có thể chạy nền qua `store`."""
        allow = await self._allowlist(user_id)
        valid, rejected, dropped = self.validate(events, allow, self._hash(user_id))
        return Checked(valid, IngestResult(len(valid), rejected, dropped))

    async def store(self, user_id: UUID, events: Sequence[TelemetryEvent]) -> None:
        if events:
            async with self._uow.for_user(user_id) as uow:
                await uow.telemetry.add_many(events)

    async def ingest(self, user_id: UUID, events: Sequence[RawEvent]) -> IngestResult:
        checked = await self.check(user_id, events)
        await self.store(user_id, checked.valid)
        return checked.result


def _safe_value(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, str):
        return len(value) <= MAX_STRING_PROP and bool(_SAFE_STRING.match(value))
    return False
