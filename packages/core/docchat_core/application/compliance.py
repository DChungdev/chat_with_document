"""Thông báo sử dụng dữ liệu (US-401): bắt buộc xác nhận trước khi tải tệp."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from docchat_core.domain import DataNotice
from docchat_core.domain.errors import NoticeNotAccepted, NoticeVersionMismatch
from docchat_core.ports import UnitOfWork, UnitOfWorkFactory


@dataclass(frozen=True)
class NoticeStatus:
    notice: DataNotice
    accepted: bool


async def require_notice_accepted(uow: UnitOfWork) -> None:
    """Dùng trong cùng giao dịch với thao tác cần chặn. Thiếu thông báo ⇒ chặn (fail closed)."""
    notice = await uow.notices.current()
    if notice is None or not await uow.notices.has_accepted(notice.version):
        raise NoticeNotAccepted()


class ComplianceService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow = uow_factory

    async def status(self, user_id: UUID) -> NoticeStatus | None:
        async with self._uow.for_user(user_id) as uow:
            notice = await uow.notices.current()
            if notice is None:
                return None
            return NoticeStatus(notice, await uow.notices.has_accepted(notice.version))

    async def accept(self, user_id: UUID, version: str) -> None:
        """Ghi xác nhận. Audit `notice_accepted` do trigger CSDL ghi khi chèn dòng mới."""
        async with self._uow.for_user(user_id) as uow:
            notice = await uow.notices.current()
            if notice is None or notice.version != version:
                raise NoticeVersionMismatch()
            await uow.notices.accept(version)
