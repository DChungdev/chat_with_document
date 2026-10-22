"""Dữ liệu tham chiếu mà CSDL seed ở V005 — nhân bản cho chế độ bộ nhớ (có test chống lệch)."""

from __future__ import annotations

TELEMETRY_ALLOWLIST: dict[str, frozenset[str]] = {
    "session_started": frozenset({"entry_source"}),
    "data_notice_accepted": frozenset({"notice_version"}),
    "upload_started": frozenset({"file_size", "file_index"}),
    "upload_succeeded": frozenset({"file_size", "duration_ms"}),
    "upload_failed": frozenset({"error_code", "file_size"}),
    "document_ready": frozenset({"page_count", "processing_ms"}),
    "document_processing_failed": frozenset({"error_code"}),
    "document_deleted": frozenset({"document_age_days"}),
    "question_submitted": frozenset({"question_length", "docs_selected_count"}),
    "answer_first_token": frozenset({"latency_ms"}),
    "answer_completed": frozenset({"total_ms", "citation_count", "grounded"}),
    "answer_failed": frozenset({"error_code", "stage"}),
    "answer_stopped": frozenset({"elapsed_ms"}),
    "citation_opened": frozenset({"citation_index"}),
    "answer_feedback": frozenset({"rating", "reason_code"}),
    "task_marked_done": frozenset({"task_id", "elapsed_ms", "success"}),
    "copy_answer": frozenset({"answer_id"}),
}
