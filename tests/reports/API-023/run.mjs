import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-023", { title: "Hỏi đáp trên nhiều tài liệu" });
let u, v;

let d1, d2, conv, ids;
await tc.step("Chuẩn bị: baogia + hopdong ready", "OK", async () => {
  u = await setupUser(tc);
  d1 = await readyDoc(tc, u, "baogia.pdf");
  d2 = await readyDoc(tc, u, "hopdong.pdf");
  conv = await newConv(tc, u);
  ids = [d1.id, d2.id];
});
await tc.step("Hỏi phí bảo trì với cả 2 documentIds", "citations có hopdong.pdf", async () => {
  const r = await ask(tc, u, conv, "Phí bảo trì hằng năm bằng bao nhiêu phần trăm giá trị hợp đồng?", { documentIds: ids, label: "POST …/messages (phí bảo trì)" });
  expect(r.status).toBe(200);
  expect(r.sse.citations.map((c) => c.documentName)).toContain("hopdong.pdf");
});
await tc.step("Hỏi thanh toán với cả 2 documentIds", "citations có baogia.pdf trang 2", async () => {
  const r = await ask(tc, u, conv, Q_PAY, { documentIds: ids, label: "POST …/messages (thanh toán)" });
  expect(r.sse.citations.some((c) => c.documentName === "baogia.pdf" && c.page === 2)).toBe(true);
});
await tc.step("Câu hỏi cần cả hai tài liệu", "Ghi số tài liệu trong citations", async () => {
  const r = await ask(tc, u, conv, "Cho tôi điều khoản thanh toán và phí bảo trì hằng năm", { documentIds: ids, label: "POST …/messages (cần cả hai)" });
  expect(r.status).toBe(200);
  const names = [...new Set(r.sse.citations.map((c) => c.documentName))];
  if (names.length < 2) tc.note(`Câu hỏi tổng hợp chỉ dẫn ${names.length} tài liệu (${names.join(", ") || "không có"}). FakeLLM trích câu tốt nhất nên đây là hạn chế của FakeLLM, không kết luận lỗi sản phẩm; cần LLM thật (RAG-002).`);
  return `Tài liệu trong citations: ${names.join(", ")}`;
});

await tc.finish();
