from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from docchat_core.domain import UserRole
from docchat_core.domain.errors import RateLimited, SessionExpired, Unauthenticated
from docchat_infra.auth import JwtAuthProvider
from docchat_infra.ratelimit import InMemoryRateLimiter

SECRET = "x" * 48


def tok(key: Any = SECRET, alg: str = "HS256", **claims: Any) -> str:
    base: dict[str, Any] = {"sub": "alice", "exp": datetime.now(UTC) + timedelta(hours=1)}
    base.update(claims)
    base = {k: v for k, v in base.items() if v is not None}
    return jwt.encode(base, key, algorithm=alg)


def hs() -> JwtAuthProvider:
    return JwtAuthProvider(algorithms=["HS256"], key=SECRET)


async def test_valid_token_yields_principal_with_default_role() -> None:
    p = await hs().authenticate(tok())
    assert p.subject == "alice" and p.roles == {UserRole.USER}


async def test_roles_claim_is_mapped_and_unknown_roles_ignored() -> None:
    p = await hs().authenticate(tok(roles=["ops", "superadmin", "evaluator"]))
    assert p.roles == {UserRole.OPS, UserRole.EVALUATOR}


async def test_expired_token_is_session_expired() -> None:
    with pytest.raises(SessionExpired):
        await hs().authenticate(tok(exp=datetime.now(UTC) - timedelta(hours=1)))


async def test_small_clock_skew_is_tolerated() -> None:
    await hs().authenticate(tok(exp=datetime.now(UTC) - timedelta(seconds=30)))


@pytest.mark.parametrize(
    "token",
    [
        "garbage",
        jwt.encode({"sub": "a", "exp": 9999999999}, "y" * 48, algorithm="HS256"),  # sai khóa
        jwt.encode({"sub": "a"}, SECRET, algorithm="HS256"),  # thiếu exp
        jwt.encode({"exp": 9999999999}, SECRET, algorithm="HS256"),  # thiếu sub
        jwt.encode({"sub": "a", "exp": 9999999999}, SECRET, algorithm="HS384"),  # sai thuật toán
        jwt.encode({"sub": "a", "exp": 9999999999}, None, algorithm="none"),  # alg=none
    ],
)
async def test_invalid_tokens_are_unauthenticated(token: str) -> None:
    with pytest.raises(Unauthenticated) as ei:
        await hs().authenticate(token)
    assert not isinstance(ei.value, SessionExpired)
    assert token not in str(ei.value) and token not in ei.value.detail  # không lộ token


async def test_oidc_style_rs256_with_issuer_and_audience() -> None:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    provider = JwtAuthProvider(
        algorithms=["RS256"],
        key_resolver=lambda _t: private.public_key(),
        issuer="https://idp.example",
        audience="docchat",
    )
    good = tok(private, "RS256", iss="https://idp.example", aud="docchat")
    assert (await provider.authenticate(good)).subject == "alice"
    for bad in (
        tok(private, "RS256", iss="https://evil.example", aud="docchat"),  # sai issuer
        tok(private, "RS256", iss="https://idp.example", aud="other"),  # sai audience
        tok(other, "RS256", iss="https://idp.example", aud="docchat"),  # sai khóa ký
        tok(private, "RS256", iss="https://idp.example"),  # thiếu audience
    ):
        with pytest.raises(Unauthenticated):
            await provider.authenticate(bad)


def test_provider_needs_exactly_one_key_source() -> None:
    with pytest.raises(ValueError):
        JwtAuthProvider(algorithms=["HS256"])
    with pytest.raises(ValueError):
        JwtAuthProvider(algorithms=["HS256"], key="k", key_resolver=lambda _t: "k")


# ---------- B5: rate limit ----------
class Clock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


async def test_rate_limit_blocks_after_limit_with_retry_after() -> None:
    clock, user = Clock(), uuid4()
    rl = InMemoryRateLimiter(monotonic=clock)
    for _ in range(3):
        await rl.hit(user, "ask", 3, 60)
        clock.t += 10
    with pytest.raises(RateLimited) as ei:
        await rl.hit(user, "ask", 3, 60)
    assert ei.value.retry_after_seconds == 30  # lượt đầu hết hạn sau 60 - 30 = 30s


async def test_rate_limit_window_slides() -> None:
    clock, user = Clock(), uuid4()
    rl = InMemoryRateLimiter(monotonic=clock)
    await rl.hit(user, "ask", 1, 60)
    clock.t += 61
    await rl.hit(user, "ask", 1, 60)  # cửa sổ cũ đã trượt qua


async def test_rate_limit_is_per_user_and_per_bucket() -> None:
    rl = InMemoryRateLimiter()
    a, b = uuid4(), uuid4()
    await rl.hit(a, "ask", 1, 60)
    await rl.hit(b, "ask", 1, 60)  # người dùng khác
    await rl.hit(a, "upload", 1, 60)  # nhóm khác
    with pytest.raises(RateLimited):
        await rl.hit(a, "ask", 1, 60)
