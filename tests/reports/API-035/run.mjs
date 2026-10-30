import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-035", { title: "CORS chỉ cho phép origin của SPA" });
let u, v;

const EVIL = "https://evil.example";
await tc.step("OPTIONS /api/v1/config với Origin lạ", "Không có Access-Control-Allow-Origin cho origin này", async () => {
  const r = await tc.http("OPTIONS", `${API}/config`, { headers: { Origin: EVIL, "Access-Control-Request-Method": "GET" }, label: "OPTIONS /config (Origin lạ)" });
  const acao = r.headers["access-control-allow-origin"];
  expect(acao).not.toBe("*");
  expect(acao).not.toBe(EVIL);
  return `HTTP ${r.status}, ACAO=${acao ?? "(không có)"}`;
});
await tc.step("GET /api/v1/config với Origin lạ", "Không ACAO: * và không phản chiếu origin lạ", async () => {
  u = await setupUser(tc);
  const r = await tc.http("GET", `${API}/config`, { token: u.token, headers: { Origin: EVIL }, label: "GET /config (Origin lạ)" });
  const acao = r.headers["access-control-allow-origin"];
  expect(acao).not.toBe("*");
  expect(acao).not.toBe(EVIL);
  return `ACAO=${acao ?? "(không có)"}`;
});
await tc.step("Origin hợp lệ http://127.0.0.1:8000", "Hoạt động bình thường", async () => {
  const r = await tc.http("GET", `${API}/config`, { token: u.token, headers: { Origin: "http://127.0.0.1:8000" }, label: "GET /config (cùng origin)" });
  expect(r.status).toBe(200);
});

await tc.finish();
