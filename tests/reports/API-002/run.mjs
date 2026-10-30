import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-002", { title: "GET /data-notice trả thông báo hiện hành" });
let u, v;

await tc.step("GET /data-notice có token", "200; version + nội dung không rỗng", async () => {
  u = await setupUser(tc, { notice: false });
  const r = await tc.http("GET", `${API}/data-notice`, { token: u.token, label: "GET /data-notice" });
  expect(r.status).toBe(200);
  expect(r.json.version).toBeTruthy();
  expect(String(r.json.content).length).toBeGreaterThan(10);
  return `version=${r.json.version}, accepted=${r.json.accepted}`;
});
await tc.step("GET /data-notice không token", "401", async () => {
  const r = await tc.http("GET", `${API}/data-notice`, { label: "GET /data-notice (không token)" });
  expectProblem(r, 401);
});

await tc.finish();
