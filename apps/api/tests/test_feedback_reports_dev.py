"""US-502 (phản hồi), US-501/F1 (báo cáo MVP), đăng nhập dev và chế độ chạy local."""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from api_helpers import Env, completed, parse_sse
from fastapi.testclient import TestClient

from docchat_api.devserver import build_dev
from docchat_api.main import create_app
from docchat_core.config import Settings
from docchat_infra.memory import TELEMETRY_ALLOWLIST
from docchat_infra.pdf.synthetic import make_pdf

ROOT = Path(__file__).resolve().parents[3]


def ai_id(env: Env) -> str:
    return str(next(m.id for m in env.store.messages.values() if m.role.value == "ai"))


# ---------- feedback ----------
@pytest.fixture()
def answered(env: Env):  # type: ignore[no-untyped-def]
    env.accept_notice()
    doc, chunk = env.seed_ready_document()
    env.pipeline.script = [completed(doc, chunk)]
    env.ask(env.conversation())
    return env, ai_id(env)


def put(env: Env, mid: str, body: dict[str, Any], sub: str = "alice") -> Any:
    return env.client.put(f"/api/v1/messages/{mid}/feedback", json=body, headers=env.headers(sub))


def test_feedback_is_stored_and_overwritable(answered) -> None:  # type: ignore[no-untyped-def]
    env, mid = answered
    assert put(env, mid, {"rating": "down", "reasonCode": "wrong_answer"}).status_code == 204
    assert list(env.store.feedback.values()) == [("down", "wrong_answer")]
    assert put(env, mid, {"rating": "up", "reasonCode": "wrong_answer"}).status_code == 204
    assert list(env.store.feedback.values()) == [("up", None)]  # lý do chỉ có nghĩa với "down"


@pytest.mark.parametrize(
    "body",
    [
        {"rating": "meh"},
        {"rating": "down", "reasonCode": "Có dấu và khoảng trắng"},
        {"rating": "down", "reasonCode": "x" * 40},
    ],
)
def test_feedback_rejects_free_text_and_unknown_ratings(answered, body) -> None:  # type: ignore[no-untyped-def]
    env, mid = answered
    assert put(env, mid, body).status_code == 400
    assert env.store.feedback == {}


def test_feedback_only_on_own_ai_messages(answered) -> None:  # type: ignore[no-untyped-def]
    env, mid = answered
    user_msg = next(m for m in env.store.messages.values() if m.role.value == "user")
    assert put(env, str(user_msg.id), {"rating": "up"}).status_code == 404
    assert put(env, str(uuid4()), {"rating": "up"}).status_code == 404
    assert put(env, mid, {"rating": "up"}, sub="bob").status_code == 404


# ---------- báo cáo MVP ----------
def telemetry(
    env: Env, sub: str, *events: tuple[str, dict[str, Any]], session: str | None = None
) -> None:
    sid = session or str(uuid4())
    body = {
        "events": [
            {
                "name": n,
                "ts": datetime.now(UTC).isoformat(),
                "sessionId": sid,
                "appVersion": "0.1.0",
                "props": p,
            }
            for n, p in events
        ]
    }
    r = env.client.post("/api/v1/telemetry/events", json=body, headers=env.headers(sub))
    assert r.status_code == 202, r.text


def report(env: Env, sub: str = "minh", **params: Any) -> Any:
    return env.client.get(
        "/api/v1/reports/mvp-metrics", params=params, headers=env.headers(sub, roles=["evaluator"])
    )


def test_report_requires_evaluator_role(env: Env) -> None:
    r = env.client.get("/api/v1/reports/mvp-metrics", headers=env.headers("alice"))
    assert r.status_code == 403 and r.json()["code"] == "FORBIDDEN"
    assert env.client.get("/api/v1/reports/mvp-metrics").status_code == 401
    assert report(env).status_code == 200


def test_empty_report_says_it_cannot_conclude(env: Env) -> None:
    body = report(env).json()
    assert body["conclusive"] is False
    assert any("chưa được duyệt" in r for r in body["reasons"]) and any(
        "baseline" in r for r in body["reasons"]
    )
    assert {m["id"] for m in body["metrics"]} == {"MET-001", "MET-002", "KR1.2", "KR2.2"}
    assert all(m["status"] == "unknown" and m["value"] is None for m in body["metrics"])
    assert [f["event"] for f in body["funnel"]][0] == "session_started"


