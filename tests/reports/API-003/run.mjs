import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-003", { title: "POST /data-notice/acceptances (idempotent)" });
let u, v;

let version;
await tc.step("Lấy version từ GET /data-notice", "200", async () => {
  u = await setupUser(tc, { notice: false });
  const r = await tc.http("GET", `${API}/data-notice`, { token: u.token, label: "GET /data-notice" });
  expect(r.status).toBe(200);
  version = r.json.version;
});
await tc.step("POST /data-notice/acceptances", "201", async () => {
  const r = await tc.http("POST", `${API}/data-notice/acceptances`, { token: u.token, json: { version }, label: "POST /data-notice/acceptances (lần 1)" });
  expect(r.status).toBe(201);
});
await tc.step("Gọi lại lần hai cùng body", "201 hoặc tương đương, không 5xx", async () => {
  const r = await tc.http("POST", `${API}/data-notice/acceptances`, { token: u.token, json: { version }, label: "POST /data-notice/acceptances (lần 2)" });
  expect(r.status).toBeLessThan(500);
  expect([200, 201, 204]).toContain(r.status);
  return `HTTP ${r.status}`;
});
await tc.step("GET /config", "noticeAccepted=true", async () => {
  const r = await tc.http("GET", `${API}/config`, { token: u.token, label: "GET /config" });
  expect(r.json.noticeAccepted).toBe(true);
});
await tc.step("Gửi version sai", "Bị từ chối 4xx problem+json", async () => {
  const r = await tc.http("POST", `${API}/data-notice/acceptances`, { token: u.token, json: { version: "khong-ton-tai" }, label: "POST acceptances (version sai)" });
  expect(r.status, "version sai không được chấp nhận").toBeGreaterThanOrEqual(400);
  expect(r.status).toBeLessThan(500);
  return `HTTP ${r.status} code=${r.json?.code}`;
});

await tc.finish();
