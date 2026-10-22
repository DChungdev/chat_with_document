export interface ComposerInput {
  text: string;
  noticeAccepted: boolean;
  qaEnabled: boolean;
  readyCount: number;
  selectedCount: number;
  maxQuestionLength: number;
  maxDocuments: number;
  streaming: boolean;
}

export interface ComposerState {
  /** Ô nhập bị khóa. */
  off?: boolean;
  /** Nút Gửi bị khóa nhưng ô nhập còn dùng được. */
  sendOff?: boolean;
  /** Nút chuyển thành "Dừng". */
  stop?: boolean;
  reason?: string;
  neutral?: boolean;
}

/** Quy tắc bật/tắt ô chat, theo thứ tự ưu tiên của prototype (SCR-02/04/08). Hàm thuần để test. */
export function composerState(i: ComposerInput): ComposerState {
  if (!i.noticeAccepted) return { off: true, reason: "Xác nhận thông báo dữ liệu để bắt đầu" };
  if (!i.qaEnabled) return { off: true, reason: "Tính năng hỏi đáp tạm thời không khả dụng" };
  if (i.readyCount === 0)
    return { off: true, reason: "Tải ít nhất 1 PDF và chờ ở trạng thái Sẵn sàng" };
  if (i.selectedCount === 0) return { off: true, reason: "Chọn ít nhất 1 tài liệu để hỏi" };
  if (i.selectedCount > i.maxDocuments) {
    return { off: true, reason: `Chỉ chọn tối đa ${i.maxDocuments} tài liệu cho một câu hỏi` };
  }
  if (i.streaming) return { stop: true, reason: "Đang tạo câu trả lời…", neutral: true };
  if (!i.text.trim()) return { sendOff: true };
  if (i.text.length > i.maxQuestionLength)
    return { sendOff: true, reason: `Tối đa ${i.maxQuestionLength} ký tự` };
  return {};
}
