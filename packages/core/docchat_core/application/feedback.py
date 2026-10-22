"""Đánh giá câu trả lời hữu ích / không hữu ích (US-502, IF-09)."""

from __future__ import annotations

import re
from uuid import UUID

from docchat_core.domain import MessageRole
from docchat_core.domain.errors import NotFound, ValidationFailed
from docchat_core.ports import UnitOfWorkFactory

RATINGS = frozenset({"up", "down"})
_REASON = re.compile(r"^[a-z][a-z0-9_]{0,31}$")  # mã lý do, không phải văn bản tự do


class FeedbackService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow = uow_factory

    async def rate(
        self, user_id: UUID, message_id: UUID, rating: str, reason_code: str | None = None
    ) -> None:
        """Chỉ nhận mã (up|down + reason_code) — không bao giờ nhận hay lưu nội dung (PRD 5.2)."""
        if rating not in RATINGS:
            raise ValidationFailed("rating phải là 'up' hoặc 'down'.")
        if reason_code is not None and not _REASON.match(reason_code):
            raise ValidationFailed("reasonCode không hợp lệ.")
        async with self._uow.for_user(user_id) as uow:
            msg = await uow.messages.get(message_id)
            if msg is None or msg.role is not MessageRole.AI:
                raise NotFound()
            await uow.feedback.upsert(message_id, rating, reason_code if rating == "down" else None)
