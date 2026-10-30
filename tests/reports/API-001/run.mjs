import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-001", { title: "GET /config trả giới hạn và cờ" });
let u, v;

await tc.step("GET /config không token", "401 problem+json", async () => {
  const r = await tc.http("GET", `${API}/config`, { label: "GET /config (không token)" });
  expectProblem(r, 401);
  return `401 code=${r.json.code}`;
});
await tc.step("GET /config có token (chưa xác nhận thông báo)", "200; qaEnabled=true, noticeVersion, noticeAccepted=false, giới hạn 20MB/50 tệp/2000 ký tự", async () => {
  u = await setupUser(tc, { notice: false });
  const r = await tc.http("GET", `${API}/config`, { token: u.token, label: "GET /config (có token)" });
  expect(r.status).toBe(200);
  expect(r.json.qaEnabled).toBe(true);
  expect(r.json.noticeVersion).toBeTruthy();
  expect(r.json.noticeAccepted).toBe(false);
  expect(r.json.maxFileSizeBytes).toBe(20 * 1024 * 1024);
  expect(r.json.maxFiles).toBe(50);
  expect(r.json.maxQuestionLength).toBe(2000);
  return `maxFileSizeBytes=${r.json.maxFileSizeBytes}, maxFiles=${r.json.maxFiles}, maxQuestionLength=${r.json.maxQuestionLength}, maxDocumentsPerQuestion=${r.json.maxDocumentsPerQuestion}`;
});
await tc.step("Xác nhận thông báo rồi GET /config", "noticeAccepted=true", async () => {
  await acceptNotice(tc, u);
  const r = await tc.http("GET", `${API}/config`, { token: u.token, label: "GET /config (sau khi xác nhận)" });
  expect(r.json.noticeAccepted).toBe(true);
});
await tc.step("Kiểm tra header X-Request-Id", "Có X-Request-Id", async () => {
  const r = await tc.http("GET", `${API}/config`, { token: u.token, label: "GET /config — header" });
  expect(r.headers["x-request-id"]).toBeTruthy();
  return `X-Request-Id=${r.headers["x-request-id"]}`;
});

await tc.finish();
