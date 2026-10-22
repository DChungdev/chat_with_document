import type { ApiCitation, ChatMessage } from "../../api/types";

export interface ChatState {
  conversationId: string | null;
  messages: ChatMessage[];
}

export const initialChat: ChatState = { conversationId: null, messages: [] };

export type ChatAction =
  | { type: "conversation"; id: string }
  | { type: "ask"; user: ChatMessage; ai: ChatMessage }
  | { type: "server_id"; key: string; serverId: string }
  | { type: "token"; key: string; text: string }
  | { type: "citations"; key: string; citations: ApiCitation[] }
  | { type: "done"; key: string; status: "complete" | "stopped"; grounded: boolean }
  | { type: "fail"; key: string; errorCode: string; errorText?: string }
  | { type: "restart"; key: string }
  | { type: "stopped_local"; key: string }
  | { type: "feedback"; key: string; value: "up" | "down" | null }
  | { type: "reset" };

function patch(state: ChatState, key: string, fn: (m: ChatMessage) => ChatMessage): ChatState {
  return { ...state, messages: state.messages.map((m) => (m.key === key ? fn(m) : m)) };
}

/** Máy trạng thái tin nhắn AI: sending → streaming → complete | interrupted | failed | stopped (Blueprint 3.7). */
export function chatReducer(state: ChatState, a: ChatAction): ChatState {
  switch (a.type) {
    case "reset":
      return initialChat;
    case "conversation":
      return { ...state, conversationId: a.id };
    case "ask":
      return { ...state, messages: [...state.messages, a.user, a.ai] };
    case "server_id":
      return patch(state, a.key, (m) => ({ ...m, serverId: a.serverId }));
    case "token":
      return patch(state, a.key, (m) =>
        m.status === "sending" || m.status === "streaming"
          ? { ...m, status: "streaming", text: m.text + a.text }
          : m,
      );
    case "citations":
      return patch(state, a.key, (m) => ({ ...m, citations: a.citations }));
    case "done":
      return patch(state, a.key, (m) => ({ ...m, status: a.status, grounded: a.grounded }));
    case "fail":
      // Đã nhận một phần ⇒ interrupted (giữ phần đó); chưa có gì ⇒ failed. Câu hỏi luôn được giữ.
      return patch(state, a.key, (m) => ({
        ...m,
        status: m.text ? "interrupted" : "failed",
        errorCode: a.errorCode,
        errorText: a.errorText,
      }));
    case "restart":
      return patch(state, a.key, (m) => ({
        ...m,
        status: "sending",
        text: "",
        citations: [],
        grounded: undefined,
        errorCode: undefined,
        errorText: undefined,
        feedback: null,
        serverId: undefined,
      }));
    case "stopped_local":
      return patch(state, a.key, (m) => ({ ...m, status: "stopped" }));
    case "feedback":
      return patch(state, a.key, (m) => ({ ...m, feedback: a.value }));
  }
}

export const isLive = (m: ChatMessage): boolean =>
  m.role === "ai" && (m.status === "sending" || m.status === "streaming");
