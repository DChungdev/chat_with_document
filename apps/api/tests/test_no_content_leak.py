"""G4 (NFR riêng tư): nội dung tài liệu, câu hỏi, tên tệp KHÔNG xuất hiện trong log, metrics, telemetry, audit.

Dùng "canary": chuỗi hiếm nhúng vào PDF, tên tệp và câu hỏi; chạy đủ luồng (thành công + các đường lỗi),
rồi quét mọi đầu ra vận hành. Phản hồi cho chính chủ (tài liệu, câu trả lời) được phép chứa canary.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import pytest
from api_helpers import parse_sse
from prometheus_client import generate_latest
from qa_helpers import QaEnv, make_qa_env

from docchat_infra.pdf.synthetic import make_pdf

DOC_CANARY = "ZEBRAXQ7NOIDUNG"
Q_CANARY = "ZEBRAXQ7CAUHOI"
FILE_CANARY = "ZEBRAXQ7TENTEP"
ALL = (DOC_CANARY, Q_CANARY, FILE_CANARY)

PDF = make_pdf([f"BÁO GIÁ\nThanh toán trong vòng 30 ngày với mã {DOC_CANARY} theo hợp đồng."])


@pytest.fixture()
def env() -> Iterator[QaEnv]:
    yield from make_qa_env()


def _ops_outputs(
    env: QaEnv, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> dict[str, str]:
    out = capsys.readouterr()
    return {
        "stdout": out.out,
        "stderr": out.err,
        "caplog": "\n".join(
            f"{r.getMessage()} {r.exc_text or ''} {r.__dict__.get('stack_info') or ''}"
            for r in caplog.records
        ),
        "metrics": generate_latest().decode("utf8"),
        "telemetry": repr(env.store.telemetry),
        "audit": repr(env.store.audit),
    }


def _assert_clean(outputs: dict[str, str]) -> None:
    for name, text in outputs.items():
        for canary in ALL:
            assert canary not in text, f"canary {canary} rò vào {name}"
    # vẫn có log (kiểm tra test không rỗng vô nghĩa)
    assert "request" in outputs["stdout"] or "request" in outputs["caplog"]


def test_happy_path_leaks_nothing(env: QaEnv, capsys, caplog) -> None:  # type: ignore[no-untyped-def]
    caplog.set_level(logging.DEBUG)
    env.accept_notice()
    r = env.upload(name=f"{FILE_CANARY}.pdf", content=PDF)
    assert r.status_code == 202
    env.run_ingest()
    conv = env.conversation()
    resp = env.ask(conv, f"Thanh toán trong vòng bao nhiêu ngày với mã {Q_CANARY}?")
    events = parse_sse(resp.text)
    assert events[-1][0] == "done"
    # chủ sở hữu được thấy nội dung của mình (không phải rò)
    assert FILE_CANARY in env.client.get("/api/v1/documents", headers=env.headers()).text
    cit = next(d for n, d in events if n == "citations")["citations"][0]["id"]
    assert DOC_CANARY in env.client.get(f"/api/v1/citations/{cit}", headers=env.headers()).text
    env.client.delete(f"/api/v1/documents/{r.json()['id']}", headers=env.headers())
    _assert_clean(_ops_outputs(env, capsys, caplog))


def test_failure_paths_leak_nothing(env: QaEnv, capsys, caplog, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    caplog.set_level(logging.DEBUG)
    env.accept_notice()
    env.upload(name=f"{FILE_CANARY}.pdf", content=PDF)
    env.run_ingest()
    # PDF hỏng + tệp giả PDF mang canary trong tên và thân
    bad = env.upload(
        name=f"{FILE_CANARY}-hong.pdf", content=b"%PDF-1.4 " + DOC_CANARY.encode() + b" broken"
    )
    env.run_ingest()
    env.upload(name=f"{FILE_CANARY}.txt", content=DOC_CANARY.encode(), content_type="text/plain")
    assert bad.status_code in (202, 400, 415)

    async def boom(**kwargs: Any):  # nhà cung cấp lỗi, thông điệp lỗi dội lại cả prompt
        raise RuntimeError(f"provider echo: {kwargs.get('user')}")
        yield ""  # pragma: no cover

    monkeypatch.setattr(env.llm, "stream", boom)
    conv = env.conversation()
    resp = env.ask(conv, f"Thanh toán trong vòng bao nhiêu ngày với mã {Q_CANARY}?")
    events = parse_sse(resp.text)
    assert events[-1][0] == "error", events  # đường lỗi nhà cung cấp thật sự được chạm tới
    assert Q_CANARY not in str(events)  # phản hồi lỗi cho client cũng không dội lại nội dung
    _assert_clean(_ops_outputs(env, capsys, caplog))


def test_telemetry_endpoint_refuses_content_even_if_client_sends_it(env: QaEnv, capsys, caplog) -> None:  # type: ignore[no-untyped-def]
    caplog.set_level(logging.DEBUG)
    env.accept_notice()
    from datetime import UTC, datetime
    from uuid import uuid4

    def ev(name: str, **props: Any) -> dict[str, Any]:
        return {
            "name": name,
            "ts": datetime.now(UTC).isoformat(),
            "sessionId": str(uuid4()),
            "appVersion": "0.1.0",
            "props": props,
        }

    r = env.client.post(
        "/api/v1/telemetry/events",
        json={
            "events": [
                ev("answer_completed", question=Q_CANARY, totalMs=12),
                ev("upload_failed", fileName=FILE_CANARY, fileSize=10),
                ev("answer_completed", errorCode=Q_CANARY * 3, totalMs=5),
            ]
        },
        headers=env.headers(),
    )
    assert r.status_code == 202, r.text
    assert r.json()["accepted"] + r.json()["rejected"] == 3, r.json()
    _assert_clean(_ops_outputs(env, capsys, caplog))
