import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-032", { title: "Health & metrics endpoints" });
let u, v;

await tc.step("GET /health và /api/v1/health/live không token", "200 {status:ok}", async () => {
  for (const p of ["/health", `${API}/health/live`]) {
    const r = await tc.http("GET", p, { label: `GET ${p}` });
    expect(r.status).toBe(200);
    expect(r.json.status).toBe("ok");
  }
});
await tc.step("GET /api/v1/health/ready không token", "200 ready hoặc 503 unavailable — ghi thực tế", async () => {
  const r = await tc.http("GET", `${API}/health/ready`, { label: "GET /api/v1/health/ready" });
  expect([200, 503]).toContain(r.status);
  tc.note(`health/ready trả HTTP ${r.status} (${JSON.stringify(r.json)}). Devserver không có CSDL nên 503 là hành vi kỳ vọng ở môi trường này; không coi là lỗi sản phẩm nhưng readiness với DB thật chưa được kiểm chứng.`);
  return `HTTP ${r.status} ${JSON.stringify(r.json)}`;
});
await tc.step("GET /metrics trực tiếp", "200 định dạng Prometheus", async () => {
  const r = await tc.http("GET", "/metrics", { label: "GET /metrics" });
  expect(r.status).toBe(200);
  expect(r.text).toMatch(/# (HELP|TYPE)/);
});
await tc.step("GET /metrics với X-Forwarded-For", "404", async () => {
  const r = await tc.http("GET", "/metrics", { headers: { "X-Forwarded-For": "1.2.3.4" }, label: "GET /metrics (X-Forwarded-For)" });
  expect(r.status).toBe(404);
});

await tc.finish();
