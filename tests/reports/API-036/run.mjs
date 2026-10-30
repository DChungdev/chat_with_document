import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-036", { title: "POST /messages/{id}/stop (P1)" });
let u, v;

let conv, doc, res, other;
await tc.step("Chuẩn bị: baogia ready + hội thoại", "OK", async () => {
  u = await setupUser(tc);
  other = await setupUser(tc);
  doc = await readyDoc(tc, u, "baogia.pdf");
  conv = await newConv(tc, u);
});
await tc.step("Mở SSE (fetch stream trong trình duyệt), lấy messageId và gọi stop ngay", "messageId có; stop trả 202", async () => {
  res = await askAndStop(tc, u, conv, Q_PAY, [doc.id]);
  await showEvidence(tc, "SSE + POST /messages/{id}/stop", [`HTTP ${res.status}`, `messageId=${res.messageId}`, `stop → HTTP ${res.stopStatus}`, "", res.text.slice(0, 1500)]);
  expect(res.messageId).toBeTruthy();
  expect(res.stopStatus).toBe(202);
});
await tc.step("Đọc phần còn lại của luồng", "Kết thúc bằng done status=stopped, grounded=false, citationCount=0", async () => {
  const sse = parseSse(res.text);
  expect(sse.done, "không có sự kiện done").toBeTruthy();
  expect(sse.done.status).toBe("stopped");
  expect(sse.done.grounded).toBe(false);
  expect(sse.done.citationCount).toBe(0);
  return `Văn bản nhận được trước khi dừng: "${sse.text}"`;
});
await tc.step("stop lần hai trên message đã kết thúc", "202 (idempotent)", async () => {
  const r = await tc.http("POST", `${API}/messages/${res.messageId}/stop`, { token: u.token, label: "POST /messages/{id}/stop (lần 2)" });
  expect(r.status).toBe(202);
});
await tc.step("stop message của người khác", "404", async () => {
  const r = await tc.http("POST", `${API}/messages/${res.messageId}/stop`, { token: other.token, label: "B: POST /messages/{id}/stop" });
  expectProblem(r, 404);
});

await tc.finish();
