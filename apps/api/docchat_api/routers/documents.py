from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, Query, Response, UploadFile

from docchat_api.container import Container
from docchat_api.deps import CurrentUser, container, current_user
from docchat_api.schemas import DocumentOut, DocumentPage
from docchat_core.domain.errors import ValidationFailed

router = APIRouter(tags=["documents"])


def _idempotency_key(raw: str | None) -> UUID:
    try:
        return UUID(raw or "")
    except ValueError:
        raise ValidationFailed("Thiếu hoặc sai header Idempotency-Key (cần UUID).") from None


@router.post("/documents", status_code=202, response_model=DocumentOut)
async def upload_document(
    response: Response,
    file: UploadFile = File(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: CurrentUser = Depends(current_user),
    c: Container = Depends(container),
) -> DocumentOut:
    """Một tệp mỗi yêu cầu để lỗi một tệp không ảnh hưởng tệp khác (API-03). Trả 202 ngay."""
    doc = await c.documents.upload(
        user.id,
        filename=file.filename,
        content_type=file.content_type,
        content=file.file,
        idempotency_key=_idempotency_key(idempotency_key),
    )
    response.headers["Location"] = f"/api/v1/documents/{doc.id}"
    return DocumentOut.of(doc)


@router.get("/documents", response_model=DocumentPage)
async def list_documents(
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=256),
    user: CurrentUser = Depends(current_user),
    c: Container = Depends(container),
) -> DocumentPage:
    try:
        items, nxt = await c.documents.list(user.id, limit, cursor)
    except (ValueError, UnicodeError):
        raise ValidationFailed("Cursor không hợp lệ.") from None
    return DocumentPage(items=[DocumentOut.of(d) for d in items], next_cursor=nxt)


@router.get("/documents/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: UUID, user: CurrentUser = Depends(current_user), c: Container = Depends(container)
) -> DocumentOut:
    return DocumentOut.of(await c.documents.get(user.id, document_id))


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID, user: CurrentUser = Depends(current_user), c: Container = Depends(container)
) -> Response:
    await c.documents.delete(user.id, document_id)
    return Response(status_code=204)
