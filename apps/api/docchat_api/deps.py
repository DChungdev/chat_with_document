from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Request

from docchat_api.container import Container
from docchat_core.domain import UserRole
from docchat_core.domain.errors import Unauthenticated
from docchat_core.ports import Principal
from docchat_infra.observability import hash_user_id


def container(request: Request) -> Container:
    c: Container = request.app.state.container
    return c


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    principal: Principal


def _bearer(request: Request) -> str:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise Unauthenticated()
    return token.strip()


async def current_user(request: Request, c: Container = Depends(container)) -> CurrentUser:
    """Xác thực JWT, lấy/tạo người dùng. `user_id` luôn lấy từ token, không bao giờ từ client."""
    principal = await c.auth.authenticate(_bearer(request))
    role = next(
        (r for r in (UserRole.OPS, UserRole.EVALUATOR) if r in principal.roles), UserRole.USER
    )
    async with c.uow_factory.system() as uow:
        user = await uow.users.upsert_by_subject(principal.subject, role)
    request.state.user_hash = hash_user_id(user.id, c.settings.telemetry_salt.get_secret_value())
    return CurrentUser(user.id, principal)
