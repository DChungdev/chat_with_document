"""Feedback + báo cáo MVP trong bộ nhớ — cùng ngữ nghĩa với fn_mvp_report (V008)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from docchat_core.domain import TelemetryEvent
from docchat_infra.memory.base import _Repo

FUNNEL_EVENTS = (
    "session_started",
    "data_notice_accepted",
    "upload_succeeded",
    "document_ready",
    "question_submitted",
    "answer_completed",
    "citation_opened",
)


def percentile_cont(values: Sequence[float], q: float) -> float | None:
    """Giống percentile_cont của PostgreSQL (nội suy tuyến tính)."""
    if not values:
        return None
    xs = sorted(values)
    pos = q * (len(xs) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


class MemFeedback(_Repo):
    async def upsert(self, message_id: UUID, rating: str, reason_code: str | None) -> None:
        self.s.feedback[message_id] = (rating, reason_code)


class MemReports(_Repo):
    async def aggregates(self, since: datetime | None, until: datetime | None) -> dict[str, Any]:
        evs = [
            e
            for e in self.s.telemetry
            if (since is None or e.ts >= since) and (until is None or e.ts < until)
        ]

        def named(*names: str) -> list[TelemetryEvent]:
            return [e for e in evs if e.name in names]

        tasks = [
            e for e in named("task_marked_done") if "elapsed_ms" in e.props and "success" in e.props
        ]
        ok = [float(e.props["elapsed_ms"]) for e in tasks if e.props["success"]]  # type: ignore[arg-type]
        ft = [
            float(e.props["latency_ms"])  # type: ignore[arg-type]
            for e in named("answer_first_token")
            if "latency_ms" in e.props
        ]
        answers = named("answer_completed")
        cited = [
            e
            for e in answers
            if e.props.get("grounded") is True
            and int(e.props.get("citation_count", 0)) >= 1  # type: ignore[call-overload]
        ]
        failed = named("answer_failed")
        up, pr = len(named("upload_failed")), len(named("document_processing_failed"))
        gen_total = len(answers) + len(failed)

        def stage(name: str) -> int:
            return sum(1 for e in failed if e.props.get("stage") == name)

        return {
            "sessions": len({e.session_id for e in evs}),
            "users": len({e.user_hash for e in evs}),
            "tasksTotal": len(tasks),
            "tasksSuccess": sum(1 for e in tasks if e.props["success"]),
            "met001MedianMs": percentile_cont(ok, 0.5),
            "firstTokenN": len(ft),
            "firstTokenP95Ms": percentile_cont(ft, 0.95),
            "answersCompleted": len(answers),
            "answersWithCitation": len(cited),
            "errors": {
                "upload": {"failed": up, "total": up + len(named("upload_succeeded"))},
                "processing": {"failed": pr, "total": pr + len(named("document_ready"))},
                "generation": {"failed": stage("generation"), "total": gen_total},
                "streaming": {"failed": stage("streaming"), "total": gen_total},
            },
            "funnel": {
                n: len({e.session_id for e in evs if e.name == n})
                for n in FUNNEL_EVENTS
                if any(e.name == n for e in evs)
            },
        }
