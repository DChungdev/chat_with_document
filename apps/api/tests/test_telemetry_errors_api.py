"""B10 (telemetry allow-list) và B5 (định dạng lỗi RFC 7807)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from api_helpers import Env

from docchat_core.application.telemetry import TelemetryService


def ev(name: str = "answer_completed", **props: Any) -> dict[str, Any]:
    return {
        "name": name,
        "ts": datetime.now(UTC).isoformat(),
        "sessionId": str(uuid4()),
        "appVersion": "0.1.0",
        "props": props,
    }


def post(env: Env, *events: dict[str, Any], sub: str = "alice") -> Any:
    return env.client.post(
        "/api/v1/telemetry/events", json={"events": list(events)}, headers=env.headers(sub)
    )


# ---------- B10 ----------
def test_valid_event_is_stored_with_snake_case_props_and_hashed_user(env: Env) -> None:
    r = post(env, ev(totalMs=4200, citationCount=2, grounded=True))
    assert r.status_code == 202 and r.json() == {"accepted": 1, "rejected": 0}
    (stored,) = env.store.telemetry
    assert stored.props == {"total_ms": 4200, "citation_count": 2, "grounded": True}
    uid = str(env.user_id("alice"))
    assert re.fullmatch(r"[0-9a-f]{64}", stored.user_hash) and uid not in stored.user_hash
    assert uid not in repr(stored)  # user_id dạng rõ không xuất hiện trong bảng


def test_unknown_event_name_is_rejected(env: Env) -> None:
    r = post(env, ev("totally_unknown"), ev("citation_opened", citationIndex=1))
    assert r.json() == {"accepted": 1, "rejected": 1}
    assert [e.name for e in env.store.telemetry] == ["citation_opened"]


def test_unknown_props_are_dropped_but_event_kept(env: Env) -> None:
    post(env, ev(totalMs=10, sneaky=123))
    assert env.store.telemetry[0].props == {"total_ms": 10}


def test_free_text_values_are_dropped(env: Env) -> None:
    long_text = "Điều khoản thanh toán là gì và tôi cần biết chi tiết " * 3
    post(env, ev("upload_failed", errorCode=long_text, fileSize=100))
    assert env.store.telemetry[0].props == {"file_size": 100}  # chuỗi dài/văn bản tự do bị loại
    post(env, ev("upload_failed", errorCode="PDF_CORRUPT"))
    assert env.store.telemetry[1].props == {"error_code": "PDF_CORRUPT"}


def test_content_like_property_rejects_whole_event(env: Env) -> None:
    r = post(env, ev(question="Điều khoản thanh toán là gì?", totalMs=1))
    assert r.json() == {"accepted": 0, "rejected": 1}
    assert env.store.telemetry == []


def test_client_cannot_send_user_id(env: Env) -> None:
    post(env, ev(userId="spoofed", totalMs=1))
    assert "user_id" not in env.store.telemetry[0].props


def test_batch_limit_is_50(env: Env) -> None:
    assert post(env, *[ev(totalMs=1) for _ in range(51)]).status_code == 400
    assert post(env, *[ev(totalMs=1) for _ in range(50)]).json()["accepted"] == 50


def test_persist_failure_does_not_change_response(env: Env, monkeypatch: Any) -> None:
    async def boom(self: TelemetryService, user_id: Any, events: Any) -> None:
        raise ConnectionError("db down")

    monkeypatch.setattr(TelemetryService, "store", boom)
    r = post(env, ev(totalMs=1))
    assert r.status_code == 202 and r.json()["accepted"] == 1


def test_telemetry_requires_authentication(env: Env) -> None:
    r = env.client.post("/api/v1/telemetry/events", json={"events": []})
    assert r.status_code == 401


# ---------- B5 ----------
def test_problem_json_shape_for_domain_error(env: Env) -> None:
    r = env.client.get(f"/api/v1/documents/{uuid4()}", headers=env.headers())
    body = r.json()
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")
    assert set(body) == {"type", "title", "status", "code", "detail", "retryable", "requestId"}
    assert body["type"] == "https://docs.example/errors/not-found" and body["retryable"] is False
    assert body["requestId"] == r.headers["x-request-id"]


def test_request_id_from_client_is_echoed(env: Env) -> None:
    r = env.client.get("/api/v1/documents", headers={**env.headers(), "X-Request-Id": "abc-123"})
    assert r.headers["x-request-id"] == "abc-123"


def test_unknown_route_is_problem_json(env: Env) -> None:
    r = env.client.get("/api/v1/nope", headers=env.headers())
    assert r.status_code == 404 and r.json()["code"] == "NOT_FOUND"


def test_unhandled_exception_is_500_without_internal_details(env: Env) -> None:
    @env.client.app.get("/boom")  # type: ignore[attr-defined]
    async def boom() -> None:
        raise RuntimeError("secret-internal-detail")

    r = env.client.get("/boom")
    assert r.status_code == 500 and r.json()["code"] == "INTERNAL_ERROR"
    assert "secret-internal-detail" not in r.text


def test_401_carries_www_authenticate(env: Env) -> None:
    r = env.client.get("/api/v1/documents")
    assert r.headers["www-authenticate"] == "Bearer"


def test_expired_token_returns_session_expired(env: Env) -> None:
    expired = env.token("alice", expires_in=-3600)
    r = env.client.get("/api/v1/documents", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401 and r.json()["code"] == "SESSION_EXPIRED"


def test_malformed_authorization_header(env: Env) -> None:
    for header in ("", "Basic abc", "Bearer", "Bearer not.a.jwt"):
        r = env.client.get("/api/v1/documents", headers={"Authorization": header})
        assert r.status_code == 401 and r.json()["code"] == "UNAUTHENTICATED"


def test_user_is_created_on_first_request_and_reused(env: Env) -> None:
    env.client.get("/api/v1/documents", headers=env.headers("carol"))
    env.client.get("/api/v1/documents", headers=env.headers("carol"))
    assert [u.external_subject for u in env.store.users.values()] == ["carol"]


def test_health_endpoints_need_no_auth(env: Env) -> None:
    for path in ("/health", "/api/v1/health/live"):
        assert env.client.get(path).status_code == 200
    assert env.client.get("/api/v1/health/ready").status_code == 503  # không có engine trong test
