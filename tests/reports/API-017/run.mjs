import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-017", { title: "Hỏi đáp với documentIds của người khác → 404" });
let u, v;

let A, B, docA, convB;
await tc.step("Chuẩn bị: A có baogia ready; B có hội thoại", "OK", async () => {
  A = await setupUser(tc); B = await setupUser(tc);
  docA = await readyDoc(tc, A, "baogia.pdf");
  convB = await newConv(tc, B, "B: POST /conversations");
});
await tc.step("B hỏi với documentIds của A", "404 NOT_FOUND, không SSE", async () => {
  const r = await ask(tc, B, convB, Q_PAY, { documentIds: [docA.id], label: "B: POST …/messages (documentIds của A)" });
  expectProblem(r, 404, "NOT_FOUND");
});
await tc.step("B hỏi với documentIds rỗng", "422 NO_READY_DOCUMENTS (không dùng tài liệu của A)", async () => {
  const r = await ask(tc, B, convB, Q_PAY, { label: "B: POST …/messages (không chỉ định tài liệu)" });
  expectProblem(r, 422, "NO_READY_DOCUMENTS");
});
await tc.step("B dùng conversationId của A", "404", async () => {
  const convA = await newConv(tc, A, "A: POST /conversations");
  const r = await ask(tc, B, convA, Q_PAY, { label: "B: POST …/messages (conversation của A)" });
  expectProblem(r, 404);
});

await tc.finish();
