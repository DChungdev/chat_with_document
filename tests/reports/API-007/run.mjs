import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-007", { title: "POST /documents từ chối tệp quá kích thước" });
let u, v;

let limit;
await tc.step("Đọc giới hạn từ /config", "Có maxFileSizeBytes", async () => {
  u = await setupUser(tc);
  const r = await tc.http("GET", `${API}/config`, { token: u.token, label: "GET /config" });
  limit = r.json.maxFileSizeBytes;
  expect(limit).toBeGreaterThan(0);
  return `limit=${limit}`;
});
await tc.step("Tải tệp %PDF- dài limit+1 byte", "413 FILE_TOO_LARGE; detail nêu giới hạn", async () => {
  const buf = Buffer.alloc(limit + 1, 0x20);
  buf.write("%PDF-1.4\n", 0);
  const r = await uploadPdf(tc, u, "x.pdf", { buffer: buf, name: "qua-lon.pdf", label: `POST /documents (limit+1 = ${limit + 1} byte)` });
  expectProblem(r, 413, "FILE_TOO_LARGE");
  return `413 detail="${r.json.detail}"`;
});
await tc.step("Tải tệp %PDF- kích thước limit-10 (nội dung không hợp lệ)", "Không bị 413 (chứng minh ranh giới)", async () => {
  const buf = Buffer.alloc(limit - 10, 0x20);
  buf.write("%PDF-1.4\n", 0);
  const r = await uploadPdf(tc, u, "x.pdf", { buffer: buf, name: "sat-gioi-han.pdf", label: `POST /documents (limit-10 = ${limit - 10} byte)` });
  expect(r.status, "không được 413 khi nhỏ hơn giới hạn").not.toBe(413);
  return `HTTP ${r.status}`;
});

await tc.finish();
