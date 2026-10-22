from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Response

from docchat_api.container import Container
from docchat_api.deps import CurrentUser, container, current_user
from docchat_api.schemas import CitationOut, FlagIn, TelemetryIn, TelemetryOut
from docchat_core.application.telemetry import RawEvent

logger = logging.getLogger("docchat.api")

router = APIRouter()


@router.get("/citations/{citation_id}", response_model=CitationOut, tags=["citations"])
async def get_citation(
    citation_id: UUID, user: CurrentUser = Depends(current_user), c: Container = Depends(container)
) -> CitationOut:
    return CitationOut.of(await c.citations.get(user.id, citation_id))


@router.post("/telemetry/events", status_code=202, response_model=TelemetryOut, tags=["telemetry"])
async def post_telemetry(
    body: TelemetryIn,
    background: BackgroundTasks,
    user: CurrentUser = Depends(current_user),
    c: Container = Depends(container),
) -> TelemetryOut:
    """Lọc allow-list đồng bộ; ghi nền để telemetry không làm chậm hay làm hỏng thao tác chính."""
    raw = [RawEvent(e.name, e.ts, e.session_id, e.app_version, e.props) for e in body.events]
    checked = await c.telemetry.check(user.id, raw)

    async def persist() -> None:
        try:
            await c.telemetry.store(user.id, checked.valid)
        except Exception:
            logger.warning("telemetry persist failed", extra={"event": "telemetry_failed"})

    background.add_task(persist)
    return TelemetryOut(accepted=checked.result.accepted, rejected=checked.result.rejected)


@router.put("/admin/flags/qa-enabled", status_code=204, tags=["admin"])
async def set_qa_enabled(
    body: FlagIn, user: CurrentUser = Depends(current_user), c: Container = Depends(container)
) -> Response:
    """Kill switch (vai trò `ops`)."""
    await c.flags.set_qa_enabled(user.principal, body.enabled)
    return Response(status_code=204)
