import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { ApiError, NetworkError } from "../../api/client";
import { ev, fakeApi, sse } from "../../test/fakeApi";
import { SESSION, spyTracker } from "../../test/render";
import { AuthTestProvider } from "../../auth/AuthProvider";
import { TelemetryTestProvider } from "../../telemetry/TelemetryProvider";
import { ToastProvider } from "../../ui/Toasts";
import { useChat } from "./useChat";

function setup(apiOver: Parameters<typeof fakeApi>[0] = {}, docs = ["d1", "d2"]) {
  const api = fakeApi(apiOver);
  const tracker = spyTracker();
  const onKillSwitch = vi.fn();
  const onDocumentsStale = vi.fn();
  const wrapper = ({ children }: { children: ReactNode }) => (
    <ToastProvider>
      <AuthTestProvider api={api} session={SESSION}>
        <TelemetryTestProvider tracker={tracker}>{children}</TelemetryTestProvider>
      </AuthTestProvider>
    </ToastProvider>
  );
  const hook = renderHook(
    () => useChat({ api, getDocumentIds: () => docs, onKillSwitch, onDocumentsStale }),
    { wrapper },
  );
  return { api, tracker, hook, onKillSwitch, onDocumentsStale };
}

const goodStream = () =>
  sse(
    [
      ev("message", { messageId: "srv1", status: "streaming" }),
      ev("token", { text: "Thanh toán " }),
      ev("token", { text: "30 ngày." }),
      ev("citations", {
        citations: [
          { id: "c1", documentId: "d1", documentName: "baogia.pdf", page: 4, valid: true },
        ],
      }),
      ev("done", { messageId: "srv1", status: "complete", grounded: true, citationCount: 1 }),
    ],
    { chunkSize: 7 }, // cắt nhỏ để kiểm tra phân tách SSE xuyên qua nhiều chunk
  );

const lastAi = (h: ReturnType<typeof setup>["hook"]) => h.result.current.messages.at(-1);

