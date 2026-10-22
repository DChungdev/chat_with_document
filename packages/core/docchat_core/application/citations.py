"""Xem đoạn nguồn của một trích dẫn (US-302)."""

from __future__ import annotations

from uuid import UUID

from docchat_core.config import AppConfig
from docchat_core.domain import CitationView
from docchat_core.domain.errors import NotFound
from docchat_core.ports import UnitOfWorkFactory

_ELLIPSIS = "…"


class CitationService:
    def __init__(self, uow_factory: UnitOfWorkFactory, config: AppConfig) -> None:
        self._uow = uow_factory
        self._config = config

    async def get(self, user_id: UUID, citation_id: UUID) -> CitationView:
        """Tài liệu đã xóa ⇒ view có valid=False, snippet=None (không 404, không để trống — PRD 4.2).

        Citation của người khác ⇒ NotFound (RLS + lọc user_id).
        """
        async with self._uow.for_user(user_id) as uow:
            view = await uow.citations.get_view(citation_id)
        if view is None:
            raise NotFound()
        if view.snippet is None:
            return view
        limit = int(await self._config.get("citation_snippet_max_chars"))
        if len(view.snippet) <= limit:
            return view
        return CitationView(view.citation, view.snippet[: limit - 1].rstrip() + _ELLIPSIS)