def seed_telemetry(env: Env) -> None:
    for i in range(4):
        telemetry(
            env, "alice",
            ("session_started", {"entry_source": "direct"}),
            ("answer_first_token", {"latency_ms": 1000 + 1000 * i}),
            ("answer_completed", {"total_ms": 4000, "citation_count": 2 if i < 3 else 0, "grounded": i < 3}),
            ("task_marked_done", {"task_id": f"T{i}", "elapsed_ms": 30000 + 10000 * i, "success": i != 3}),
        )  # fmt: skip
    telemetry(
        env,
        "alice",
        ("upload_succeeded", {"file_size": 1, "duration_ms": 5}),
        ("upload_failed", {"error_code": "X", "file_size": 1}),
    )
    telemetry(env, "alice", ("answer_failed", {"error_code": "LLM_TIMEOUT", "stage": "generation"}))


def test_report_computes_metrics_but_stays_inconclusive_until_targets_are_approved(
    env: Env,
) -> None:
    seed_telemetry(env)
    body = report(env).json()
    m = {x["id"]: x for x in body["metrics"]}
    assert m["MET-002"]["value"] == 75.0 and m["MET-002"]["sample"] == 4  # 3/4 tác vụ thành công
    assert m["KR2.2"]["value"] == 75.0  # 3/4 câu trả lời có trích dẫn hợp lệ
    assert m["KR1.2"]["value"] == pytest.approx(3.85, abs=0.01)  # p95 của 1,2,3,4 giây (nội suy)
    assert m["MET-001"]["value"] is None  # chưa có baseline
    assert all(x["status"] == "unknown" for x in m.values()) and body["conclusive"] is False
    assert body["inputs"]["tasks"] == 4 and body["inputs"]["sessions"] >= 4


def test_report_judges_targets_once_approved_and_baseline_given(env: Env) -> None:
    seed_telemetry(env)
    env.config.values.update(metrics_targets_approved=True, met001_baseline_ms=80000)
    body = report(env).json()
    m = {x["id"]: x for x in body["metrics"]}
    # trung vị thời gian của tác vụ thành công (30s, 40s, 50s) = 40s → giảm 50% so với baseline 80s
    assert m["MET-001"]["value"] == 50.0 and m["MET-001"]["status"] == "met"
    assert m["MET-002"]["status"] == "not_met"  # 75% < 80%
    assert m["KR2.2"]["status"] == "not_met"  # 75% < 90%
    assert m["KR1.2"]["status"] == "met"  # 3,85 s ≤ 5 s
    assert body["conclusive"] is True and body["reasons"] == []


def test_report_error_rates_and_funnel(env: Env) -> None:
    seed_telemetry(env)
    body = report(env).json()
    rates = {r["event"]: r for r in body["errorRates"]}
    assert rates["upload_failed"]["failed"] == 1 and rates["upload_failed"]["total"] == 2
    gen = rates["answer_failed (stage=generation)"]
    assert gen["failed"] == 1 and gen["total"] == 5 and gen["rate"] == 20.0
    funnel = {f["event"]: f["sessions"] for f in body["funnel"]}
    assert funnel["session_started"] == 4 and funnel["citation_opened"] == 0


def test_report_exposes_no_content_or_identifiers(env: Env) -> None:
    seed_telemetry(env)
    text = report(env).text
    uid = str(env.user_id("alice"))
    assert uid not in text and "dev|" not in text and "alice" not in text
    assert not re.search(r"[0-9a-f]{64}", text)  # không lộ user_hash


def test_report_period_filter(env: Env) -> None:
    seed_telemetry(env)
    assert report(env, until="2000-01-01T00:00:00Z").json()["inputs"]["tasks"] == 0
    assert report(env, since="2000-01-01T00:00:00Z").json()["inputs"]["tasks"] == 4


# ---------- đăng nhập dev + chế độ local ----------
def test_dev_login_route_is_absent_outside_dev(env: Env) -> None:
    assert (
        env.client.post("/api/v1/dev/login", json={"name": "x"}).status_code == 404
    )  # environment=test


