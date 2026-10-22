import { useCallback, useEffect, useReducer, useRef } from "react";
import type { Api } from "../../api/api";
import { ApiError, NetworkError } from "../../api/client";
import { readSse } from "../../api/sse";
import type { ApiCitation, ChatMessage } from "../../api/types";
import { useTelemetry } from "../../telemetry/TelemetryProvider";
import { useToast } from "../../ui/Toasts";
import { uuid } from "../../ui/format";
import { chatReducer, initialChat, isLive } from "./chatReducer";

export interface ChatDeps {
  api: Api;
  /** Tài liệu đang được chọn để hỏi (id). */
  getDocumentIds(): string[];
  onKillSwitch(): void;
  onDocumentsStale(): void;
}

/** Thông báo thân thiện cho lỗi trước/trong khi stream (không bao giờ lộ chi tiết kỹ thuật). */
export function chatErrorText(code: string, retryAfter?: number | null): string {
  switch (code) {
    case "QA_DISABLED":
      return "Hỏi đáp đang tạm thời không khả dụng. Câu hỏi của bạn vẫn được giữ.";
    case "RATE_LIMITED":
      return `Bạn hỏi quá nhanh${retryAfter ? `, hãy thử lại sau ${retryAfter} giây` : ""}. Câu hỏi của bạn vẫn được giữ.`;
    case "NO_READY_DOCUMENTS":
      return "Chưa có tài liệu nào sẵn sàng. Hãy tải PDF lên và chờ trạng thái “Sẵn sàng”.";
    case "DOCUMENT_NOT_READY":
    case "NOT_FOUND":
      return "Một số tài liệu đã chọn không còn khả dụng. Hãy kiểm tra danh sách tài liệu rồi hỏi lại.";
    case "QUESTION_TOO_LONG":
      return "Câu hỏi quá dài. Hãy rút gọn rồi gửi lại.";
    case "REQUEST_IN_PROGRESS":
      return "Câu hỏi này đang được xử lý. Vui lòng đợi giây lát.";
    case "NETWORK_LOST":
    case "NETWORK_ERROR":
      return "Kết nối bị gián đoạn. Câu hỏi của bạn vẫn được giữ.";
    case "UNAUTHENTICATED":
    case "SESSION_EXPIRED":
      return "Phiên đã hết hạn. Hãy đăng nhập lại rồi thử lại — câu hỏi của bạn vẫn được giữ.";
    default:
      return "Chưa thể tạo câu trả lời lúc này. Câu hỏi của bạn vẫn được giữ.";
  }
}

