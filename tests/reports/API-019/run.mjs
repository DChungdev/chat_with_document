import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-019", { title: "Câu hỏi ngoài tài liệu: grounded=false, không citation" });
let u, v;

let doc, conv;
await tc.step("Chuẩn bị", "baogia ready + hội thoại", async () => {
  u = await setupUser(tc);
  doc = await readyDoc(tc, u, "baogia.pdf");
  conv = await newConv(tc, u);
});
await tc.step("Hỏi ngoài phạm vi", "200 SSE; token “Không tìm thấy thông tin này”; done grounded=false, citationCount=0", async () => {
  const r = await ask(tc, u, conv, Q_OUT, { documentIds: [doc.id], label: "POST …/messages (ngoài phạm vi)" });
  expect(r.status).toBe(200);
  expect(r.sse.text).toContain("Không tìm thấy thông tin này");
  expect(r.sse.citations).toHaveLength(0);
  expect(r.sse.done.grounded).toBe(false);
  expect(r.sse.done.citationCount).toBe(0);
  return `Văn bản: ${r.sse.text}`;
});
await tc.step("Hỏi câu có đáp án ngay sau đó", "grounded=true, citationCount ≥ 1", async () => {
  const r = await ask(tc, u, conv, Q_PAY, { documentIds: [doc.id], label: "POST …/messages (có đáp án)" });
  expect(r.sse.done.grounded).toBe(true);
  expect(r.sse.done.citationCount).toBeGreaterThanOrEqual(1);
});
tc.note("Việc “không gọi LLM” không quan sát được từ bên ngoài; chỉ ghi nhận hành vi quan sát được.");

await tc.finish();
