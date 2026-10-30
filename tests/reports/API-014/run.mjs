import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-014", { title: "POST /conversations" });
let u, v;

const K = uuid();
let first;
await tc.step("POST /conversations", "201, id UUID", async () => {
  u = await setupUser(tc);
  const r = await tc.http("POST", `${API}/conversations`, { token: u.token, headers: { "Idempotency-Key": K }, label: "POST /conversations (lần 1)" });
  expect(r.status).toBe(201);
  expect(r.json.id).toMatch(/^[0-9a-f-]{36}$/);
  first = r.json.id;
});
await tc.step("Gọi lại cùng Idempotency-Key", "Cùng hội thoại", async () => {
  const r = await tc.http("POST", `${API}/conversations`, { token: u.token, headers: { "Idempotency-Key": K }, label: "POST /conversations (cùng key)" });
  expect(r.status).toBeLessThan(300);
  expect(r.json.id).toBe(first);
});
await tc.step("Idempotency-Key không phải UUID", "400/422 problem+json", async () => {
  const r = await tc.http("POST", `${API}/conversations`, { token: u.token, headers: { "Idempotency-Key": "abc" }, label: "POST /conversations (key sai)" });
  expect([400, 422]).toContain(r.status);
  expect(r.headers["content-type"]).toContain("problem+json");
});
await tc.step("Không token", "401", async () => {
  const r = await tc.http("POST", `${API}/conversations`, { label: "POST /conversations (không token)" });
  expectProblem(r, 401);
});

await tc.finish();
