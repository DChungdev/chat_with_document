"""Lỗi theo RFC 7807 (`application/problem+json`) — API_Design 3.4.6.

`detail` không bao giờ chứa nội dung người dùng: lỗi validate của FastAPI KHÔNG được phản chiếu
giá trị đầu vào.
"""

from __future__ import annotations

import logging
import re

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from docchat_core.domain.errors import DomainError, RateLimited

logger = logging.getLogger("docchat.api")

STATUS_BY_CODE: dict[str, int] = {
    "VALIDATION_ERROR": 400,
    "INVALID_FILE_TYPE": 400,
    "UNAUTHENTICATED": 401,
    "SESSION_EXPIRED": 401,
    "NOTICE_NOT_ACCEPTED": 403,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "LIMIT_EXCEEDED": 409,
    "DOCUMENT_NOT_READY": 409,
    "NOTICE_VERSION_MISMATCH": 409,
    "REQUEST_IN_PROGRESS": 409,
    "INVALID_STATE": 409,
    "FILE_TOO_LARGE": 413,
    "QUESTION_TOO_LONG": 413,
    "NO_READY_DOCUMENTS": 422,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500,
    "LLM_UNAVAILABLE": 502,
    "LLM_TIMEOUT": 504,
    "QA_DISABLED": 503,
}

TITLES: dict[int, str] = {
    400: "Yêu cầu không hợp lệ",
    401: "Chưa xác thực",
    403: "Không được phép",
    404: "Không tìm thấy",
    405: "Phương thức không được hỗ trợ",
    409: "Xung đột trạng thái",
    413: "Dữ liệu vượt giới hạn",
    422: "Không thể xử lý",
    429: "Quá nhiều yêu cầu",
    500: "Lỗi hệ thống",
    502: "Dịch vụ AI không khả dụng",
    503: "Dịch vụ tạm thời không khả dụng",
    504: "Dịch vụ AI quá thời gian",
}


def problem(
    request: Request,
    status: int,
    code: str,
    detail: str,
    *,
    retryable: bool = False,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    slug = re.sub(r"_", "-", code.lower())
    body = {
        "type": f"https://docs.example/errors/{slug}",
        "title": TITLES.get(status, "Lỗi"),
        "status": status,
        "code": code,
        "detail": detail,
        "retryable": retryable,
        "requestId": getattr(request.state, "request_id", None),
    }
    return JSONResponse(
        body, status_code=status, media_type="application/problem+json", headers=headers
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError) -> JSONResponse:
        status = STATUS_BY_CODE.get(exc.code, 500)
        headers = None
        if isinstance(exc, RateLimited):
            headers = {"Retry-After": str(exc.retry_after_seconds)}
        if status == 401:
            headers = {"WWW-Authenticate": "Bearer"}
        return problem(
            request, status, exc.code, exc.detail, retryable=exc.retryable, headers=headers
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Chỉ nêu TÊN trường lỗi, không phản chiếu giá trị người dùng gửi.
        fields = sorted({str(e["loc"][-1]) for e in exc.errors() if e.get("loc")})
        detail = "Dữ liệu không hợp lệ" + (f" ở: {', '.join(fields)}." if fields else ".")
        return problem(request, 400, "VALIDATION_ERROR", detail)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return problem(request, exc.status_code, code, TITLES.get(exc.status_code, "Lỗi"))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled exception",
            extra={
                "event": "unhandled",
                "exc_type": type(exc).__name__,
                "error_code": "INTERNAL_ERROR",
            },
        )
        return problem(request, 500, "INTERNAL_ERROR", "Đã xảy ra lỗi hệ thống.", retryable=True)
