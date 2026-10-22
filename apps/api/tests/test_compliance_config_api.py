"""B6 (thông báo dữ liệu), /config, B9 (kill switch qua endpoint admin)."""

from __future__ import annotations

from api_helpers import Env, make_env

from docchat_core.domain import DataNotice


def test_notice_and_acceptance_flow(env: Env) -> None:
    h = env.headers()
    n = env.client.get("/api/v1/data-notice", headers=h).json()
    assert n["version"] == "draft-0" and n["content"] and n["accepted"] is False

    bad = env.client.post("/api/v1/data-notice/acceptances", json={"version": "old"}, headers=h)
    assert bad.status_code == 409 and bad.json()["code"] == "NOTICE_VERSION_MISMATCH"

    ok = env.client.post("/api/v1/data-notice/acceptances", json={"version": "draft-0"}, headers=h)
    assert ok.status_code == 201
    assert env.client.get("/api/v1/data-notice", headers=h).json()["accepted"] is True


def test_accepting_twice_is_idempotent_and_audits_once(env: Env) -> None:
    env.accept_notice()
    env.accept_notice()
    uid = env.user_id("alice")
    assert [a for a in env.store.audit if a[:2] == (uid, "notice_accepted")] == [
        (uid, "notice_accepted", None)
    ]


def test_new_notice_version_requires_reacceptance(env: Env) -> None:
    env.accept_notice()
    assert env.upload().status_code == 202
    env.store.notice = DataNotice("2026-11-v2", "Nội dung mới")
    r = env.upload()
    assert r.status_code == 403 and r.json()["code"] == "NOTICE_NOT_ACCEPTED"
    h = env.headers()
    assert env.client.get("/api/v1/config", headers=h).json()["noticeAccepted"] is False
    assert (
        env.client.post(
            "/api/v1/data-notice/acceptances", json={"version": "2026-11-v2"}, headers=h
        ).status_code
        == 201
    )
    assert env.upload().status_code == 202


def test_acceptances_are_per_user(env: Env) -> None:
    env.accept_notice("alice")
    assert env.upload("bob").status_code == 403


def test_config_exposes_limits_from_app_config() -> None:
    for e in make_env(
        {"max_file_size_bytes": 1000, "max_files_per_user": 3, "max_question_length": 99}
    ):
        body = e.client.get("/api/v1/config", headers=e.headers()).json()
        assert body["maxFileSizeBytes"] == 1000
        assert body["maxFiles"] == 3 and body["maxQuestionLength"] == 99
        assert body["acceptedTypes"] == ["application/pdf"]
        assert body["qaEnabled"] is True and body["noticeAccepted"] is False
        assert body["noticeVersion"] == "draft-0"


def test_admin_flag_requires_ops_role(env: Env) -> None:
    r = env.client.put(
        "/api/v1/admin/flags/qa-enabled", json={"enabled": False}, headers=env.headers("alice")
    )
    assert r.status_code == 403 and r.json()["code"] == "FORBIDDEN"
    assert env.config.values.get("qa_enabled", True) is True


def test_ops_can_toggle_kill_switch_and_ask_is_blocked(env: Env) -> None:
    env.accept_notice()
    conv = env.conversation()
    ops = env.headers("root", roles=["ops"])
    assert (
        env.client.put(
            "/api/v1/admin/flags/qa-enabled", json={"enabled": False}, headers=ops
        ).status_code
        == 204
    )
    assert env.client.get("/api/v1/config", headers=env.headers()).json()["qaEnabled"] is False

    r = env.ask(conv)
    assert r.status_code == 503 and r.json()["code"] == "QA_DISABLED"
    assert env.pipeline.calls == []
    assert env.upload().status_code == 202  # tải tài liệu vẫn hoạt động khi tắt hỏi đáp

    assert (
        env.client.put(
            "/api/v1/admin/flags/qa-enabled", json={"enabled": True}, headers=ops
        ).status_code
        == 204
    )
    doc, chunk = env.seed_ready_document()
    from api_helpers import completed

    env.pipeline.script = [completed(doc, chunk)]
    assert env.ask(conv).status_code == 200
