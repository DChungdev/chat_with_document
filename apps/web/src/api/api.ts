import { ApiError, HttpClient, NetworkError } from "./client";
import type {
  ApiCitation,
  ApiDocument,
  AppConfig,
  AskBody,
  DataNotice,
  LoginResult,
  MvpReport,
  TelemetryWire,
} from "./types";

/** Giao diện API cho UI — tách khỏi fetch để test thay bằng bản giả (src/test/fakeApi.ts). */
export interface Api {
  getConfig(): Promise<AppConfig>;
  getNotice(): Promise<DataNotice>;
  acceptNotice(version: string): Promise<void>;
  listDocuments(): Promise<ApiDocument[]>;
  uploadDocument(
    file: File,
    idempotencyKey: string,
    onProgress: (percent: number) => void,
    signal?: AbortSignal,
  ): Promise<ApiDocument>;
  deleteDocument(id: string): Promise<void>;
  createConversation(): Promise<{ id: string }>;
  ask(conversationId: string, body: AskBody, signal: AbortSignal): Promise<Response>;
  regenerate(messageId: string, signal: AbortSignal): Promise<Response>;
  stop(messageId: string): Promise<void>;
  getCitation(id: string): Promise<ApiCitation>;
  sendFeedback(messageId: string, rating: "up" | "down", reasonCode?: string): Promise<void>;
  sendTelemetry(events: TelemetryWire[], keepalive?: boolean): Promise<void>;
  mvpReport(): Promise<MvpReport>;
  devLogin(name: string, roles: string[]): Promise<LoginResult>;
}

interface Page {
  items: ApiDocument[];
  nextCursor: string | null;
}

export function createApi(
  http: HttpClient,
  xhrFactory: () => XMLHttpRequest = () => new XMLHttpRequest(),
  baseUrl = "/api/v1",
): Api {
  return {
    getConfig: () => http.json<AppConfig>("/config"),
    getNotice: () => http.json<DataNotice>("/data-notice"),
    acceptNotice: (version) =>
      http.postJson("/data-notice/acceptances", { version }).then(() => undefined),

    async listDocuments() {
      const all: ApiDocument[] = [];
      let cursor: string | null = null;
      do {
        const q: string = cursor ? `&cursor=${encodeURIComponent(cursor)}` : "";
        const page: Page = await http.json<Page>(`/documents?limit=100${q}`);
        all.push(...page.items);
        cursor = page.nextCursor;
      } while (cursor);
      return all;
    },

    // XHR thay cho fetch: fetch không có sự kiện tiến trình tải lên (cần cho thanh tiến trình, US-102).
    uploadDocument(file, idempotencyKey, onProgress, signal) {
      return new Promise<ApiDocument>((resolve, reject) => {
        const xhr = xhrFactory();
        xhr.open("POST", `${baseUrl}/documents`);
        for (const [k, v] of Object.entries(http.authHeaders())) xhr.setRequestHeader(k, v);
        xhr.setRequestHeader("Idempotency-Key", idempotencyKey);
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) onProgress(Math.round((100 * e.loaded) / e.total));
        };
        xhr.onload = () => {
          let body: unknown = null;
          try {
            body = JSON.parse(xhr.responseText);
          } catch {
            /* không phải JSON */
          }
          if (xhr.status >= 200 && xhr.status < 300) return resolve(body as ApiDocument);
          const p = (body ?? {}) as Partial<{
            code: string;
            title: string;
            detail: string;
            retryable: boolean;
          }>;
          const retryAfter = Number(xhr.getResponseHeader("retry-after")) || null;
          const err = new ApiError(
            {
              title: p.title ?? "Lỗi",
              status: xhr.status,
              code: p.code ?? "HTTP_ERROR",
              detail: p.detail,
              retryable: p.retryable,
            },
            retryAfter,
          );
          if (xhr.status === 401) http.signalUnauthorized();
          reject(err);
        };
        xhr.onerror = () => reject(new NetworkError());
        xhr.onabort = () => reject(new DOMException("aborted", "AbortError"));
        signal?.addEventListener("abort", () => xhr.abort());
        const form = new FormData();
        form.append("file", file);
        xhr.send(form);
      });
    },

    deleteDocument: (id) => http.send(`/documents/${id}`, { method: "DELETE" }),
    createConversation: () =>
      http.postJson("/conversations", {}).then((r) => r.json() as Promise<{ id: string }>),
    ask: (conversationId, body, signal) =>
      http.postJson(`/conversations/${conversationId}/messages`, body, { signal }),
    regenerate: (messageId, signal) =>
      http.postJson(`/messages/${messageId}/regenerate`, {}, { signal }),
    stop: (messageId) => http.postJson(`/messages/${messageId}/stop`, {}).then(() => undefined),
    getCitation: (id) => http.json<ApiCitation>(`/citations/${id}`),
    sendFeedback: (messageId, rating, reasonCode) =>
      http
        .postJson(
          `/messages/${messageId}/feedback`,
          { rating, reasonCode: reasonCode ?? null },
          { method: "PUT" },
        )
        .then(() => undefined),
    sendTelemetry: (events, keepalive) =>
      http.postJson("/telemetry/events", { events }, { keepalive }).then(() => undefined),
    mvpReport: () => http.json<MvpReport>("/reports/mvp-metrics"),
    devLogin: (name, roles) =>
      http.postJson("/dev/login", { name, roles }).then((r) => r.json() as Promise<LoginResult>),
  };
}
