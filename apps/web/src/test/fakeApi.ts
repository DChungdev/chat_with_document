import { vi } from "vitest";
import type { Api } from "../api/api";
import type { ApiDocument, AppConfig } from "../api/types";

export const CONFIG: AppConfig = {
  qaEnabled: true,
  maxFileSizeBytes: 20 * 1024 * 1024,
  maxFiles: 50,
  maxQuestionLength: 2000,
  maxDocumentsPerQuestion: 10,
  acceptedTypes: ["application/pdf"],
  noticeVersion: "v1",
  noticeAccepted: true,
};

export function doc(over: Partial<ApiDocument> = {}): ApiDocument {
  return {
    id: "d1",
    name: "baogia.pdf",
    sizeBytes: 1_258_000,
    uploadedAt: new Date(Date.now() - 120_000).toISOString(),
    status: "ready",
    pageCount: 5,
    errorCode: null,
    ...over,
  };
}

/** Api giả: mọi phương thức là vi.fn có hành vi mặc định hợp lý; test ghi đè từng phần. */
export function fakeApi(
  over: Partial<Record<keyof Api, unknown>> = {},
): Api & { [K in keyof Api]: ReturnType<typeof vi.fn> } {
  const api = {
    getConfig: vi.fn(async () => ({ ...CONFIG })),
    getNotice: vi.fn(async () => ({
      version: "v1",
      content: "Nội dung thông báo",
      accepted: true,
    })),
    acceptNotice: vi.fn(async () => undefined),
    listDocuments: vi.fn(async () => [] as ApiDocument[]),
    uploadDocument: vi.fn(async (file: File) =>
      doc({ id: "up1", name: file.name, status: "processing", pageCount: null }),
    ),
    deleteDocument: vi.fn(async () => undefined),
    createConversation: vi.fn(async () => ({ id: "c1" })),
    ask: vi.fn(async () => sse([])),
    regenerate: vi.fn(async () => sse([])),
    stop: vi.fn(async () => undefined),
    getCitation: vi.fn(async () => ({
      id: "x",
      documentId: "d1",
      documentName: "baogia.pdf",
      page: 2,
      snippet: "Đoạn gốc",
      valid: true,
    })),
    sendFeedback: vi.fn(async () => undefined),
    sendTelemetry: vi.fn(async () => undefined),
    mvpReport: vi.fn(),
    devLogin: vi.fn(),
    ...over,
  };
  return api as never;
}

export interface Ev {
  name: string;
  data: unknown;
}
export const ev = (name: string, data: unknown = {}): Ev => ({ name, data });

/**
 * Response SSE từ danh sách sự kiện. `chunkSize` cắt nhỏ thân để kiểm tra phân tách tại mọi ranh giới.
 * `hold`: giữ lại sự kiện CUỐI cho tới khi promise này resolve (mô phỏng câu trả lời đang chạy dở).
 */
export function sse(
  events: Ev[],
  opts: { chunkSize?: number; thenError?: boolean; hold?: Promise<void> } = {},
): Response {
  const enc = new TextEncoder();
  const encode = (list: Ev[]) =>
    enc.encode(
      list
        .map(
          (e) => `event: ${e.name}
data: ${JSON.stringify(e.data)}

`,
        )
        .join(""),
    );
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const chunks: (Uint8Array | Promise<Uint8Array>)[] = [];
      if (opts.hold && events.length > 1) {
        chunks.push(encode(events.slice(0, -1)));
        chunks.push(opts.hold.then(() => encode(events.slice(-1))));
      } else {
        const bytes = encode(events);
        const size = opts.chunkSize ?? Math.max(bytes.length, 1);
        for (let i = 0; i < bytes.length; i += size) chunks.push(bytes.slice(i, i + size));
      }
      for (const c of chunks) controller.enqueue(await c);
      if (opts.thenError) {
        await new Promise((r) => setTimeout(r, 20)); // để người đọc kịp nhận dữ liệu đã gửi trước khi đứt
        controller.error(new TypeError("network error"));
      } else controller.close();
    },
  });
  return new Response(stream, { status: 200, headers: { "content-type": "text/event-stream" } });
}

export function problem(
  status: number,
  code: string,
  extra: Record<string, unknown> = {},
  headers: Record<string, string> = {},
): Response {
  return new Response(
    JSON.stringify({ title: "Lỗi", status, code, detail: "chi tiết", retryable: false, ...extra }),
    {
      status,
      headers: { "content-type": "application/problem+json", ...headers },
    },
  );
}

export const wait = (ms = 0) => new Promise((r) => setTimeout(r, ms));
