import { ApiError, NetworkError } from "../../api/client";
import { fmtSize } from "../../ui/format";

/** Lý do tài liệu `error` hiển thị cho người dùng (mã lấy từ worker, API_Design 3.4.1). */
export function documentErrorText(code: string | null): string {
  switch (code) {
    case "PDF_PASSWORD":
      return "PDF có mật khẩu";
    case "PDF_CORRUPT":
      return "PDF bị hỏng";
    case "NO_TEXT":
      return "PDF quét, không có chữ để đọc";
    case "PDF_TOO_MANY_PAGES":
      return "PDF quá nhiều trang";
    case "PDF_TOO_COMPLEX":
      return "PDF quá phức tạp";
    default:
      return "Xử lý không thành công";
  }
}

export function documentErrorAdvice(code: string | null): string {
  switch (code) {
    case "PDF_PASSWORD":
      return "Hãy gỡ mật khẩu rồi tải lại.";
    case "NO_TEXT":
      return "Hiện chưa hỗ trợ PDF quét (không có lớp văn bản).";
    case "PDF_CORRUPT":
      return "Hãy kiểm tra tệp rồi tải lại.";
    case "PDF_TOO_MANY_PAGES":
      return "Hãy tách tệp thành các phần nhỏ hơn.";
    default:
      return "Hãy thử tải lại. Nếu vẫn lỗi, hãy báo cho quản trị viên.";
  }
}

/** Thông báo cho lỗi tải lên; `retryable` quyết định có hiện nút "Thử lại" không. */
export function uploadErrorMessage(
  e: unknown,
  name: string,
  maxBytes: number,
): { text: string; retryable: boolean } {
  if (e instanceof NetworkError) return { text: `Mất kết nối khi tải “${name}”.`, retryable: true };
  if (e instanceof ApiError) {
    switch (e.code) {
      case "FILE_TOO_LARGE":
        return {
          text: `“${name}” vượt giới hạn ${fmtSize(maxBytes)}. Hãy chọn tệp nhỏ hơn.`,
          retryable: false,
        };
      case "INVALID_FILE_TYPE":
        return {
          text: `“${name}” không phải PDF hợp lệ. Hiện chỉ hỗ trợ tệp .pdf.`,
          retryable: false,
        };
      case "LIMIT_EXCEEDED":
        return { text: "Đã đạt số tài liệu tối đa. Xóa bớt để tải thêm.", retryable: false };
      case "RATE_LIMITED":
        return {
          text: `Bạn tải lên quá nhanh${e.retryAfter ? `, thử lại sau ${e.retryAfter} giây` : ""}.`,
          retryable: true,
        };
      case "NOTICE_NOT_ACCEPTED":
        return { text: "Cần xác nhận thông báo dữ liệu trước khi tải tài liệu.", retryable: false };
      default:
        return { text: `Không tải được “${name}”. ${e.detail}`, retryable: e.retryable };
    }
  }
  return { text: `Không tải được “${name}”.`, retryable: true };
}
