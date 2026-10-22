import type { Problem } from "./types";

/** Lỗi API theo RFC 7807. `detail` đã được server làm sạch, an toàn để hiển thị cho người dùng. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly retryable: boolean;
  readonly detail: string;
  readonly retryAfter: number | null;

  constructor(problem: Problem, retryAfter: number | null = null) {
    super(problem.code);
    this.name = "ApiError";
    this.status = problem.status;
    this.code = problem.code;
    this.retryable = Boolean(problem.retryable);
    this.detail = problem.detail ?? problem.title;
    this.retryAfter = retryAfter;
  }
}

/** Lỗi mạng (mất kết nối, server tắt): khác với lỗi nghiệp vụ do server trả về. */
export class NetworkError extends Error {
  constructor() {
    super("NETWORK_ERROR");
    this.name = "NetworkError";
  }
}

export interface ClientOptions {
  baseUrl?: string;
  getToken: () => string | null;
  onUnauthorized: () => void;
  fetchImpl?: typeof fetch;
}

async function toApiError(res: Response): Promise<ApiError> {
  const retryAfterHeader = res.headers.get("retry-after");
  const retryAfter = retryAfterHeader ? Number(retryAfterHeader) : null;
  try {
    const body = (await res.json()) as Partial<Problem>;
    if (body && typeof body.code === "string") {
      return new ApiError(
        // Trạng thái HTTP thật là nguồn đúng; không tin trường `status` trong thân.
        { title: body.title ?? "Lỗi", ...body, status: res.status, code: body.code },
        retryAfter,
      );
    }
  } catch {
    /* thân phản hồi không phải JSON (vd. lỗi từ proxy) */
  }
  return new ApiError(
    { title: res.statusText, status: res.status, code: "HTTP_ERROR" },
    retryAfter,
  );
}

export class HttpClient {
  private readonly base: string;
  private readonly getToken: () => string | null;
  private readonly onUnauthorized: () => void;
  private readonly fetchImpl: typeof fetch;

  constructor(opts: ClientOptions) {
    this.base = opts.baseUrl ?? "/api/v1";
    this.getToken = opts.getToken;
    this.onUnauthorized = opts.onUnauthorized;
    this.fetchImpl = opts.fetchImpl ?? ((...a) => fetch(...a));
  }

  /** Cho các kênh không đi qua `raw` (vd. XHR tải lên) báo phiên hết hạn. */
  signalUnauthorized(): void {
    this.onUnauthorized();
  }

  authHeaders(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  /** Trả về Response khi 2xx; ngược lại ném ApiError. 401 kích hoạt luồng hết phiên. */
  async raw(path: string, init: RequestInit = {}): Promise<Response> {
    let res: Response;
    try {
      res = await this.fetchImpl(`${this.base}${path}`, {
        ...init,
        headers: { ...this.authHeaders(), ...(init.headers as Record<string, string> | undefined) },
      });
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") throw e;
      throw new NetworkError();
    }
    if (!res.ok) {
      const err = await toApiError(res);
      if (res.status === 401) this.onUnauthorized();
      throw err;
    }
    return res;
  }

  async json<T>(path: string, init: RequestInit = {}): Promise<T> {
    const res = await this.raw(path, init);
    return (await res.json()) as T;
  }

  async send(path: string, init: RequestInit = {}): Promise<void> {
    await this.raw(path, init);
  }

  postJson(path: string, body: unknown, init: RequestInit = {}): Promise<Response> {
    return this.raw(path, {
      ...init,
      method: init.method ?? "POST",
      headers: { "Content-Type": "application/json", ...(init.headers as Record<string, string>) },
      body: JSON.stringify(body),
    });
  }
}