@pytest.fixture()
def local() -> Any:
    settings = Settings(environment="dev")
    container, ingest = build_dev(settings)

    async def loop(stop: Any) -> None:
        await ingest.run_forever(stop, poll_interval=0.05)

    with TestClient(create_app(container, workers=[loop])) as client:
        yield client


def login(client: TestClient, name: str = "Lan", roles: list[str] | None = None) -> dict[str, str]:
    r = client.post("/api/v1/dev/login", json={"name": name, "roles": roles or ["user"]})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['accessToken']}"}


def test_dev_login_issues_usable_tokens_and_filters_roles(local: TestClient) -> None:
    r = local.post(
        "/api/v1/dev/login", json={"name": "Minh", "roles": ["evaluator", "superadmin"]}
    ).json()
    assert r["roles"] == ["evaluator"] and r["subject"] == "dev|minh" and r["expiresIn"] > 0
    h = {"Authorization": f"Bearer {r['accessToken']}"}
    assert local.get("/api/v1/config", headers=h).status_code == 200
    assert (
        local.get("/api/v1/reports/mvp-metrics", headers=h).status_code == 200
    )  # role evaluator hoạt động
    assert local.post("/api/v1/dev/login", json={"name": "<script>"}).status_code == 400
    assert local.post("/api/v1/dev/login", json={"name": ""}).status_code == 400


def test_local_mode_end_to_end_with_background_ingest(local: TestClient) -> None:
    h = login(local)
    v = local.get("/api/v1/data-notice", headers=h).json()["version"]
    local.post("/api/v1/data-notice/acceptances", json={"version": v}, headers=h)
    pdf = make_pdf(
        [
            "BÁO GIÁ\nGiá trọn gói là 250 triệu đồng.",
            "BẢO HÀNH\nThiết bị được bảo hành 12 tháng kể từ ngày bàn giao.",
        ]
    )
    r = local.post(
        "/api/v1/documents",
        files={"file": ("baogia.pdf", pdf, "application/pdf")},
        headers={**h, "Idempotency-Key": str(uuid4())},
    )
    assert r.status_code == 202 and r.json()["status"] == "processing"

    doc: dict[str, Any] = {}
    for _ in range(100):  # worker chạy nền trong cùng tiến trình xử lý PDF
        doc = local.get(f"/api/v1/documents/{r.json()['id']}", headers=h).json()
        if doc["status"] != "processing":
            break
        time.sleep(0.05)
    assert doc["status"] == "ready" and doc["pageCount"] == 2

    conv = local.post("/api/v1/conversations", headers=h).json()["id"]
    res = local.post(
        f"/api/v1/conversations/{conv}/messages",
        json={"question": "Thiết bị được bảo hành bao lâu kể từ ngày bàn giao?"},
        headers=h,
    )
    events = parse_sse(res.text)
    assert events[-1][1]["grounded"] is True
    cit = next(d for n, d in events if n == "citations")["citations"][0]
    assert cit["documentName"] == "baogia.pdf" and cit["page"] == 2
    src = local.get(f"/api/v1/citations/{cit['id']}", headers=h).json()
    assert "12 tháng" in src["snippet"]


def test_local_mode_refuses_non_dev_environment() -> None:
    with pytest.raises(RuntimeError, match="ENVIRONMENT=dev"):
        build_dev(Settings(environment="staging"))


def test_in_memory_telemetry_allowlist_matches_the_database_seed() -> None:
    """Chống lệch giữa bản bộ nhớ và migration V005."""
    sql = (ROOT / "db/migrations/sql/V005__seed_reference.sql").read_text(encoding="utf-8")
    seeded = {
        name: frozenset(re.findall(r"'(\w+)'", props))
        for name, props in re.findall(r"\('(\w+)',\s*ARRAY\[([^\]]*)\]\)", sql)
    }
    assert seeded == TELEMETRY_ALLOWLIST


def test_static_ui_is_served_last_and_does_not_shadow_the_api(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>UI</h1>", encoding="utf-8")
    container, _ = build_dev(Settings(environment="dev"))
    with TestClient(create_app(container, static_dir=tmp_path)) as client:
        assert client.get("/").text == "<h1>UI</h1>"
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/api/v1/config").status_code == 401  # API vẫn hoạt động
