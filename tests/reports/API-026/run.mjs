import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-026", { title: "Citation sau khi xóa tài liệu → valid=false" });
let u, v;

let cid, doc;
await tc.step("Chuẩn bị: câu trả lời có citation", "OK", async () => {
  u = await setupUser(tc);
  doc = await readyDoc(tc, u, "baogia.pdf");
  const conv = await newConv(tc, u);
  const r = await ask(tc, u, conv, Q_PAY, { documentIds: [doc.id], label: "POST …/messages" });
  cid = r.sse.citations[0].id;
});
await tc.step("Xóa baogia.pdf", "204", async () => {
  const r = await tc.http("DELETE", `${API}/documents/${doc.id}`, { token: u.token, label: "DELETE /documents/{id}" });
  expect(r.status).toBe(204);
});
await tc.step("GET /citations/{id}", "200; valid=false; snippet/documentId/documentName = null", async () => {
  const r = await tc.http("GET", `${API}/citations/${cid}`, { token: u.token, label: "GET /citations/{id} (đã xóa tài liệu)" });
  expect(r.status).toBe(200);
  expect(r.json.valid).toBe(false);
  expect(r.json.snippet ?? null).toBeNull();
  expect(r.json.documentId ?? null).toBeNull();
  expect(r.json.documentName ?? null).toBeNull();
});

await tc.finish();
