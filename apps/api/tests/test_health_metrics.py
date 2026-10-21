import logging
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from docchat_api.main import create_app


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as c:
        yield c


def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
    assert r.headers["x-request-id"]


def test_metrics_exposes_expected_names(client: TestClient) -> None:
    client.get("/health")
    body = client.get("/metrics").text
    for name in (
        "docchat_http_request_duration_seconds",
        "docchat_answer_first_token_seconds",
        "docchat_ingest_queue_length",
        "docchat_ingest_duration_seconds",
        "docchat_stage_errors_total",
        "docchat_answers_total",
    ):
        assert name in body, name


def test_metrics_hidden_behind_reverse_proxy(client: TestClient) -> None:
    assert client.get("/metrics", headers={"X-Forwarded-For": "1.2.3.4"}).status_code == 404


def test_request_log_has_route_template_not_content(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="docchat.api"):
        client.get("/health?q=bí-mật")
    rec = next(r for r in caplog.records if r.getMessage() == "request")
    assert rec.route == "/health"  # type: ignore[attr-defined]
    assert "bí-mật" not in str(rec.__dict__)


def test_ready_reports_503_when_db_down(client: TestClient) -> None:
    # Không có Postgres trong unit test ⇒ readiness phải báo không sẵn sàng, không văng 500.
    assert client.get("/ready").status_code == 503
