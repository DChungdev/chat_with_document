import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-034", { title: "X-Request-Id trên mọi phản hồi" });
let u, v;

const seen = [];
await tc.step("Gọi 6 endpoint khác nhau (200, 201, 202, 204, 4xx, SSE)", "Mỗi phản hồi có X-Request-Id", async () => {
  u = await setupUser(tc);
  const doc = await readyDoc(tc, u, "baogia.pdf");
  const conv = await newConv(tc, u);
  const rs = [
    await tc.http("GET", `${API}/config`, { token: u.token, label: "200: GET /config" }),
    await tc.http("POST", `${API}/conversations`, { token: u.token, headers: { "Idempotency-Key": uuid() }, label: "201: POST /conversations" }),
    await uploadPdf(tc, u, "hopdong.pdf", { label: "202: POST /documents" }),
    await tc.http("DELETE", `${API}/documents/${doc.id}`, { token: u.token, label: "204: DELETE /documents/{id}" }),
    await tc.http("GET", `${API}/documents/${uuid()}`, { token: u.token, label: "404: GET /documents/<lạ>" }),
    await ask(tc, u, conv, Q_PAY, { documentIds: [], label: "SSE/422: POST …/messages" }),
  ];
  for (const r of rs) { expect(r.headers["x-request-id"], `HTTP ${r.status}`).toBeTruthy(); seen.push(r.headers["x-request-id"]); }
  return rs.map((r) => r.status).join(", ");
});
await tc.step("Gửi X-Request-Id: abc123", "Ghi nhận: giữ nguyên hay sinh mới", async () => {
  const r = await tc.http("GET", `${API}/config`, { token: u.token, headers: { "X-Request-Id": "abc123" }, label: "GET /config (X-Request-Id: abc123)" });
  return `Phản hồi X-Request-Id=${r.headers["x-request-id"]} (${r.headers["x-request-id"] === "abc123" ? "giữ nguyên giá trị client" : "server sinh mới"})`;
});
await tc.step("Hai yêu cầu liên tiếp", "Hai giá trị khác nhau", async () => {
  const a = await tc.http("GET", `${API}/config`, { token: u.token, label: "GET /config #1" });
  const b = await tc.http("GET", `${API}/config`, { token: u.token, label: "GET /config #2" });
  expect(a.headers["x-request-id"]).not.toBe(b.headers["x-request-id"]);
});

await tc.finish();
