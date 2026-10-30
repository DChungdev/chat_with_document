import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-012", { title: "GET /documents/{id}: tồn tại và không tồn tại" });
let u, v;

let A, B, doc;
await tc.step("A: GET /documents/{id}", "200, đúng schema Document", async () => {
  A = await setupUser(tc); B = await setupUser(tc);
  doc = await readyDoc(tc, A, "baogia.pdf");
  const r = await tc.http("GET", `${API}/documents/${doc.id}`, { token: A.token, label: "A: GET /documents/{id}" });
  expect(r.status).toBe(200);
  for (const k of ["id", "name", "sizeBytes", "uploadedAt", "status"]) expect(r.json[k], k).toBeDefined();
});
await tc.step("B: GET /documents/{id của A}", "404 NOT_FOUND", async () => {
  const r = await tc.http("GET", `${API}/documents/${doc.id}`, { token: B.token, label: "B: GET /documents/{id của A}" });
  expectProblem(r, 404, "NOT_FOUND");
});
await tc.step("A: GET /documents/<uuid ngẫu nhiên>", "404", async () => {
  const r = await tc.http("GET", `${API}/documents/${uuid()}`, { token: A.token, label: "A: GET /documents/<uuid lạ>" });
  expectProblem(r, 404, "NOT_FOUND");
});
await tc.step("A: GET /documents/khong-phai-uuid", "400/422 problem+json", async () => {
  const r = await tc.http("GET", `${API}/documents/khong-phai-uuid`, { token: A.token, label: "A: GET /documents/khong-phai-uuid" });
  expect([400, 422]).toContain(r.status);
  expect(r.headers["content-type"]).toContain("problem+json");
});

await tc.finish();
