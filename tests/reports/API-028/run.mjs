import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-028", { title: "POST /telemetry/events (allow-list)" });
let u, v;

const ALLOW = {
  session_started: ["entry_source"], data_notice_accepted: ["notice_version"], upload_started: ["file_size", "file_index"],
  upload_succeeded: ["file_size", "duration_ms"], upload_failed: ["error_code", "file_size"], document_ready: ["page_count", "processing_ms"],
  document_processing_failed: ["error_code"], document_deleted: ["document_age_days"], question_submitted: ["question_length", "docs_selected_count"],
  answer_first_token: ["latency_ms"], answer_completed: ["total_ms", "citation_count", "grounded"], answer_failed: ["error_code", "stage"],
  answer_stopped: ["elapsed_ms"], citation_opened: ["citation_index"], answer_feedback: ["rating", "reason_code"],
  task_marked_done: ["task_id", "elapsed_ms", "success"], copy_answer: ["answer_id"],
};
const val = (k) => (/grounded|success/.test(k) ? true : /code|stage|rating|source|version|task_id|answer_id/.test(k) ? "x" : 5);
const camel = (s) => s.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
const sid = uuid();
const ev = (name, style) => ({ name, ts: new Date().toISOString(), sessionId: sid, appVersion: "0.1.0", props: Object.fromEntries(ALLOW[name].map((k) => [style === "camel" ? camel(k) : k, val(k)])) });
await tc.step("Gửi answer_completed", "202; accepted=1, rejected=0", async () => {
  u = await setupUser(tc);
  const r = await tc.http("POST", `${API}/telemetry/events`, { token: u.token, json: { events: [ev("answer_completed", "snake")] }, label: "POST /telemetry/events (props snake_case)" });
  expect(r.status).toBe(202);
  if (r.json.accepted !== 1) {
    const r2 = await tc.http("POST", `${API}/telemetry/events`, { token: u.token, json: { events: [ev("answer_completed", "camel")] }, label: "POST /telemetry/events (props camelCase)" });
    expect(r2.json.accepted, "cả snake_case và camelCase đều không được chấp nhận").toBe(1);
    return "Chấp nhận props camelCase (snake_case bị loại)";
  }
  return "Chấp nhận props snake_case";
});
await tc.step("Gửi 17 sự kiện trong allow-list (1 lô)", "accepted=17, rejected=0", async () => {
  let r = await tc.http("POST", `${API}/telemetry/events`, { token: u.token, json: { events: Object.keys(ALLOW).map((n) => ev(n, "snake")) }, label: "POST /telemetry/events (17 sự kiện)" });
  if (r.json?.accepted !== 17) r = await tc.http("POST", `${API}/telemetry/events`, { token: u.token, json: { events: Object.keys(ALLOW).map((n) => ev(n, "camel")) }, label: "POST /telemetry/events (17 sự kiện, camelCase)" });
  expect(r.status).toBe(202);
  expect(r.json.accepted).toBe(17);
  expect(r.json.rejected).toBe(0);
});
await tc.step("Gửi 51 sự kiện trong một lô", "Bị từ chối 4xx", async () => {
  const r = await tc.http("POST", `${API}/telemetry/events`, { token: u.token, json: { events: Array.from({ length: 51 }, () => ev("copy_answer", "snake")) }, label: "POST /telemetry/events (51 sự kiện)" });
  expect(r.status).toBeGreaterThanOrEqual(400);
  expect(r.status).toBeLessThan(500);
  return `HTTP ${r.status} code=${r.json.code}`;
});

await tc.finish();
