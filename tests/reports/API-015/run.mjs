import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-015", { title: "SSE hỏi đáp: đủ chuỗi sự kiện" });
let u, v;

let doc, conv, r;
await tc.step("Chuẩn bị: tải baogia.pdf và tạo hội thoại", "ready", async () => {
  u = await setupUser(tc);
  doc = await readyDoc(tc, u, "baogia.pdf");
  conv = await newConv(tc, u);
});
await tc.step("POST …/messages với câu hỏi thanh toán", "200 text/event-stream; Cache-Control: no-cache; X-Accel-Buffering: no", async () => {
  r = await ask(tc, u, conv, Q_PAY, { documentIds: [doc.id], clientMessageId: uuid() });
  expect(r.status).toBe(200);
  expect(r.headers["content-type"]).toContain("text/event-stream");
  expect(r.headers["cache-control"]).toContain("no-cache");
  expect(r.headers["x-accel-buffering"]).toBe("no");
});
await tc.step("Phân tích chuỗi sự kiện", "message đầu; token…; một citations; done complete grounded=true", async () => {
  const names = r.sse.events.map((e) => e.name).filter((n) => n !== "ping");
  expect(names[0]).toBe("message");
  expect(r.sse.events[0].data.status).toBe("streaming");
  expect(names.filter((n) => n === "citations")).toHaveLength(1);
  expect(names.at(-1)).toBe("done");
  expect(r.sse.done.status).toBe("complete");
  expect(r.sse.done.grounded).toBe(true);
  expect(r.sse.done.citationCount).toBeGreaterThanOrEqual(1);
  return `Thứ tự: ${[...new Set(names)].join(" → ")}; số token=${names.filter((n) => n === "token").length}`;
});
await tc.step("Văn bản ghép từ token", "Chứa “30 ngày”; không có nhãn [Sx]", async () => {
  expect(r.sse.text).toContain("30 ngày");
  expect(r.sse.text).not.toMatch(/\[S\d+\]/);
  return `Văn bản: ${r.sse.text.slice(0, 120)}`;
});
await tc.step("Kiểm tra citations[0]", "baogia.pdf, page=2, valid=true", async () => {
  const c = r.sse.citations[0];
  expect(c.documentName).toBe("baogia.pdf");
  expect(c.page).toBe(2);
  expect(c.valid).toBe(true);
});

await tc.finish();
