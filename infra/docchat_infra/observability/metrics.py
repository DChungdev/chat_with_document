"""Metrics Prometheus theo SAD 5.3. Nhãn chỉ gồm giá trị thuộc tập hữu hạn (không có nội dung)."""

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUEST_SECONDS = Histogram(
    "docchat_http_request_duration_seconds",
    "Độ trễ yêu cầu HTTP",
    ["method", "route", "status"],
    buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)
FIRST_TOKEN_SECONDS = Histogram(
    "docchat_answer_first_token_seconds",
    "Thời gian từ lúc gửi câu hỏi tới token đầu tiên (mục tiêu p95 ≤ 5s)",
    buckets=(0.25, 0.5, 1, 2, 3, 4, 5, 7.5, 10, 20),
)
INGEST_QUEUE_LENGTH = Gauge("docchat_ingest_queue_length", "Số job ingest đang chờ")
INGEST_SECONDS = Histogram(
    "docchat_ingest_duration_seconds",
    "Thời gian xử lý một PDF (mục tiêu ≤ 60s)",
    buckets=(1, 5, 10, 20, 30, 45, 60, 90, 120, 300),
)
STAGE_ERRORS = Counter(
    "docchat_stage_errors_total",
    "Lỗi theo giai đoạn (extract|chunk|embed|write|retrieve|llm)",
    ["stage"],
)
ANSWERS = Counter(
    "docchat_answers_total",
    "Câu trả lời đã hoàn tất, theo cờ grounded",
    ["grounded"],
)


class PrometheusChatMetrics:
    """Triển khai cổng `ChatMetrics` của lõi bằng metric Prometheus."""

    def first_token(self, seconds: float) -> None:
        FIRST_TOKEN_SECONDS.observe(seconds)

    def answer_finished(self, grounded: bool) -> None:
        ANSWERS.labels("true" if grounded else "false").inc()

    def stage_error(self, stage: str) -> None:
        STAGE_ERRORS.labels(stage).inc()
