"""Đăng nhập GIẢ cho phát triển cục bộ — chỉ được gắn khi environment=dev và auth_provider=dev.

Cơ chế đăng nhập thật chưa chốt [TBD: OQ-014]. Endpoint này phát JWT HS256 bằng `JWT_SECRET` cho tên
bất kỳ để chạy thử giao diện (kể cả vai trò evaluator/ops để xem báo cáo, bật kill switch). Nó KHÔNG
bao giờ tồn tại ở staging/production: `create_app` không đăng ký router này ở đó.
"""

from __future__ import annotations

import re
import time

import jwt
from fastapi import APIRouter, Depends

from docchat_api.container import Container
from docchat_api.deps import container
from docchat_api.schemas import DevLoginIn, DevLoginOut
from docchat_core.domain import UserRole
from docchat_core.domain.errors import ValidationFailed

router = APIRouter(tags=["dev"])

TOKEN_TTL_SECONDS = 8 * 3600
_NAME = re.compile(r"^[\w.\- ]{1,40}$", re.UNICODE)


@router.post("/dev/login", response_model=DevLoginOut)
async def dev_login(body: DevLoginIn, c: Container = Depends(container)) -> DevLoginOut:
    name = body.name.strip()
    if not _NAME.match(name):
        raise ValidationFailed("Tên chỉ gồm chữ, số, khoảng trắng, dấu chấm, gạch.")
    allowed = {r.value for r in UserRole}
    roles = [r for r in dict.fromkeys(body.roles) if r in allowed] or ["user"]
    subject = f"dev|{name.lower()}"
    token = jwt.encode(
        {"sub": subject, "roles": roles, "exp": int(time.time()) + TOKEN_TTL_SECONDS},
        c.settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    return DevLoginOut(
        access_token=token, expires_in=TOKEN_TTL_SECONDS, subject=subject, roles=roles
    )
