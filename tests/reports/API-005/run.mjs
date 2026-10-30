import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-005", { title: "POST /documents idempotent theo Idempotency-Key" });
let u, v;

const K = uuid();
let X;
await tc.step("Tải baogia.pdf với key K", "202; ghi id", async () => {
  u = await setupUser(tc);
  const r = await uploadPdf(tc, u, "baogia.pdf", { key: K, label: "POST /documents (lần 1, key K)" });
  expect(r.status).toBe(202);
  X = r.json.id;
});
await tc.step("Gửi lại y hệt (cùng K)", "Cùng id, không tạo mới", async () => {
  const r = await uploadPdf(tc, u, "baogia.pdf", { key: K, label: "POST /documents (lần 2, cùng K)" });
  expect(r.status).toBeLessThan(300);
  expect(r.json.id).toBe(X);
  return `HTTP ${r.status}, id trùng`;
});
await tc.step("GET /documents", "Chỉ 1 tài liệu", async () => {
  await pollDoc(tc, u, X);
  const r = await tc.http("GET", `${API}/documents`, { token: u.token, label: "GET /documents" });
  expect(r.json.items).toHaveLength(1);
});
await tc.step("Tệp khác với cùng K", "Nhất quán (trả bản ghi cũ hoặc 4xx) — ghi thực tế", async () => {
  const r = await uploadPdf(tc, u, "hopdong.pdf", { key: K, label: "POST /documents (hopdong.pdf, cùng K)" });
  expect(r.status).toBeLessThan(500);
  const list = await tc.context.request.get(`${API}/documents`, { headers: auth(u) });
  const n = (await list.json()).items.length;
  expect(n, "không được tạo bản ghi thứ hai ngoài ý muốn").toBeLessThanOrEqual(1);
  return `HTTP ${r.status}; id=${r.json?.id === X ? "trả bản ghi cũ" : (r.json?.code ?? "khác")}; số tài liệu=${n}`;
});
await tc.step("Không có header Idempotency-Key", "400/422 VALIDATION_ERROR", async () => {
  const buf = fs.readFileSync(tc.fixture("baogia.pdf"));
  const r = await tc.http("POST", `${API}/documents`, { token: u.token, multipart: { file: { name: "baogia.pdf", mimeType: "application/pdf", buffer: buf } }, label: "POST /documents (thiếu Idempotency-Key)" });
  expect([400, 422]).toContain(r.status);
  expect(r.headers["content-type"]).toContain("problem+json");
  return `HTTP ${r.status} code=${r.json.code}`;
});

await tc.finish();
