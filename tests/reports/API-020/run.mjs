import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-020", { title: "Hỏi đáp idempotent theo clientMessageId" });
let u, v;

let doc, conv;
const M = uuid();
await tc.step("Chuẩn bị", "baogia ready + hội thoại", async () => {
  u = await setupUser(tc);
  doc = await readyDoc(tc, u, "baogia.pdf");
  conv = await newConv(tc, u);
});
await tc.step("Hỏi với clientMessageId = M", "200 SSE hoàn tất", async () => {
  const r = await ask(tc, u, conv, Q_PAY, { documentIds: [doc.id], clientMessageId: M, label: "POST …/messages (M, lần 1)" });
  expect(r.status).toBe(200);
  expect(r.sse.done.status).toBe("complete");
});
await tc.step("Gửi lại cùng M và cùng nội dung", "Không 5xx; ghi hành vi thực tế", async () => {
  const r = await ask(tc, u, conv, Q_PAY, { documentIds: [doc.id], clientMessageId: M, label: "POST …/messages (M, lần 2)" });
  expect(r.status).toBeLessThan(500);
  return `HTTP ${r.status}; ${r.sse ? "SSE " + r.sse.events.map((e) => e.name).filter((n) => n !== "token" && n !== "ping").join("→") : "code=" + r.json?.code}`;
});
await tc.step("Hỏi với clientMessageId mới", "200 SSE bình thường", async () => {
  const r = await ask(tc, u, conv, Q_PAY, { documentIds: [doc.id], clientMessageId: uuid(), label: "POST …/messages (M mới)" });
  expect(r.status).toBe(200);
});
tc.note("Chưa có endpoint đọc lịch sử (xem API-039) nên không xác nhận được số câu hỏi lưu; chỉ kết luận từ phản hồi.");

await tc.finish();
