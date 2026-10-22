import { describe, expect, it, vi } from "vitest";
import { createApi } from "./api";
import { ApiError, HttpClient, NetworkError } from "./client";
import { readSse, type SseEvent } from "./sse";

function stream(chunks: string[]): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  let i = 0;
  return new ReadableStream({
    pull(c) {
      if (i < chunks.length) c.enqueue(enc.encode(chunks[i++]));
      else c.close();
    },
  });
}
async function collect(s: ReadableStream<Uint8Array>): Promise<SseEvent[]> {
  const out: SseEvent[] = [];
  for await (const e of readSse(s)) out.push(e);
  return out;
}

describe("readSse", () => {
  const full =
    'event: message\ndata: {"messageId":"m1"}\n\nevent: token\ndata: {"text":"Xin chào"}\n\n';

  it("đọc các sự kiện có tên và dữ liệu JSON", async () => {
    expect(await collect(stream([full]))).toEqual([
      { name: "message", data: { messageId: "m1" } },
      { name: "token", data: { text: "Xin chào" } },
    ]);
  });

  it("đúng khi luồng bị cắt tại BẤT KỲ byte nào (kể cả giữa ký tự tiếng Việt)", async () => {
    const bytes = new TextEncoder().encode(full);
    for (let cut = 1; cut < bytes.length; cut++) {
      const parts = [bytes.slice(0, cut), bytes.slice(cut)];
      const s = new ReadableStream<Uint8Array>({
        start(c) {
          parts.forEach((p) => c.enqueue(p));
          c.close();
        },
      });
      const events = await collect(s);
      expect(
        events.map((e) => e.name),
        `cắt tại ${cut}`,
      ).toEqual(["message", "token"]);
      expect((events[1]?.data as { text: string }).text).toBe("Xin chào");
    }
  });

  it("chấp nhận CRLF, chú thích và bỏ qua khối không có dữ liệu", async () => {
    const text = ': ping\r\n\r\nevent: token\r\ndata: {"text":"a"}\r\n\r\nevent: x\r\n\r\n';
    expect(await collect(stream([text]))).toEqual([{ name: "token", data: { text: "a" } }]);
  });

  it("bỏ qua JSON hỏng thay vì làm sập luồng", async () => {
    const text = 'event: token\ndata: {hỏng\n\nevent: token\ndata: {"text":"ok"}\n\n';
    expect(await collect(stream([text]))).toEqual([{ name: "token", data: { text: "ok" } }]);
  });

  it("gộp nhiều dòng data và đọc khối cuối không có dòng trống kết thúc", async () => {
    expect(
      await collect(stream(['event: a\ndata: {"x":\ndata: 1}\n\n', 'event: b\ndata: {"y":2}'])),
    ).toEqual([
      { name: "a", data: { x: 1 } },
      { name: "b", data: { y: 2 } },
    ]);
  });
});

const problemBody = (code: string, extra = {}) =>
  JSON.stringify({
    title: "Lỗi",
    status: 400,
    code,
    detail: "Chi tiết an toàn",
    retryable: true,
    ...extra,
  });

