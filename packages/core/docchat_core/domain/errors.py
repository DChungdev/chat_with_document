"""Lỗi miền. Mỗi lỗi có `code` ổn định; tầng API ánh xạ `code` sang HTTP (API_Design mục 3.4.6).

`detail` hiển thị cho người dùng nên KHÔNG được chứa nội dung tài liệu/câu hỏi.
"""

from __future__ import annotations


class DomainError(Exception):
    code = "INTERNAL_ERROR"
    retryable = False
    default_detail = "Đã xảy ra lỗi."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.code)  # thông điệp ngoại lệ chỉ là mã, tránh lọt vào log


class ValidationFailed(DomainError):
    code = "VALIDATION_ERROR"
    default_detail = "Dữ liệu gửi lên không hợp lệ."


class Unauthenticated(DomainError):
    code = "UNAUTHENTICATED"
    default_detail = "Cần đăng nhập."


class SessionExpired(Unauthenticated):
    code = "SESSION_EXPIRED"
    default_detail = "Phiên đăng nhập đã hết hạn."


class Forbidden(DomainError):
    code = "FORBIDDEN"
    default_detail = "Bạn không có quyền thực hiện thao tác này."


class NoticeNotAccepted(DomainError):
    code = "NOTICE_NOT_ACCEPTED"
    default_detail = "Cần xác nhận thông báo sử dụng dữ liệu trước khi tiếp tục."


class NoticeVersionMismatch(DomainError):
    code = "NOTICE_VERSION_MISMATCH"
    default_detail = "Phiên bản thông báo đã thay đổi, vui lòng đọc lại."


class NotFound(DomainError):
    """Không tồn tại HOẶC thuộc người khác — không phân biệt (US-402)."""

    code = "NOT_FOUND"
    default_detail = "Không tìm thấy."


class InvalidFileType(DomainError):
    code = "INVALID_FILE_TYPE"
    default_detail = "Chỉ hỗ trợ tệp PDF."


class FileTooLarge(DomainError):
    code = "FILE_TOO_LARGE"
    default_detail = "Tệp vượt quá giới hạn kích thước."


class LimitExceeded(DomainError):
    code = "LIMIT_EXCEEDED"
    default_detail = "Đã vượt quá số tệp cho phép."


class QuestionTooLong(DomainError):
    code = "QUESTION_TOO_LONG"
    default_detail = "Câu hỏi quá dài."


class DocumentNotReady(DomainError):
    code = "DOCUMENT_NOT_READY"
    default_detail = "Có tài liệu chưa sẵn sàng."


class NoReadyDocuments(DomainError):
    code = "NO_READY_DOCUMENTS"
    default_detail = "Chưa có tài liệu nào sẵn sàng. Hãy tải PDF lên trước."


class RequestInProgress(DomainError):
    code = "REQUEST_IN_PROGRESS"
    default_detail = "Yêu cầu này đang được xử lý."


class QaDisabled(DomainError):
    code = "QA_DISABLED"
    default_detail = "Tính năng hỏi đáp đang tạm tắt."


class RateLimited(DomainError):
    code = "RATE_LIMITED"
    retryable = True
    default_detail = "Bạn thao tác quá nhanh, vui lòng thử lại sau."

    def __init__(self, retry_after_seconds: int, detail: str | None = None) -> None:
        super().__init__(detail)
        self.retry_after_seconds = max(1, int(retry_after_seconds))


class InvalidTransition(DomainError):
    code = "INVALID_STATE"
    default_detail = "Trạng thái hiện tại không cho phép thao tác này."


class AnswerFailed(DomainError):
    """Lỗi trong pipeline trả lời (LLM/retrieval); mang `stage` để UI và metric phân loại."""

    code = "LLM_UNAVAILABLE"
    retryable = True
    default_detail = "Dịch vụ AI tạm thời không khả dụng."

    def __init__(
        self,
        code: str = "LLM_UNAVAILABLE",
        stage: str = "generate",
        retryable: bool = True,
    ) -> None:
        super().__init__()
        self.code = code
        self.stage = stage
        self.retryable = retryable
