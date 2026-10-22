import type { TelemetryWire } from "../api/types";
import { uuid } from "../ui/format";

/**
 * Danh sách sự kiện và thuộc tính được phép (PRD 5.2, Blueprint 3.6). PHẢI khớp bảng
 * `telemetry_event_types` ở server. Client lọc trước; server lọc lại (phòng thủ nhiều lớp).
 * Tuyệt đối không có trường văn bản tự do: không câu hỏi, câu trả lời, tên tệp.
 */
export const ALLOWED: Readonly<Record<string, readonly string[]>> = {
  session_started: ["entry_source"],
  data_notice_accepted: ["notice_version"],
  upload_started: ["file_size", "file_index"],
  upload_succeeded: ["file_size", "duration_ms"],
  upload_failed: ["file_size", "error_code"],
  document_ready: ["page_count", "processing_ms"],
  document_processing_failed: ["error_code"],
  document_deleted: ["document_age_days"],
  question_submitted: ["question_length", "docs_selected_count"],
  answer_first_token: ["latency_ms"],
  answer_completed: ["total_ms", "citation_count", "grounded"],
  answer_failed: ["error_code", "stage"],
  answer_stopped: ["elapsed_ms"],
  citation_opened: ["citation_index"],
  answer_feedback: ["rating", "reason_code"],
  copy_answer: ["answer_id"],
  task_marked_done: ["task_id", "elapsed_ms", "success"],
};

export type TelemetryName = keyof typeof ALLOWED;
export type Props = Record<string, string | number | boolean>;

export type Sender = (events: TelemetryWire[], keepalive?: boolean) => Promise<void>;

export interface TelemetryOptions {
  send: Sender;
  appVersion?: string;
  flushIntervalMs?: number;
  maxBatch?: number;
  now?: () => Date;
  onDrop?: (name: string, blocked: string[]) => void;
}

export interface Tracker {
  track(name: string, props?: Props): void;
  flush(keepalive?: boolean): Promise<void>;
  dispose(): void;
}

const MAX_QUEUE = 200;

export class TelemetryClient implements Tracker {
  readonly sessionId = uuid();
  private queue: TelemetryWire[] = [];
  private timer: ReturnType<typeof setInterval> | null = null;
  private flushing = false;
  private disabled = false;
  private readonly opts: Required<Omit<TelemetryOptions, "onDrop">> &
    Pick<TelemetryOptions, "onDrop">;

  constructor(opts: TelemetryOptions) {
    this.opts = {
      appVersion: "0.1.0",
      flushIntervalMs: 5000,
      maxBatch: 20,
      now: () => new Date(),
      onDrop: undefined,
      ...opts,
    };
    this.timer = setInterval(() => void this.flush(), this.opts.flushIntervalMs);
  }

  track(name: string, props: Props = {}): void {
    if (this.disabled) return;
    const allowed = ALLOWED[name];
    if (!allowed) {
      this.opts.onDrop?.(name, Object.keys(props));
      return; // sự kiện lạ không bao giờ rời trình duyệt
    }
    const clean: Props = {};
    const blocked: string[] = [];
    for (const [k, v] of Object.entries(props)) {
      if (allowed.includes(k)) clean[k] = v;
      else blocked.push(k);
    }
    if (blocked.length) this.opts.onDrop?.(name, blocked);
    this.queue.push({
      name,
      ts: this.opts.now().toISOString(),
      sessionId: this.sessionId,
      appVersion: this.opts.appVersion,
      props: clean,
    });
    if (this.queue.length > MAX_QUEUE) this.queue.splice(0, this.queue.length - MAX_QUEUE);
    if (this.queue.length >= this.opts.maxBatch) void this.flush();
  }

  async flush(keepalive = false): Promise<void> {
    if (this.flushing || this.disabled || this.queue.length === 0) return;
    this.flushing = true;
    const batch = this.queue.splice(0, 50);
    try {
      await this.opts.send(batch, keepalive);
    } catch (e) {
      // Telemetry không bao giờ làm phiền người dùng. Lỗi 4xx (vd. 401/403) bỏ lô; lỗi mạng giữ lại thử sau.
      const status = (e as { status?: number }).status;
      if (status === undefined) this.queue.unshift(...batch);
      else if (status === 401) this.disabled = true;
    } finally {
      this.flushing = false;
    }
  }

  dispose(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }
}
