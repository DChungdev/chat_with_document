from __future__ import annotations

import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse

from docchat_api.container import Container
from docchat_api.deps import CurrentUser, container, current_user
from docchat_api.schemas import AskIn, ConversationOut
from docchat_core.domain.errors import ValidationFailed

router = APIRouter(tags=["conversations"])


def _sse(name: str, data: dict[str, object]) -> str:
    return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/conversations", status_code=201, response_model=ConversationOut)
async def create_conversation(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: CurrentUser = Depends(current_user),
    c: Container = Depends(container),
) -> ConversationOut:
    key = None
    if idempotency_key:
        try:
            key = UUID(idempotency_key)
        except ValueError:
            raise ValidationFailed("Idempotency-Key phải là UUID.") from None
    return ConversationOut.of(await c.chat.create_conversation(user.id, key))


@router.post("/conversations/{conversation_id}/messages")
async def ask(
    conversation_id: UUID,
    body: AskIn,
    user: CurrentUser = Depends(current_user),
    c: Container = Depends(container),
) -> StreamingResponse:
    """Hỏi đáp qua SSE. Mọi lỗi kiểm tra xảy ra TRƯỚC khi mở stream ⇒ trả problem+json."""
    ctx = await c.chat.prepare(
        user.id,
        conversation_id,
        question=body.question,
        document_ids=body.document_ids,
        client_message_id=body.client_message_id,
    )

    async def events() -> AsyncIterator[str]:
        async for ev in c.chat.stream(ctx):
            yield _sse(ev.name, ev.data)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
