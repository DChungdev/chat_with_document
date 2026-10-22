"""Báo cáo đánh giá MVP cho Minh (US-501, SCR-09): MET-001, MET-002, KR1.2, KR2.2.

Chỉ dùng số liệu tổng hợp từ telemetry (độ dài, số lượng, mã lỗi) — không có nội dung tài liệu hay
câu hỏi. Mục tiêu, baseline và việc “đã được duyệt” đọc từ `app_config`; khi chưa duyệt (OQ-005,
OQ-009) báo cáo ghi rõ “chưa thể kết luận” theo AC của US-501 thay vì tự kết luận Đạt/Không đạt.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from docchat_core.application.common import Clock, utc_now
from docchat_core.config import AppConfig
from docchat_core.domain import UserRole
from docchat_core.domain.errors import Forbidden
from docchat_core.ports import Principal, UnitOfWorkFactory

FUNNEL = (
    "session_started",
    "data_notice_accepted",
    "upload_succeeded",
    "document_ready",
    "question_submitted",
    "answer_completed",
    "citation_opened",
)

# (bước, sự kiện hiển thị, khóa lỗi trong aggregates["errors"])
ERROR_STEPS = (
    ("Tải lên", "upload_failed", "upload"),
    ("Xử lý tài liệu", "document_processing_failed", "processing"),
    ("Sinh câu trả lời", "answer_failed (stage=generation)", "generation"),
    ("Streaming", "answer_failed (stage=streaming)", "streaming"),
)


def _pct(part: float, whole: float) -> float | None:
    return round(100.0 * part / whole, 1) if whole else None


@dataclass(frozen=True)
class MetricLine:
    id: str
    label: str
    value: float | None
    unit: str
    target: float
    comparison: str  # ">=" | "<="
    status: str  # met | not_met | unknown
    sample: int
    note: str


class ReportService:
    def __init__(
        self, uow_factory: UnitOfWorkFactory, config: AppConfig, *, clock: Clock = utc_now
    ) -> None:
        self._uow = uow_factory
        self._config = config
        self._clock = clock

    async def mvp(
        self,
        user_id: UUID,
        principal: Principal,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> dict[str, Any]:
        if UserRole.EVALUATOR not in principal.roles:
            raise Forbidden()
        async with self._uow.for_user(user_id) as uow:
            agg = await uow.reports.aggregates(since, until)

        cfg = self._config
        approved = bool(await cfg.get("metrics_targets_approved"))
        baseline = await cfg.get("met001_baseline_ms")
        tgt1 = float(await cfg.get("met001_target_reduction_pct"))
        tgt2 = float(await cfg.get("met002_target_pct"))
        tgt_ft = float(await cfg.get("first_token_target_ms"))
        tgt_cit = float(await cfg.get("citation_target_pct"))

        median = agg.get("met001MedianMs")
        reduction = (
            round(100.0 * (float(baseline) - float(median)) / float(baseline), 1)
            if baseline and median is not None
            else None
        )
        success_pct = _pct(agg["tasksSuccess"], agg["tasksTotal"])
        cited_pct = _pct(agg["answersWithCitation"], agg["answersCompleted"])
        p95 = agg.get("firstTokenP95Ms")

        def status(value: float | None, target: float, cmp: str) -> str:
            if not approved or value is None:
                return "unknown"  # chưa duyệt mục tiêu / thiếu dữ liệu ⇒ không kết luận
            return "met" if (value >= target if cmp == ">=" else value <= target) else "not_met"

        metrics = [
            MetricLine("MET-001", "Giảm thời gian tra cứu (trung vị)", reduction, "%", tgt1, ">=",
                       status(reduction, tgt1, ">="), agg["tasksSuccess"],
                       "Cần baseline thời gian tra cứu thủ công (met001_baseline_ms)."
                       if baseline is None else "So với baseline đã nhập."),
            MetricLine("MET-002", "Tác vụ được xác nhận thành công", success_pct, "%", tgt2, ">=",
                       status(success_pct, tgt2, ">="), agg["tasksTotal"],
                       "Dựa trên sự kiện task_marked_done."),
            MetricLine("KR1.2", "Token đầu (p95)", None if p95 is None else round(p95 / 1000, 2),
                       "s", tgt_ft / 1000, "<=", status(None if p95 is None else p95 / 1000, tgt_ft / 1000, "<="),
                       agg["firstTokenN"], "Đo ở trình duyệt: từ lúc gửi câu hỏi tới token đầu."),
            MetricLine("KR2.2", "Câu trả lời có trích dẫn hợp lệ", cited_pct, "%", tgt_cit, ">=",
                       status(cited_pct, tgt_cit, ">="), agg["answersCompleted"],
                       "grounded và có ít nhất một trích dẫn."),
        ]  # fmt: skip

        reasons = []
        if not approved:
            reasons.append("Mục tiêu MET-001/MET-002 chưa được duyệt (OQ-005).")
        if baseline is None:
            reasons.append("Chưa có baseline thời gian tra cứu để tính MET-001 (OQ-005).")
        if agg["tasksTotal"] == 0:
            reasons.append("Chưa có tác vụ nào được người dùng xác nhận (task_marked_done).")

        errors = agg["errors"]
        return {
            "generatedAt": self._clock().isoformat(),
            "conclusive": not reasons and all(m.status != "unknown" for m in metrics),
            "reasons": reasons,
            "inputs": {
                "sessions": agg["sessions"], "users": agg["users"], "tasks": agg["tasksTotal"],
                "answers": agg["answersCompleted"],
            },  # fmt: skip
            "metrics": [m.__dict__ for m in metrics],
            "errorRates": [
                {
                    "step": step, "event": event, "failed": errors[key]["failed"],
                    "total": errors[key]["total"], "rate": _pct(errors[key]["failed"], errors[key]["total"]),
                }
                for step, event, key in ERROR_STEPS
            ],  # fmt: skip
            "funnel": [{"event": name, "sessions": agg["funnel"].get(name, 0)} for name in FUNNEL],
        }
