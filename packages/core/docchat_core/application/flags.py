"""Kill switch hỏi đáp (PRD 5.1): đổi `qa_enabled` không cần deploy."""

from __future__ import annotations

import logging

from docchat_core.config import AppConfig
from docchat_core.domain import UserRole
from docchat_core.domain.errors import Forbidden
from docchat_core.ports import ConfigWriter, Principal

logger = logging.getLogger(__name__)


class FlagService:
    def __init__(self, writer: ConfigWriter, config: AppConfig) -> None:
        self._writer = writer
        self._config = config

    async def set_qa_enabled(self, principal: Principal, enabled: bool) -> None:
        if UserRole.OPS not in principal.roles:
            raise Forbidden()
        await self._writer.set_value("qa_enabled", enabled)
        self._config.invalidate()  # replica này thấy ngay; replica khác sau ≤ TTL
        logger.warning("qa_enabled changed", extra={"event": "qa_enabled_changed"})
