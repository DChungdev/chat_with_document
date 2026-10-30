import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-033", { title: "Mô hình lỗi RFC 7807 thống nhất" });
let u, v;

const S = "TC-SENTINEL-123";
const results = [];
await tc.step("Gây các lỗi 401, 404, 400, 413, 422, 403", "Mỗi phản hồi là application/problem+json", async () => {
  u = await setupUser(tc);
  const n = await setupUser(tc, { notice: false });
  const conv = await newConv(tc, u);
  const mk = async (label, p) => { const r = await p; results.push({ label, r }); return r; };
  await mk("401", tc.http("GET", `${API}/config`, { label: "401: không token" }));
  await mk("404", tc.http("GET", `${API}/documents/${uuid()}`, { token: u.token, label: "404: id lạ" }));
  await mk("400", uploadPdf(tc, u, "khong-phai-pdf.pdf", { name: `${S}.pdf`, label: "400: tệp giả (tên chứa sentinel)" }));
  await mk("413", ask(tc, u, conv, S + "a".repeat(2000), { label: "413: câu hỏi quá dài (chứa sentinel)" }));
  await mk("422", ask(tc, u, conv, Q_PAY, { label: "422: chưa có tài liệu ready" }));
  await mk("403", uploadPdf(tc, n, "baogia.pdf", { label: "403: chưa xác nhận thông báo" }));
  for (const { label, r } of results) expect(r.headers["content-type"], label).toContain("application/problem+json");
  return results.map((x) => `${x.label}→${x.r.status}`).join(", ");
});
await tc.step("Kiểm tra từng body", "Có type,title,status(=HTTP),code,detail,retryable,requestId", async () => {
  for (const { label, r } of results) {
    for (const k of ["type", "title", "status", "code", "detail", "retryable", "requestId"]) expect(r.json[k], `${label}.${k}`).toBeDefined();
    expect(r.json.status, label).toBe(r.status);
  }
});
await tc.step("detail không chứa sentinel", "Không chứa TC-SENTINEL-123", async () => {
  for (const { label, r } of results) expect(r.text, label).not.toContain(S);
});
await tc.step("requestId trùng X-Request-Id", "Trùng nhau", async () => {
  for (const { label, r } of results) expect(r.json.requestId, label).toBe(r.headers["x-request-id"]);
});

await tc.finish();