describe("useChat", () => {
  it("hỏi → stream → hoàn tất với trích dẫn; phát đủ telemetry", async () => {
    const { api, tracker, hook } = setup({ ask: vi.fn(async () => goodStream()) });
    act(() => hook.result.current.ask("  Hạn thanh toán?  "));
    expect(hook.result.current.messages.map((m) => m.role)).toEqual(["user", "ai"]);
    expect(hook.result.current.messages[0]?.text).toBe("Hạn thanh toán?"); // đã cắt khoảng trắng

    await waitFor(() => expect(lastAi(hook)?.status).toBe("complete"));
    expect(lastAi(hook)).toMatchObject({
      text: "Thanh toán 30 ngày.",
      serverId: "srv1",
      grounded: true,
    });
    expect(lastAi(hook)?.citations[0]).toMatchObject({ documentName: "baogia.pdf", page: 4 });

    expect(api.createConversation).toHaveBeenCalledTimes(1);
    const [conv, body] = api.ask.mock.calls[0] as [
      string,
      { question: string; documentIds: string[]; clientMessageId: string },
    ];
    expect(conv).toBe("c1");
    expect(body).toMatchObject({ question: "Hạn thanh toán?", documentIds: ["d1", "d2"] });
    expect(body.clientMessageId).toMatch(/^[0-9a-f-]{36}$/);

    const names = tracker.events.map((e) => e.name);
    expect(names).toEqual(["question_submitted", "answer_first_token", "answer_completed"]);
    expect(tracker.events[0]?.props).toEqual({ question_length: 15, docs_selected_count: 2 });
    expect(tracker.events[2]?.props).toMatchObject({ citation_count: 1, grounded: true });
    expect(JSON.stringify(tracker.events)).not.toContain("Hạn thanh toán"); // không nội dung trong telemetry
  });

  it("dùng lại cùng hội thoại cho các câu hỏi sau", async () => {
    const { api, hook } = setup({ ask: vi.fn(async () => goodStream()) });
    act(() => hook.result.current.ask("một"));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("complete"));
    act(() => hook.result.current.ask("hai"));
    await waitFor(() => expect(hook.result.current.messages).toHaveLength(4));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("complete"));
    expect(api.createConversation).toHaveBeenCalledTimes(1);
  });

  it("không gửi câu hỏi rỗng", () => {
    const { api, hook } = setup();
    act(() => hook.result.current.ask("   "));
    expect(hook.result.current.messages).toEqual([]);
    expect(api.ask).not.toHaveBeenCalled();
  });

  it("sự kiện error giữa chừng ⇒ interrupted, giữ phần đã nhận, cho Tạo lại", async () => {
    const { hook, tracker } = setup({
      ask: vi.fn(async () =>
        sse([
          ev("message", { messageId: "s" }),
          ev("token", { text: "Phần đầu" }),
          ev("error", { code: "LLM_TIMEOUT", stage: "generate", retryable: true }),
        ]),
      ),
    });
    act(() => hook.result.current.ask("q"));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("interrupted"));
    expect(lastAi(hook)).toMatchObject({ text: "Phần đầu", errorCode: "LLM_TIMEOUT" });
    expect(tracker.events.at(-1)).toMatchObject({
      name: "answer_failed",
      props: { error_code: "LLM_TIMEOUT", stage: "streaming" },
    });
  });

  it("lỗi trước khi có chữ ⇒ failed với stage=generation", async () => {
    const { hook, tracker } = setup({
      ask: vi.fn(async () =>
        sse([
          ev("message", { messageId: "s" }),
          ev("error", { code: "LLM_UNAVAILABLE", stage: "generate", retryable: true }),
        ]),
      ),
    });
    act(() => hook.result.current.ask("q"));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("failed"));
    expect(tracker.events.at(-1)?.props).toMatchObject({ stage: "generation" });
  });

  it("luồng đứt đột ngột (mạng) ⇒ NETWORK_LOST, không treo ở streaming", async () => {
    const { hook } = setup({
      ask: vi.fn(async () =>
        sse([ev("message", { messageId: "s" }), ev("token", { text: "dở" })], { thenError: true }),
      ),
    });
    act(() => hook.result.current.ask("q"));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("interrupted"));
    expect(lastAi(hook)).toMatchObject({ text: "dở", errorCode: "NETWORK_LOST" });
  });

  it("luồng đóng mà không có done ⇒ coi là mất kết nối", async () => {
    const { hook } = setup({
      ask: vi.fn(async () => sse([ev("message", { messageId: "s" }), ev("token", { text: "x" })])),
    });
    act(() => hook.result.current.ask("q"));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("interrupted"));
    expect(lastAi(hook)?.errorCode).toBe("NETWORK_LOST");
  });

  it("lỗi HTTP trước stream: ánh xạ thông điệp, không mất câu hỏi", async () => {
    const { hook, onKillSwitch, onDocumentsStale } = setup({
      ask: vi.fn(async () => {
        throw new ApiError({ title: "x", status: 503, code: "QA_DISABLED" });
      }),
    });
    act(() => hook.result.current.ask("câu hỏi quan trọng"));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("failed"));
    expect(lastAi(hook)?.errorText).toContain("tạm thời không khả dụng");
    expect(hook.result.current.messages[0]?.text).toBe("câu hỏi quan trọng");
    expect(onKillSwitch).toHaveBeenCalled();
    expect(onDocumentsStale).not.toHaveBeenCalled();
  });

  it.each(["NO_READY_DOCUMENTS", "DOCUMENT_NOT_READY", "NOT_FOUND"])(
    "%s ⇒ yêu cầu làm mới danh sách tài liệu",
    async (code) => {
      const { hook, onDocumentsStale } = setup({
        ask: vi.fn(async () => {
          throw new ApiError({ title: "x", status: 409, code });
        }),
      });
      act(() => hook.result.current.ask("q"));
      await waitFor(() => expect(lastAi(hook)?.status).toBe("failed"));
      expect(onDocumentsStale).toHaveBeenCalled();
    },
  );

  it("RATE_LIMITED nêu số giây chờ", async () => {
    const { hook } = setup({
      ask: vi.fn(async () => {
        throw new ApiError({ title: "x", status: 429, code: "RATE_LIMITED" }, 9);
      }),
    });
    act(() => hook.result.current.ask("q"));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("failed"));
    expect(lastAi(hook)?.errorText).toContain("9 giây");
  });

  it("mất mạng khi gửi ⇒ failed + Thử lại gửi lại CÙNG clientMessageId, không nhân đôi câu hỏi", async () => {
    const ask = vi
      .fn()
      .mockRejectedValueOnce(new NetworkError())
      .mockImplementation(async () => goodStream());
    const { hook } = setup({ ask });
    act(() => hook.result.current.ask("q?"));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("failed"));
    const key = lastAi(hook)?.key as string;
    act(() => hook.result.current.retry(key));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("complete"));
    expect(hook.result.current.messages.filter((m) => m.role === "user")).toHaveLength(1);
    expect(ask.mock.calls[1]?.[1].clientMessageId).toBe(ask.mock.calls[0]?.[1].clientMessageId);
  });

  it("Tạo lại sau gián đoạn dùng endpoint regenerate theo serverId", async () => {
    const regenerate = vi.fn(async () =>
      sse([
        ev("message", { messageId: "srv2" }),
        ev("token", { text: "Mới" }),
        ev("citations", { citations: [] }),
        ev("done", { status: "complete", grounded: false, citationCount: 0 }),
      ]),
    );
    const { hook, api } = setup({
      regenerate,
      ask: vi.fn(async () =>
        sse([
          ev("message", { messageId: "srv1" }),
          ev("token", { text: "dở" }),
          ev("error", { code: "LLM_TIMEOUT" }),
        ]),
      ),
    });
    act(() => hook.result.current.ask("q"));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("interrupted"));
    act(() => hook.result.current.retry(lastAi(hook)?.key as string));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("complete"));
    expect(api.regenerate).toHaveBeenCalledWith("srv1", expect.any(AbortSignal));
    expect(lastAi(hook)).toMatchObject({ text: "Mới", serverId: "srv2" });
    expect(api.ask).toHaveBeenCalledTimes(1);
  });

  it("Dừng: gọi stop theo serverId, giữ phần đã nhận, đánh dấu stopped", async () => {
    let release!: () => void;
    const hold = new Promise<void>((r) => (release = r));
    const stopSpy = vi.fn(async () => release());
    const { hook, tracker } = setup({
      stop: stopSpy,
      ask: vi.fn(async () =>
        sse(
          [
            ev("message", { messageId: "srv1" }),
            ev("token", { text: "Một " }),
            ev("done", { messageId: "srv1", status: "stopped", grounded: false, citationCount: 0 }),
          ],
          { hold },
        ),
      ),
    });
    act(() => hook.result.current.ask("q"));
    await waitFor(() => expect(lastAi(hook)?.serverId).toBe("srv1"));
    expect(hook.result.current.live).toBe(true);
    act(() => hook.result.current.stop());
    expect(stopSpy).toHaveBeenCalledWith("srv1");
    await waitFor(() => expect(lastAi(hook)?.status).toBe("stopped"));
    expect(lastAi(hook)?.text).toContain("Một");
    expect(tracker.events.map((e) => e.name)).toContain("answer_stopped");
    expect(hook.result.current.live).toBe(false);
  });

  it("Dừng khi chưa có serverId: hủy kết nối phía client", async () => {
    const ask = vi.fn(
      (_c: string, _b: unknown, signal: AbortSignal) =>
        new Promise<Response>((_res, rej) =>
          signal.addEventListener("abort", () => rej(new DOMException("a", "AbortError"))),
        ),
    );
    const { hook, api } = setup({ ask });
    act(() => hook.result.current.ask("q"));
    await waitFor(() => expect(ask).toHaveBeenCalled());
    act(() => hook.result.current.stop());
    await waitFor(() => expect(lastAi(hook)?.status).toBe("stopped"));
    expect(api.stop).not.toHaveBeenCalled();
  });

  it("đánh giá: gọi API, phát telemetry không nội dung, bỏ chọn chỉ cục bộ", async () => {
    const { hook, api, tracker } = setup({ ask: vi.fn(async () => goodStream()) });
    act(() => hook.result.current.ask("q"));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("complete"));
    const key = lastAi(hook)?.key as string;
    act(() => hook.result.current.rate(key, "down"));
    expect(api.sendFeedback).toHaveBeenCalledWith("srv1", "down");
    expect(lastAi(hook)?.feedback).toBe("down");
    expect(tracker.events.at(-1)).toMatchObject({
      name: "answer_feedback",
      props: { rating: "down" },
    });
    act(() => hook.result.current.rate(key, "down")); // bấm lại ⇒ bỏ chọn
    expect(lastAi(hook)?.feedback).toBeNull();
    expect(api.sendFeedback).toHaveBeenCalledTimes(1);
  });

  it("đánh giá lỗi ⇒ hoàn tác trạng thái", async () => {
    const { hook } = setup({
      ask: vi.fn(async () => goodStream()),
      sendFeedback: vi.fn(async () => {
        throw new NetworkError();
      }),
    });
    act(() => hook.result.current.ask("q"));
    await waitFor(() => expect(lastAi(hook)?.status).toBe("complete"));
    act(() => hook.result.current.rate(lastAi(hook)?.key as string, "up"));
    await waitFor(() => expect(lastAi(hook)?.feedback).toBeNull());
  });

  it("task_marked_done tính thời gian từ câu hỏi đầu của tác vụ", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    const { hook, tracker } = setup({ ask: vi.fn(async () => goodStream()) });
    act(() => hook.result.current.ask("q"));
    vi.setSystemTime(Date.now() + 42_000);
    act(() => hook.result.current.markTaskDone(true));
    const e = tracker.events.at(-1);
    expect(e?.name).toBe("task_marked_done");
    expect(e?.props).toMatchObject({ success: true });
    expect(Number(e?.props.elapsed_ms)).toBeGreaterThanOrEqual(42_000);
    vi.useRealTimers();
  });
});
