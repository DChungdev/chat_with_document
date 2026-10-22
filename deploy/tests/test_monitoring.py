"""F2: dashboard và rule cảnh báo chỉ được tham chiếu metric thật, không rò nội dung."""

import json
import re
from pathlib import Path

from prometheus_client import REGISTRY

import docchat_infra.observability.metrics  # noqa: F401  (đăng ký metric)

MON = Path(__file__).resolve().parents[1] / "monitoring"
SUFFIX = ("_bucket", "_count", "_sum", "_total")


def _known() -> set[str]:
    names: set[str] = set()
    for fam in REGISTRY.collect():
        for s in fam.samples:
            names.add(s.name)
        names.add(fam.name)
    return {n for n in names if n.startswith("docchat_")}


def _used(text: str) -> set[str]:
    return set(re.findall(r"\bdocchat_[a-z0-9_]+", text))


def _resolves(name: str, known: set[str]) -> bool:
    if name in known:
        return True
    return any(name.endswith(s) and name[: -len(s)] in known for s in SUFFIX)


def test_alert_rules_reference_existing_metrics():
    text = (MON / "alerts.yml").read_text(encoding="utf8")
    exprs = "\n".join(ln for ln in text.splitlines() if "expr" in ln or ln.startswith("          "))
    known = _known()
    missing = {m for m in _used(exprs) if not _resolves(m, known)}
    assert missing == set(), missing


def test_alerts_cover_required_scenarios():
    text = (MON / "alerts.yml").read_text(encoding="utf8")
    for alert in (
        "DocchatFirstTokenSlow",
        "DocchatStageErrorsHigh",
        "DocchatLlmProviderErrors",
        "DocchatEmbeddingProviderErrors",
        "DocchatIngestBacklog",
    ):
        assert f"alert: {alert}" in text
    assert text.count("alert:") == text.count("summary:")  # mỗi cảnh báo có mô tả
    assert "> 5" in text  # p95 token đầu > 5s


def test_dashboard_is_valid_and_uses_real_metrics():
    d = json.loads((MON / "grafana-dashboard.json").read_text(encoding="utf8"))
    exprs = [t["expr"] for p in d["panels"] for t in p["targets"]]
    assert len(d["panels"]) >= 6
    known = _known()
    for e in exprs:
        for m in _used(e):
            assert _resolves(m, known), (m, e)
    joined = " ".join(exprs)
    for must in (
        "first_token",
        "ingest_queue_length",
        "ingest_duration",
        "stage_errors",
        "grounded",
    ):
        assert must in joined


def test_monitoring_never_uses_content_labels():
    blob = (MON / "alerts.yml").read_text(encoding="utf8") + (
        MON / "grafana-dashboard.json"
    ).read_text(encoding="utf8")
    for banned in ("question", "filename", "document_name", "user_id", "user_hash"):
        assert banned not in blob
