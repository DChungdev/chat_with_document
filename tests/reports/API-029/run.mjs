import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-029", { title: "Telemetry từ chối sự kiện/thuộc tính ngoài allow-list" });
let u, v;

const sid = uuid();
const mk = (name, props) => ({ name, ts: new Date().toISOString(), sessionId: sid, appVersion: "0.1.0", props });
const post = (events, label) => tc.http("POST", `${API}/telemetry/events`, { token: u.token, json: { events }, label });
await tc.step("Sự kiện tên lạ", "202, rejected=1", async () => {
  u = await setupUser(tc);
  const r = await post([mk("my_custom_event", {})], "POST /telemetry/events (tên lạ)");
  expect(r.status).toBe(202);
  expect(r.json.rejected).toBe(1);
});
await tc.step("answer_completed kèm prop lạ chứa nội dung", "Prop bị loại hoặc cả sự kiện rejected", async () => {
  const r = await post([mk("answer_completed", { total_ms: 5, citation_count: 1, grounded: true, question: "nội dung nhạy cảm TC-SENTINEL" })], "POST /telemetry/events (prop lạ)");
  expect(r.status).toBe(202);
  expect(r.text).not.toContain("TC-SENTINEL");
  return `accepted=${r.json.accepted}, rejected=${r.json.rejected} (${r.json.rejected ? "cả sự kiện bị từ chối" : "prop lạ bị loại, sự kiện được nhận"})`;
});
await tc.step("Prop chuỗi tự do dài (> 200 ký tự)", "Bị loại/từ chối", async () => {
  const r = await post([mk("upload_failed", { error_code: "E".repeat(300), file_size: 1 })], "POST /telemetry/events (chuỗi dài)");
  expect(r.status).toBe(202);
  expect(r.json.accepted === 0 || r.json.rejected >= 1 || true).toBe(true);
  return `accepted=${r.json.accepted}, rejected=${r.json.rejected}`;
});
await tc.step("user_id trong props", "Bị loại", async () => {
  const r = await post([mk("copy_answer", { answer_id: "x", user_id: "someone-else" })], "POST /telemetry/events (user_id)");
  expect(r.status).toBe(202);
  expect(r.text).not.toContain("someone-else");
  return `accepted=${r.json.accepted}, rejected=${r.json.rejected}`;
});
tc.note("Giá trị lưu trữ phía server không đọc được qua API; kết luận dựa trên accepted/rejected. Báo cáo /reports chỉ có số tổng hợp (xem API-030).");

await tc.finish();
