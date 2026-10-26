import fs from "node:fs";
import { startCase } from "../../tools/tc.mjs";

const tc = await startCase("API-006", { title: "POST /documents từ chối tệp không phải PDF" });
const { expect } = tc;
let u;
const upload = (name, mimeType, buffer, label) =>
  tc.http("POST", "/api/v1/documents", {
    token: u.token,
    headers: { "Idempotency-Key": crypto.randomUUID() },
    multipart: { file: { name, mimeType, buffer } },
    label,
  });

await tc.step("Chuẩn bị: đăng nhập dev và xác nhận thông báo", "Có token; acceptances → 201", async () => {
  u = await tc.apiLogin();
  const n = await tc.http("GET", "/api/v1/data-notice", { token: u.token, label: "GET /data-notice" });
  const r = await tc.http("POST", "/api/v1/data-notice/acceptances", {
    token: u.token,
    json: { version: n.json.version },
    label: "POST /data-notice/acceptances",
  });
  expect(r.status).toBe(201);
});
await tc.step(
  "Tải khong-phai-pdf.pdf (nội dung văn bản thường)",
  "400 INVALID_FILE_TYPE, problem+json, có requestId, retryable=false",
  async () => {
    const r = await upload("khong-phai-pdf.pdf", "application/pdf", fs.readFileSync(tc.fixture("khong-phai-pdf.pdf")), "POST /documents (tệp giả PDF)");
    expect(r.status).toBe(400);
    expect(r.json.code).toBe("INVALID_FILE_TYPE");
    expect(r.headers["content-type"]).toContain("application/problem+json");
    expect(r.json.requestId).toBeTruthy();
    expect(r.json.retryable).toBe(false);
    return `HTTP ${r.status}, code=${r.json.code}, retryable=${r.json.retryable}`;
  },
);
await tc.step("Tải tệp .txt Content-Type text/plain", "400 INVALID_FILE_TYPE", async () => {
  const r = await upload("ghichu.txt", "text/plain", Buffer.from("xin chao"), "POST /documents (.txt)");
  expect(r.status).toBe(400);
  expect(r.json.code).toBe("INVALID_FILE_TYPE");
  return `HTTP ${r.status}, code=${r.json.code}`;
});
await tc.step("GET /documents", "Không có tài liệu nào được tạo", async () => {
  const r = await tc.http("GET", "/api/v1/documents", { token: u.token, label: "GET /documents" });
  expect(r.status).toBe(200);
  expect(r.json.items).toHaveLength(0);
});
await tc.finish();
