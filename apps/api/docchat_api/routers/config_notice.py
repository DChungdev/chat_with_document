from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from docchat_api.container import Container
from docchat_api.deps import CurrentUser, container, current_user
from docchat_api.schemas import AcceptIn, AppConfigOut, DataNoticeOut
from docchat_core.domain.errors import NotFound

router = APIRouter(tags=["config"])


@router.get("/config", response_model=AppConfigOut)
async def get_config(
    user: CurrentUser = Depends(current_user), c: Container = Depends(container)
) -> AppConfigOut:
    """Giới hạn và cờ cho UI — đọc từ app_config, không hard-code (OQ-008)."""
    status = await c.compliance.status(user.id)
    cfg = c.config
    return AppConfigOut(
        qa_enabled=await cfg.qa_enabled(),
        max_file_size_bytes=await cfg.max_file_size_bytes(),
        max_files=await cfg.max_files_per_user(),
        max_question_length=await cfg.max_question_length(),
        max_documents_per_question=await cfg.max_documents_per_question(),
        accepted_types=list(await cfg.get("accepted_types")),
        notice_version=status.notice.version if status else None,
        notice_accepted=status.accepted if status else False,
    )


@router.get("/data-notice", response_model=DataNoticeOut)
async def get_notice(
    user: CurrentUser = Depends(current_user), c: Container = Depends(container)
) -> DataNoticeOut:
    status = await c.compliance.status(user.id)
    if status is None:
        raise NotFound("Chưa có thông báo dữ liệu.")
    return DataNoticeOut(
        version=status.notice.version, content=status.notice.content, accepted=status.accepted
    )


@router.post("/data-notice/acceptances", status_code=201)
async def accept_notice(
    body: AcceptIn, user: CurrentUser = Depends(current_user), c: Container = Depends(container)
) -> Response:
    await c.compliance.accept(user.id, body.version)
    return Response(status_code=201)
