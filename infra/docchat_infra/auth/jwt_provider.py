"""Xác thực JWT sau cổng `AuthProvider` (B3). Cơ chế đăng nhập thật chưa chốt [TBD: OQ-014].

- Dev: khóa đối xứng (HS256) dùng chung — chỉ dành cho dev/test.
- OIDC: khóa công khai lấy từ JWKS của IdP (RS256/ES256), cache khóa theo `kid`.

Token KHÔNG bao giờ được ghi vào log; lỗi xác thực chỉ mang mã, không mang nội dung token.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import jwt

from docchat_core.domain import UserRole
from docchat_core.domain.errors import SessionExpired, Unauthenticated
from docchat_core.ports import Principal

LEEWAY_SECONDS = 60  # đồng hồ lệch ±60s


class OidcKeyResolver:
    """Lấy khóa ký từ JWKS (PyJWKClient tự cache theo kid)."""

    def __init__(self, jwks_url: str) -> None:
        self._client = jwt.PyJWKClient(jwks_url, cache_keys=True)

    def __call__(self, token: str) -> Any:
        return self._client.get_signing_key_from_jwt(token).key


class JwtAuthProvider:
    def __init__(
        self,
        *,
        algorithms: list[str],
        key: Any = None,
        key_resolver: Callable[[str], Any] | None = None,
        issuer: str | None = None,
        audience: str | None = None,
    ) -> None:
        if (key is None) == (key_resolver is None):
            raise ValueError("Cần đúng một trong `key` hoặc `key_resolver`.")
        self._algorithms = algorithms
        self._key = key
        self._resolver = key_resolver
        self._issuer = issuer
        self._audience = audience

    async def authenticate(self, token: str) -> Principal:
        try:
            key = self._key if self._resolver is None else self._resolver(token)
            claims = jwt.decode(
                token,
                key,
                algorithms=self._algorithms,
                issuer=self._issuer,
                audience=self._audience,
                leeway=LEEWAY_SECONDS,
                options={
                    "require": ["exp", "sub"],
                    "verify_aud": self._audience is not None,
                    "verify_iss": self._issuer is not None,
                },
            )
        except jwt.ExpiredSignatureError:
            raise SessionExpired() from None
        except (jwt.PyJWTError, ValueError):
            raise Unauthenticated() from None  # chữ ký sai, thiếu claim, sai aud/iss, định dạng hỏng
        subject = claims["sub"]
        if not isinstance(subject, str) or not subject:
            raise Unauthenticated()
        return Principal(subject, _roles(claims.get("roles")))


def _roles(raw: object) -> frozenset[UserRole]:
    """Vai trò lạ bị bỏ qua; luôn có ít nhất `user`."""
    items = raw if isinstance(raw, list) else []
    roles = {UserRole(r) for r in items if r in {v.value for v in UserRole}}
    return frozenset(roles or {UserRole.USER})
