import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-039", { title: "GET /conversations/{id}/messages — lịch sử (P1)" });
let u, v;

let conv, r;
await tc.step("Chuẩn bị: hội thoại có 1 câu hỏi đã trả lời", "OK", async () => {
  u = await setupUser(tc);
  const doc = await readyDoc(tc, u, "baogia.pdf");
  conv = await newConv(tc, u);
  const a = await ask(tc, u, conv, Q_PAY, { documentIds: [doc.id], label: "POST …/messages" });
  expect(a.status).toBe(200);
});
await tc.step("GET /conversations/{id}/messages", "200 {items} gồm câu hỏi và câu trả lời (kèm citations)", async () => {
  r = await tc.http("GET", `${API}/conversations/${conv}/messages`, { token: u.token, label: "GET /conversations/{id}/messages" });
  if (r.status === 404 || r.status === 405) tc.defect(`API Design 3.3 (IF-06) liệt kê GET /conversations/{id}/messages (lịch sử hội thoại, US-204) nhưng endpoint trả HTTP ${r.status}. Có thể do chưa triển khai (P1) hoặc phụ thuộc OQ-012; cần PO xác nhận phạm vi. Mức: Minor (P1, chưa thuộc R1).`);
  expect(r.status, "Endpoint lịch sử chưa được triển khai").toBe(200);
  expect(Array.isArray(r.json.items)).toBe(true);
  expect(r.json.items.length).toBeGreaterThanOrEqual(2);
});

await tc.finish();
