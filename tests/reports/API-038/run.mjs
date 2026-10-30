import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-038", { title: "PUT /messages/{id}/feedback (P1)" });
let u, v;

let mid, other;
const fb = (who, json, label, id) => tc.http("PUT", `${API}/messages/${id ?? mid}/feedback`, { token: who.token, json, label });
await tc.step("Chuẩn bị: câu trả lời hoàn tất", "messageId", async () => {
  u = await setupUser(tc); other = await setupUser(tc);
  const doc = await readyDoc(tc, u, "baogia.pdf");
  const conv = await newConv(tc, u);
  const r = await ask(tc, u, conv, Q_PAY, { documentIds: [doc.id], label: "POST …/messages" });
  mid = r.sse.messageId;
  expect(mid).toBeTruthy();
});
await tc.step("PUT feedback {rating:'up'}", "204", async () => {
  const r = await fb(u, { rating: "up" }, "PUT feedback {rating:up}");
  expect(r.status).toBe(204);
});
await tc.step("Lặp lại cùng yêu cầu", "204, kết quả như nhau", async () => {
  const r = await fb(u, { rating: "up" }, "PUT feedback {rating:up} (lần 2)");
  expect(r.status).toBe(204);
});
await tc.step("{rating:'down', reasonCode}", "204", async () => {
  const r = await fb(u, { rating: "down", reasonCode: "wrong_source" }, "PUT feedback {rating:down, reasonCode}");
  expect(r.status, `HTTP ${r.status} ${r.text.slice(0, 150)}`).toBe(204);
});
await tc.step("{rating:'abc'}", "400/422 VALIDATION_ERROR", async () => {
  const r = await fb(u, { rating: "abc" }, "PUT feedback {rating:abc}");
  expect([400, 422]).toContain(r.status);
});
await tc.step("Message của người khác", "404", async () => {
  const r = await fb(other, { rating: "up" }, "B: PUT feedback (message của A)");
  expectProblem(r, 404);
});

await tc.finish();
