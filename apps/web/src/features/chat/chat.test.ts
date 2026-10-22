import { describe, expect, it } from "vitest";
import type { ChatMessage } from "../../api/types";
import { chatReducer, initialChat, isLive, type ChatState } from "./chatReducer";
import { composerState, type ComposerInput } from "./composerState";
import { chatErrorText } from "./useChat";

const ai = (over: Partial<ChatMessage> = {}): ChatMessage => ({
  key: "a1",
  role: "ai",
  text: "",
  status: "sending",
  question: "q?",
  citations: [],
  feedback: null,
  ...over,
});
const user: ChatMessage = {
  key: "u1",
  role: "user",
  text: "q?",
  status: "complete",
  citations: [],
};
const start = (m: ChatMessage = ai()): ChatState =>
  chatReducer(initialChat, { type: "ask", user, ai: m });

describe("chatReducer — máy trạng thái tin nhắn AI", () => {
  it("ask thêm cặp câu hỏi + câu trả lời đang chờ", () => {
    const s = start();
    expect(s.messages.map((m) => m.role)).toEqual(["user", "ai"]);
    expect(isLive(s.messages[1] as ChatMessage)).toBe(true);
  });

  it("token đầu chuyển sending → streaming và nối chuỗi", () => {
    let s = start();
    s = chatReducer(s, { type: "token", key: "a1", text: "Xin " });
    s = chatReducer(s, { type: "token", key: "a1", text: "chào" });
    expect(s.messages[1]).toMatchObject({ status: "streaming", text: "Xin chào" });
  });

  it("done → complete kèm grounded; citations được lưu", () => {
    let s = start();
    s = chatReducer(s, { type: "token", key: "a1", text: "ok" });
    s = chatReducer(s, {
      type: "citations",
      key: "a1",
      citations: [{ id: "c", documentId: "d", documentName: "a.pdf", page: 2, valid: true }],
    });
    s = chatReducer(s, { type: "done", key: "a1", status: "complete", grounded: true });
    expect(s.messages[1]).toMatchObject({ status: "complete", grounded: true });
    expect(s.messages[1]?.citations).toHaveLength(1);
  });

  it("lỗi sau khi đã nhận chữ ⇒ interrupted và GIỮ phần đã nhận", () => {
    let s = start();
    s = chatReducer(s, { type: "token", key: "a1", text: "Phần đầu" });
    s = chatReducer(s, { type: "fail", key: "a1", errorCode: "LLM_TIMEOUT", errorText: "x" });
    expect(s.messages[1]).toMatchObject({
      status: "interrupted",
      text: "Phần đầu",
      errorCode: "LLM_TIMEOUT",
    });
  });

  it("lỗi khi chưa có chữ ⇒ failed; câu hỏi vẫn còn", () => {
    const s = chatReducer(start(), { type: "fail", key: "a1", errorCode: "NETWORK_ERROR" });
    expect(s.messages[1]?.status).toBe("failed");
    expect(s.messages[0]?.text).toBe("q?");
  });

  it("restart đưa về sending, xóa kết quả cũ nhưng giữ câu hỏi và clientMessageId", () => {
    let s = start(ai({ clientMessageId: "cm1" }));
    s = chatReducer(s, { type: "token", key: "a1", text: "x" });
    s = chatReducer(s, { type: "server_id", key: "a1", serverId: "srv" });
    s = chatReducer(s, { type: "fail", key: "a1", errorCode: "E" });
    s = chatReducer(s, { type: "restart", key: "a1" });
    expect(s.messages[1]).toMatchObject({
      status: "sending",
      text: "",
      question: "q?",
      clientMessageId: "cm1",
      serverId: undefined,
    });
  });

  it("token đến muộn sau khi đã kết thúc không làm đổi tin nhắn", () => {
    let s = start();
    s = chatReducer(s, { type: "done", key: "a1", status: "stopped", grounded: false });
    expect(chatReducer(s, { type: "token", key: "a1", text: "trễ" }).messages[1]?.text).toBe("");
  });

  it("feedback và reset", () => {
    const s = chatReducer(start(), { type: "feedback", key: "a1", value: "up" });
    expect(s.messages[1]?.feedback).toBe("up");
    expect(chatReducer(s, { type: "reset" })).toEqual(initialChat);
  });
});

const base: ComposerInput = {
  text: "Câu hỏi",
  noticeAccepted: true,
  qaEnabled: true,
  readyCount: 2,
  selectedCount: 1,
  maxQuestionLength: 2000,
  maxDocuments: 10,
  streaming: false,
};

describe("composerState — thứ tự ưu tiên khóa ô chat (SCR-02/04/08)", () => {
  it("bình thường: gửi được", () => expect(composerState(base)).toEqual({}));
  it("chưa xác nhận thông báo", () =>
    expect(composerState({ ...base, noticeAccepted: false })).toMatchObject({
      off: true,
      reason: expect.stringContaining("thông báo"),
    }));
  it("kill switch", () =>
    expect(composerState({ ...base, qaEnabled: false })).toMatchObject({
      off: true,
      reason: expect.stringContaining("không khả dụng"),
    }));
  it("chưa có tài liệu sẵn sàng", () =>
    expect(composerState({ ...base, readyCount: 0, selectedCount: 0 })).toMatchObject({
      off: true,
      reason: expect.stringContaining("Tải ít nhất 1 PDF"),
    }));
  it("không chọn tài liệu nào", () =>
    expect(composerState({ ...base, selectedCount: 0 })).toMatchObject({
      off: true,
      reason: expect.stringContaining("Chọn ít nhất 1"),
    }));
  it("chọn quá số tài liệu cho phép", () =>
    expect(composerState({ ...base, selectedCount: 11 })).toMatchObject({
      off: true,
      reason: expect.stringContaining("tối đa 10"),
    }));
  it("đang tạo câu trả lời ⇒ nút thành Dừng, ô nhập vẫn dùng được", () => {
    const s = composerState({ ...base, streaming: true });
    expect(s).toMatchObject({ stop: true, neutral: true });
    expect(s.off).toBeUndefined();
  });
  it("rỗng hoặc chỉ khoảng trắng ⇒ khóa nút Gửi, không khóa ô", () =>
    expect(composerState({ ...base, text: "   " })).toEqual({ sendOff: true }));
  it("quá dài ⇒ khóa Gửi kèm lý do", () =>
    expect(composerState({ ...base, text: "x".repeat(2001) })).toMatchObject({
      sendOff: true,
      reason: "Tối đa 2000 ký tự",
    }));
  it("kill switch ưu tiên hơn đang stream", () =>
    expect(composerState({ ...base, qaEnabled: false, streaming: true }).off).toBe(true));
});

describe("chatErrorText", () => {
  it("luôn là câu thân thiện, không lộ mã kỹ thuật", () => {
    for (const code of [
      "QA_DISABLED",
      "RATE_LIMITED",
      "NO_READY_DOCUMENTS",
      "DOCUMENT_NOT_READY",
      "QUESTION_TOO_LONG",
      "NETWORK_LOST",
      "LLM_TIMEOUT",
      "INTERNAL_ERROR",
    ]) {
      const t = chatErrorText(code, 7);
      expect(t.length).toBeGreaterThan(10);
      expect(t).not.toMatch(/[A-Z]{3,}_[A-Z]{3,}/);
    }
    expect(chatErrorText("RATE_LIMITED", 7)).toContain("7 giây");
    expect(chatErrorText("LLM_TIMEOUT")).toContain("Câu hỏi của bạn vẫn được giữ");
  });
});