describe("HttpClient", () => {
  const make = (fetchImpl: typeof fetch, token: string | null = "tok") => {
    const onUnauthorized = vi.fn();
    return {
      onUnauthorized,
      http: new HttpClient({ getToken: () => token, onUnauthorized, fetchImpl }),
    };
  };

  it("gắn Bearer token và trả JSON", async () => {
    const f = vi.fn(async () => new Response('{"ok":true}', { status: 200 }));
    const { http } = make(f as never);
    expect(await http.json("/config")).toEqual({ ok: true });
    expect(f).toHaveBeenCalledWith(
      "/api/v1/config",
      expect.objectContaining({ headers: { Authorization: "Bearer tok" } }),
    );
  });

  it("chuyển problem+json thành ApiError (mã, trạng thái, retryable, Retry-After)", async () => {
    const f = async () =>
      new Response(problemBody("RATE_LIMITED"), {
        status: 429,
        headers: { "retry-after": "12", "content-type": "application/problem+json" },
      });
    const { http } = make(f as never);
    const err = (await http.json("/x").catch((e: unknown) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect([err.status, err.code, err.retryable, err.retryAfter, err.detail]).toEqual([
      429,
      "RATE_LIMITED",
      true,
      12,
      "Chi tiết an toàn",
    ]);
  });

  it("401 báo hết phiên; token rỗng vẫn ném lỗi", async () => {
    const f = async () => new Response(problemBody("SESSION_EXPIRED"), { status: 401 });
    const { http, onUnauthorized } = make(f as never);
    await expect(http.json("/x")).rejects.toMatchObject({ code: "SESSION_EXPIRED" });
    expect(onUnauthorized).toHaveBeenCalledTimes(1);
  });

  it("thân lỗi không phải JSON (lỗi từ proxy) vẫn thành ApiError an toàn", async () => {
    const f = async () =>
      new Response("<html>502</html>", { status: 502, statusText: "Bad Gateway" });
    const { http } = make(f as never);
    await expect(http.json("/x")).rejects.toMatchObject({ status: 502, code: "HTTP_ERROR" });
  });

  it("mất mạng ⇒ NetworkError; hủy chủ động ⇒ giữ nguyên AbortError", async () => {
    const { http } = make((async () => {
      throw new TypeError("Failed to fetch");
    }) as never);
    await expect(http.json("/x")).rejects.toBeInstanceOf(NetworkError);
    const { http: h2 } = make((async () => {
      throw new DOMException("aborted", "AbortError");
    }) as never);
    await expect(h2.json("/x")).rejects.toMatchObject({ name: "AbortError" });
  });
});

describe("createApi", () => {
  it("listDocuments gom mọi trang theo cursor", async () => {
    const pages = [
      { items: [{ id: "a" }], nextCursor: "c1" },
      { items: [{ id: "b" }], nextCursor: null },
    ];
    const f = vi.fn(async () => new Response(JSON.stringify(pages.shift()), { status: 200 }));
    const api = createApi(
      new HttpClient({
        getToken: () => "t",
        onUnauthorized: () => undefined,
        fetchImpl: f as never,
      }),
    );
    expect((await api.listDocuments()).map((d) => d.id)).toEqual(["a", "b"]);
    expect((f.mock.calls[1] as unknown[] | undefined)?.[0]).toBe(
      "/api/v1/documents?limit=100&cursor=c1",
    );
  });

  it("gửi phản hồi bằng PUT với mã lý do (không văn bản tự do)", async () => {
    const f = vi.fn(async () => new Response(null, { status: 204 }));
    const api = createApi(
      new HttpClient({
        getToken: () => "t",
        onUnauthorized: () => undefined,
        fetchImpl: f as never,
      }),
    );
    await api.sendFeedback("m1", "down", "wrong_answer");
    const [url, init] = f.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/v1/messages/m1/feedback");
    expect(init.method).toBe("PUT");
    expect(JSON.parse(init.body as string)).toEqual({ rating: "down", reasonCode: "wrong_answer" });
  });

  it("tải lên qua XHR có tiến trình, Idempotency-Key và Bearer", async () => {
    class FakeXhr {
      headers: Record<string, string> = {};
      upload: { onprogress?: (e: ProgressEvent) => void } = {};
      onload?: () => void;
      onerror?: () => void;
      onabort?: () => void;
      status = 202;
      responseText = JSON.stringify({ id: "d1", name: "a.pdf" });
      opened: [string, string] = ["", ""];
      body: unknown;
      open(m: string, u: string) {
        this.opened = [m, u];
      }
      setRequestHeader(k: string, v: string) {
        this.headers[k] = v;
      }
      getResponseHeader() {
        return null;
      }
      abort() {
        this.onabort?.();
      }
      send(b: unknown) {
        this.body = b;
        this.upload.onprogress?.({
          lengthComputable: true,
          loaded: 50,
          total: 100,
        } as ProgressEvent);
        this.onload?.();
      }
    }
    const xhr = new FakeXhr();
    const api = createApi(
      new HttpClient({ getToken: () => "tok", onUnauthorized: () => undefined }),
      () => xhr as never,
    );
    const seen: number[] = [];
    const doc = await api.uploadDocument(new File(["%PDF-"], "a.pdf"), "key-1", (p) =>
      seen.push(p),
    );
    expect(doc).toMatchObject({ id: "d1" });
    expect(seen).toEqual([50]);
    expect(xhr.opened).toEqual(["POST", "/api/v1/documents"]);
    expect(xhr.headers).toMatchObject({ Authorization: "Bearer tok", "Idempotency-Key": "key-1" });
    expect(xhr.body).toBeInstanceOf(FormData);
  });

  it("tải lên lỗi: ánh xạ problem+json và báo 401", async () => {
    const unauthorized = vi.fn();
    const mk = (status: number, code: string) => ({
      headers: {} as Record<string, string>,
      upload: {},
      status,
      responseText: problemBody(code, { status }),
      onload: undefined as undefined | (() => void),
      open() {},
      setRequestHeader() {},
      getResponseHeader: () => null,
      abort() {},
      send() {
        this.onload?.();
      },
    });
    const api = createApi(
      new HttpClient({ getToken: () => "t", onUnauthorized: unauthorized }),
      () => mk(413, "FILE_TOO_LARGE") as never,
    );
    await expect(
      api.uploadDocument(new File(["x"], "a.pdf"), "k", () => undefined),
    ).rejects.toMatchObject({ code: "FILE_TOO_LARGE", status: 413 });
    const api2 = createApi(
      new HttpClient({ getToken: () => "t", onUnauthorized: unauthorized }),
      () => mk(401, "SESSION_EXPIRED") as never,
    );
    await expect(
      api2.uploadDocument(new File(["x"], "a.pdf"), "k", () => undefined),
    ).rejects.toMatchObject({ status: 401 });
    expect(unauthorized).toHaveBeenCalledTimes(1);
  });
});