export function useChat(deps: ChatDeps) {
  const { api } = deps;
  const tracker = useTelemetry();
  const notify = useToast();
  const [state, dispatch] = useReducer(chatReducer, initialChat);
  const stateRef = useRef(state);
  stateRef.current = state;
  const depsRef = useRef(deps);
  depsRef.current = deps;
  const controller = useRef<AbortController | null>(null);
  const stopRequested = useRef(false);
  const taskStart = useRef<number | null>(null); // MET-001: bắt đầu từ câu hỏi đầu tiên của một tác vụ

  useEffect(() => () => controller.current?.abort(), []);

  const ensureConversation = useCallback(async (): Promise<string> => {
    const existing = stateRef.current.conversationId;
    if (existing) return existing;
    const { id } = await api.createConversation();
    dispatch({ type: "conversation", id });
    stateRef.current = { ...stateRef.current, conversationId: id };
    return id;
  }, [api]);

  const runStream = useCallback(
    async (aiKey: string, start: (signal: AbortSignal) => Promise<Response>) => {
      const ctrl = new AbortController();
      controller.current = ctrl;
      stopRequested.current = false;
      const t0 = performance.now();
      let gotToken = false;
      let terminal = false;
      let citations = 0;
      let grounded = false;
      const fail = (code: string, extra?: string) => {
        terminal = true;
        dispatch({
          type: "fail",
          key: aiKey,
          errorCode: code,
          errorText: extra ?? chatErrorText(code),
        });
        tracker.track("answer_failed", {
          error_code: code,
          stage: gotToken ? "streaming" : "generation",
        });
      };

      try {
        const res = await start(ctrl.signal);
        if (!res.body) return fail("NETWORK_ERROR");
        for await (const ev of readSse(res.body)) {
          const d = ev.data as Record<string, unknown>;
          switch (ev.name) {
            case "message":
              dispatch({ type: "server_id", key: aiKey, serverId: String(d.messageId) });
              break;
            case "token": {
              if (!gotToken) {
                gotToken = true;
                tracker.track("answer_first_token", {
                  latency_ms: Math.round(performance.now() - t0),
                });
              }
              const piece = String(d.text ?? "");
              dispatch({ type: "token", key: aiKey, text: piece });
              break;
            }
            case "citations": {
              const list = (d.citations as ApiCitation[]) ?? [];
              citations = list.length;
              dispatch({ type: "citations", key: aiKey, citations: list });
              break;
            }
            case "done": {
              terminal = true;
              grounded = Boolean(d.grounded);
              const status = d.status === "stopped" ? "stopped" : "complete";
              dispatch({ type: "done", key: aiKey, status, grounded });
              if (status === "stopped")
                tracker.track("answer_stopped", { elapsed_ms: Math.round(performance.now() - t0) });
              else
                tracker.track("answer_completed", {
                  total_ms: Math.round(performance.now() - t0),
                  citation_count: Number(d.citationCount ?? citations),
                  grounded,
                });
              break;
            }
            case "error": {
              const code = String(d.code ?? "UNKNOWN");
              if (code === "QA_DISABLED") depsRef.current.onKillSwitch();
              fail(code);
              break;
            }
            default: // "ping" và sự kiện lạ: bỏ qua
          }
        }
        if (!terminal) fail("NETWORK_LOST"); // luồng đóng mà không có done/error ⇒ mất kết nối
      } catch (e) {
        if (terminal) return;
        if (e instanceof DOMException && e.name === "AbortError") {
          if (stopRequested.current) {
            dispatch({ type: "stopped_local", key: aiKey });
            tracker.track("answer_stopped", { elapsed_ms: Math.round(performance.now() - t0) });
          }
          return; // hủy do rời trang: không báo lỗi
        }
        if (e instanceof ApiError) {
          if (e.code === "QA_DISABLED") depsRef.current.onKillSwitch();
          if (["DOCUMENT_NOT_READY", "NOT_FOUND", "NO_READY_DOCUMENTS"].includes(e.code))
            depsRef.current.onDocumentsStale();
          return fail(e.code, chatErrorText(e.code, e.retryAfter));
        }
        fail(e instanceof NetworkError ? "NETWORK_ERROR" : "NETWORK_LOST"); // đứt giữa chừng khi đang đọc
      } finally {
        if (controller.current === ctrl) controller.current = null;
      }
    },
    [tracker],
  );

  const send = useCallback(
    async (question: string, ai: ChatMessage) => {
      const docs = depsRef.current.getDocumentIds();
      await runStream(ai.key, async (signal) => {
        const conv = await ensureConversation();
        return api.ask(
          conv,
          { question, documentIds: docs, clientMessageId: ai.clientMessageId ?? uuid() },
          signal,
        );
      });
    },
    [api, ensureConversation, runStream],
  );

  const ask = useCallback(
    (raw: string) => {
      const question = raw.trim();
      if (!question) return;
      if (taskStart.current === null) taskStart.current = Date.now();
      const clientMessageId = uuid();
      const user: ChatMessage = {
        key: uuid(),
        role: "user",
        text: question,
        status: "complete",
        citations: [],
      };
      const ai: ChatMessage = {
        key: uuid(),
        role: "ai",
        text: "",
        status: "sending",
        question,
        clientMessageId,
        citations: [],
        feedback: null,
      };
      dispatch({ type: "ask", user, ai });
      tracker.track("question_submitted", {
        question_length: question.length,
        docs_selected_count: depsRef.current.getDocumentIds().length,
      });
      void send(question, ai);
    },
    [send, tracker],
  );

  /** "Tạo lại" / "Thử lại" / "Hỏi lại": cùng câu hỏi, không tạo thêm bong bóng câu hỏi. */
  const retry = useCallback(
    (key: string) => {
      const m = stateRef.current.messages.find((x) => x.key === key);
      if (!m || m.role !== "ai" || isLive(m)) return;
      const serverId = m.serverId;
      dispatch({ type: "restart", key });
      if (serverId) {
        void runStream(key, (signal) => api.regenerate(serverId, signal));
      } else if (m.question) {
        void send(m.question, { ...m, clientMessageId: m.clientMessageId });
      }
    },
    [api, runStream, send],
  );

  const stop = useCallback(() => {
    const live = stateRef.current.messages.find(isLive);
    if (!live) return;
    stopRequested.current = true;
    if (live.serverId) {
      // Server kết thúc luồng bằng `done` (status=stopped) và giữ phần đã nhận; nếu yêu cầu dừng không
      // tới được, hủy kết nối phía client để người dùng không phải chờ.
      api.stop(live.serverId).catch(() => controller.current?.abort());
    } else {
      controller.current?.abort();
    }
  }, [api]);

  const rate = useCallback(
    (key: string, value: "up" | "down") => {
      const m = stateRef.current.messages.find((x) => x.key === key);
      if (!m?.serverId) return;
      const next = m.feedback === value ? null : value;
      dispatch({ type: "feedback", key, value: next });
      if (!next) return; // bỏ chọn chỉ là trạng thái cục bộ
      tracker.track("answer_feedback", { rating: next });
      api.sendFeedback(m.serverId, next).then(
        () => notify("success", "Cảm ơn phản hồi của bạn."),
        () => {
          dispatch({ type: "feedback", key, value: m.feedback ?? null }); // hoàn tác khi lưu lỗi
          notify("danger", "Chưa ghi nhận được phản hồi. Hãy thử lại.", true);
        },
      );
    },
    [api, notify, tracker],
  );

  const markTaskDone = useCallback(
    (success: boolean) => {
      const start = taskStart.current ?? Date.now();
      tracker.track("task_marked_done", {
        task_id: uuid(),
        elapsed_ms: Date.now() - start,
        success,
      });
      taskStart.current = null;
      notify("success", "Đã ghi nhận. Cảm ơn bạn!");
    },
    [notify, tracker],
  );

  const live = state.messages.some(isLive);
  return { ...state, live, ask, retry, stop, rate, markTaskDone };
}
