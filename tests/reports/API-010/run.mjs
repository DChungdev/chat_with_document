import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-010", { title: "Rate limit tải lên → 429 + Retry-After" });
let u, v;

let buf, hit = null, ok = 0;
await tc.step("Gửi liên tiếp các yêu cầu tải PDF nhỏ tới khi gặp lỗi", "Các lượt đầu 202", async () => {
  u = await setupUser(tc);
  buf = fs.readFileSync(tc.fixture("baogia.pdf"));
  for (let i = 0; i < 60; i++) {
    const r = await tc.context.request.post(`${API}/documents`, { headers: { ...auth(u), "Idempotency-Key": uuid() }, multipart: { file: { name: `f${i}.pdf`, mimeType: "application/pdf", buffer: buf } }, failOnStatusCode: false });
    if (r.status() === 202) { ok++; continue; }
    hit = { status: r.status(), headers: r.headers(), body: await r.text() };
    break;
  }
  await showEvidence(tc, "Tải lặp để kích hoạt rate limit", [`202 liên tiếp: ${ok}`, hit ? `Lượt ${ok + 1}: HTTP ${hit.status} Retry-After=${hit.headers["retry-after"]}` : "Không bị chặn sau 60 lượt"]);
  expect(ok).toBeGreaterThan(0);
  return `${ok} lượt 202 trước khi bị chặn`;
});
await tc.step("Quan sát lượt bị giới hạn", "429 RATE_LIMITED + Retry-After > 0", async () => {
  const r = await uploadPdf(tc, u, "baogia.pdf", { label: "POST /documents (bị giới hạn)" });
  expectProblem(r, 429, "RATE_LIMITED");
  const ra = Number(r.headers["retry-after"]);
  expect(ra).toBeGreaterThan(0);
  return `429, Retry-After=${ra}s; số lượt thực tế trước khi bị chặn = ${ok} (thiết kế đề xuất: 20/giờ)`;
});
await tc.step("GET /documents cùng token", "Vẫn 200", async () => {
  const r = await tc.http("GET", `${API}/documents`, { token: u.token, label: "GET /documents (cùng token)" });
  expect(r.status).toBe(200);
});
await tc.step("Tài khoản khác tải 1 tệp", "202 (giới hạn theo người dùng)", async () => {
  const w = await setupUser(tc);
  const r = await uploadPdf(tc, w, "baogia.pdf", { label: "POST /documents (tài khoản khác)" });
  expect(r.status).toBe(202);
});
if (ok !== 20) tc.note(`Số lượt thực tế trước khi bị chặn là ${ok}, khác đề xuất 20/giờ (OQ-011).`);

await tc.finish();
