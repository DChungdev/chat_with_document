import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-030", { title: "GET /reports/mvp-metrics: phân quyền" });
let u, v;

let user, ev;
await tc.step("User thường GET /reports/mvp-metrics", "403 FORBIDDEN", async () => {
  user = await setupUser(tc);
  ev = await setupUser(tc, { roles: ["user", "evaluator"] });
  const r = await tc.http("GET", `${API}/reports/mvp-metrics`, { token: user.token, label: "user: GET /reports/mvp-metrics" });
  expectProblem(r, 403, "FORBIDDEN");
});
await tc.step("Evaluator GET /reports/mvp-metrics", "200; có MET-001, MET-002, KR1.2, KR2.2; ghi chưa thể kết luận", async () => {
  const r = await tc.http("GET", `${API}/reports/mvp-metrics`, { token: ev.token, label: "evaluator: GET /reports/mvp-metrics" });
  expect(r.status).toBe(200);
  const s = JSON.stringify(r.json);
  for (const k of ["MET-001", "MET-002", "KR1.2", "KR2.2"]) expect(s, k).toContain(k);
  expect(s.toLowerCase()).toMatch(/chưa thể kết luận|inconclusive|conclusive/);
});
await tc.step("Rà soát JSON: không có nội dung/định danh", "Không có tên tệp, câu hỏi, định danh người dùng", async () => {
  const r = await tc.context.request.get(`${API}/reports/mvp-metrics`, { headers: auth(ev) });
  const s = await r.text();
  expect(s).not.toContain(ev.name);
  expect(s).not.toMatch(/\.pdf/i);
  expect(s).not.toContain(ev.subject);
});

await tc.finish();
