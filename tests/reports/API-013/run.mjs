import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-013", { title: "DELETE /documents/{id}" });
let u, v;

let A, B, doc;
await tc.step("B: DELETE /documents/{id của A}", "404; tài liệu của A vẫn còn", async () => {
  A = await setupUser(tc); B = await setupUser(tc);
  doc = await readyDoc(tc, A, "baogia.pdf");
  const r = await tc.http("DELETE", `${API}/documents/${doc.id}`, { token: B.token, label: "B: DELETE /documents/{id của A}" });
  expectProblem(r, 404);
  const g = await tc.http("GET", `${API}/documents/${doc.id}`, { token: A.token, label: "A: GET (vẫn còn)" });
  expect(g.status).toBe(200);
});
await tc.step("A: DELETE /documents/{id}", "204", async () => {
  const r = await tc.http("DELETE", `${API}/documents/${doc.id}`, { token: A.token, label: "A: DELETE /documents/{id}" });
  expect(r.status).toBe(204);
});
await tc.step("A: GET /documents/{id}", "404", async () => {
  const r = await tc.http("GET", `${API}/documents/${doc.id}`, { token: A.token, label: "A: GET sau khi xóa" });
  expectProblem(r, 404);
});
await tc.step("A: DELETE lần hai", "404", async () => {
  const r = await tc.http("DELETE", `${API}/documents/${doc.id}`, { token: A.token, label: "A: DELETE lần hai" });
  expectProblem(r, 404);
});
await tc.step("A: GET /documents", "Danh sách không còn tài liệu", async () => {
  const r = await tc.http("GET", `${API}/documents`, { token: A.token, label: "A: GET /documents" });
  expect(r.json.items).toHaveLength(0);
});

await tc.finish();
