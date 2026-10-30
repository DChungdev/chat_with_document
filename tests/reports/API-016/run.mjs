import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-016", { title: "Hỏi đáp: lỗi kiểm tra trước khi mở stream" });
let u, v;

let conv, doc, scan;
await tc.step("Hỏi khi chưa có tài liệu ready", "422 NO_READY_DOCUMENTS (problem+json)", async () => {
  u = await setupUser(tc);
  conv = await newConv(tc, u);
  const r = await ask(tc, u, conv, Q_PAY, { label: "POST …/messages (chưa có tài liệu)" });
  expectProblem(r, 422, "NO_READY_DOCUMENTS");
});
await tc.step("Tải baogia (ready) và scan (error)", "baogia ready; scan error", async () => {
  doc = await readyDoc(tc, u, "baogia.pdf");
  const up = await uploadPdf(tc, u, "scan.pdf");
  scan = await pollDoc(tc, u, up.json.id);
  expect(scan.status).toBe("error");
});
await tc.step("Câu hỏi rỗng / toàn khoảng trắng", "400/422 VALIDATION_ERROR", async () => {
  const r = await ask(tc, u, conv, "   ", { documentIds: [doc.id], label: "POST …/messages (rỗng)" });
  expect([400, 422]).toContain(r.status);
  expect(r.headers["content-type"]).toContain("problem+json");
  return `HTTP ${r.status} code=${r.json.code}`;
});
await tc.step("Câu hỏi dài hơn maxQuestionLength", "413 QUESTION_TOO_LONG", async () => {
  const r = await ask(tc, u, conv, "a".repeat(2001), { documentIds: [doc.id], label: "POST …/messages (2001 ký tự)" });
  expectProblem(r, 413, "QUESTION_TOO_LONG");
});
await tc.step("documentIds chứa tài liệu chưa ready (scan)", "409 DOCUMENT_NOT_READY", async () => {
  const r = await ask(tc, u, conv, Q_PAY, { documentIds: [scan.id], label: "POST …/messages (tài liệu lỗi)" });
  expectProblem(r, 409, "DOCUMENT_NOT_READY");
});

await tc.finish();
