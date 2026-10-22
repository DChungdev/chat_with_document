import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { TelemetryWire } from "../api/types";
import { ALLOWED, TelemetryClient } from "./telemetry";

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

function make(send = vi.fn(async (...args: [TelemetryWire[], boolean?]) => void args), extra = {}) {
  const dropped: [string, string[]][] = [];
  const client = new TelemetryClient({ send, onDrop: (n, b) => dropped.push([n, b]), ...extra });
  return { client, send, dropped };
}

describe("TelemetryClient (E10, PRD 5.2)", () => {
  it("chỉ gửi thuộc tính trong allow-list và báo thuộc tính bị chặn", async () => {
    const { client, send, dropped } = make();
    client.track("question_submitted", {
      question_length: 12,
      docs_selected_count: 2,
      question: "Điều khoản thanh toán là gì?",
    } as never);
    await client.flush();
    const sent = send.mock.calls[0]?.[0] as TelemetryWire[];
    expect(sent[0]?.props).toEqual({ question_length: 12, docs_selected_count: 2 });
    expect(JSON.stringify(sent)).not.toContain("Điều khoản");
    expect(dropped).toEqual([["question_submitted", ["question"]]]);
    client.dispose();
  });

  it("sự kiện lạ không bao giờ rời trình duyệt", async () => {
    const { client, send, dropped } = make();
    client.track("keylogger", { text: "bí mật" });
    await client.flush();
    expect(send).not.toHaveBeenCalled();
    expect(dropped[0]?.[0]).toBe("keylogger");
    client.dispose();
  });

  it("mọi sự kiện của PRD 5.2 đều có trong danh sách và không có thuộc tính văn bản tự do", () => {
    for (const name of [
      "session_started",
      "data_notice_accepted",
      "upload_started",
      "upload_succeeded",
      "upload_failed",
      "document_ready",
      "document_processing_failed",
      "document_deleted",
      "question_submitted",
      "answer_first_token",
      "answer_completed",
      "answer_failed",
      "answer_stopped",
      "citation_opened",
      "answer_feedback",
      "task_marked_done",
      "copy_answer",
    ]) {
      expect(ALLOWED[name], name).toBeDefined();
    }
    const forbidden = /question$|answer$|text|snippet|content|file_?name|^name$/;
    for (const [name, props] of Object.entries(ALLOWED)) {
      for (const p of props) expect(forbidden.test(p), `${name}.${p}`).toBe(false);
    }
  });

  it("gắn sessionId ổn định, phiên bản và thời điểm; gộp lô khi đủ số lượng", async () => {
    const { client, send } = make(undefined, {
      maxBatch: 3,
      appVersion: "9.9.9",
      now: () => new Date("2026-10-22T08:00:00Z"),
    });
    client.track("citation_opened", { citation_index: 0 });
    client.track("citation_opened", { citation_index: 1 });
    expect(send).not.toHaveBeenCalled();
    client.track("citation_opened", { citation_index: 2 });
    await vi.advanceTimersByTimeAsync(0);
    const batch = send.mock.calls[0]?.[0] as TelemetryWire[];
    expect(batch).toHaveLength(3);
    expect(new Set(batch.map((e) => e.sessionId)).size).toBe(1);
    expect(batch[0]).toMatchObject({ appVersion: "9.9.9", ts: "2026-10-22T08:00:00.000Z" });
    client.dispose();
  });

  it("tự gửi theo chu kỳ", async () => {
    const { client, send } = make(undefined, { flushIntervalMs: 1000 });
    client.track("session_started", { entry_source: "direct" });
    await vi.advanceTimersByTimeAsync(1100);
    expect(send).toHaveBeenCalledTimes(1);
    client.dispose();
  });

  it("lỗi mạng: giữ lại và gửi lại sau; không bao giờ ném lỗi ra UI", async () => {
    const send = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("offline"))
      .mockResolvedValue(undefined);
    const { client } = make(send);
    client.track("session_started", { entry_source: "direct" });
    await expect(client.flush()).resolves.toBeUndefined();
    await client.flush();
    expect(send).toHaveBeenCalledTimes(2);
    expect(send.mock.calls[1]?.[0]).toHaveLength(1); // cùng sự kiện, không mất, không nhân đôi
    client.dispose();
  });

  it("lỗi 4xx bỏ lô; 401 tắt telemetry cho đến khi có phiên mới", async () => {
    const send = vi.fn().mockRejectedValue({ status: 401 });
    const { client } = make(send);
    client.track("session_started", { entry_source: "direct" });
    await client.flush();
    client.track("session_started", { entry_source: "direct" });
    await client.flush();
    expect(send).toHaveBeenCalledTimes(1);
    client.dispose();
  });

  it("hàng đợi có trần để không phình bộ nhớ khi mất mạng lâu", async () => {
    const send = vi.fn().mockRejectedValue(new TypeError("offline"));
    const { client } = make(send, { maxBatch: 10_000 });
    for (let i = 0; i < 500; i++) client.track("citation_opened", { citation_index: i });
    send.mockResolvedValue(undefined);
    await client.flush();
    expect((send.mock.calls.at(-1)?.[0] as TelemetryWire[]).length).toBeLessThanOrEqual(50);
    client.dispose();
  });

  it("flush(keepalive) chuyển cờ keepalive để gửi được cả khi đóng tab", async () => {
    const { client, send } = make();
    client.track("session_started", { entry_source: "direct" });
    await client.flush(true);
    expect(send.mock.calls[0]?.[1]).toBe(true);
    client.dispose();
  });
});
