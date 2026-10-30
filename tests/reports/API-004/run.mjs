import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-004", { title: "POST /documents tải PDF hợp lệ → 202" });
let u, v;

let docId;
await tc.step("POST /documents baogia.pdf + Idempotency-Key", "202; Location; status=processing; ≤ 2s", async () => {
  u = await setupUser(tc);
  const t0 = Date.now();
  const r = await uploadPdf(tc, u, "baogia.pdf");
  const ms = Date.now() - t0;
  expect(r.status).toBe(202);
  expect(r.headers["location"]).toBe(`${API}/documents/${r.json.id}`);
  expect(r.json.status).toBe("processing");
  expect(ms).toBeLessThan(2000);
  docId = r.json.id;
  return `202 trong ${ms} ms; Location=${r.headers["location"]}`;
});
await tc.step("Poll GET /documents/{id} tới ready", "ready; pageCount=3; errorCode=null", async () => {
  const d = await pollDoc(tc, u, docId);
  const r = await tc.http("GET", `${API}/documents/${docId}`, { token: u.token, label: "GET /documents/{id} (sau xử lý)" });
  expect(r.json.status).toBe("ready");
  expect(r.json.pageCount).toBe(3);
  expect(r.json.errorCode ?? null).toBeNull();
  return `status=${d.status}, pageCount=${d.pageCount}`;
});
await tc.step("GET /documents", "Đúng 1 tài liệu với name, sizeBytes, uploadedAt, status", async () => {
  const r = await tc.http("GET", `${API}/documents`, { token: u.token, label: "GET /documents" });
  expect(r.status).toBe(200);
  expect(r.json.items).toHaveLength(1);
  const d = r.json.items[0];
  for (const k of ["name", "sizeBytes", "uploadedAt", "status"]) expect(d[k], k).toBeDefined();
});

await tc.finish();
