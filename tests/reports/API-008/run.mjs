import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-008", { title: "POST /documents vượt số tệp tối đa" });
let u, v;

let maxFiles, buf, got429 = null;
await tc.step("Đọc maxFiles từ /config", "Giá trị (mặc định 50)", async () => {
  u = await setupUser(tc);
  const r = await tc.http("GET", `${API}/config`, { token: u.token, label: "GET /config" });
  maxFiles = r.json.maxFiles;
  buf = fs.readFileSync(tc.fixture("baogia.pdf"));
  return `maxFiles=${maxFiles}`;
});
await tc.step("Tải lặp PDF nhỏ tới khi đạt maxFiles", "Mọi lần đều 202", async () => {
  let ok = 0;
  for (let i = 0; i < maxFiles; i++) {
    const r = await tc.context.request.post(`${API}/documents`, { headers: { ...auth(u), "Idempotency-Key": uuid() }, multipart: { file: { name: `f${i}.pdf`, mimeType: "application/pdf", buffer: buf } }, failOnStatusCode: false });
    if (r.status() !== 202) { got429 = { status: r.status(), at: i + 1, retryAfter: r.headers()["retry-after"], body: await r.text() }; break; }
    ok++;
  }
  await showEvidence(tc, "Tải lặp PDF để đạt maxFiles", [`Thành công (202): ${ok}/${maxFiles}`, got429 ? `Bị chặn ở lượt ${got429.at}: HTTP ${got429.status}, Retry-After=${got429.retryAfter}\n${got429.body.slice(0, 300)}` : "Không bị chặn"]);
  if (got429) {
    tc.defect(`Xung đột giữa hai giới hạn: rate limit tải lên (HTTP ${got429.status}, Retry-After=${got429.retryAfter}s) chặn ở lượt ${got429.at}, TRƯỚC khi đạt maxFiles=${maxFiles}. Vì vậy giới hạn số tệp (409 LIMIT_EXCEEDED) không thể kiểm chứng bằng một người dùng. Không né bằng cách sửa mã.`);
  }
  expect(got429, `Bị chặn bởi HTTP ${got429?.status} sau ${ok} lượt (trước maxFiles=${maxFiles})`).toBeNull();
  return `${ok}/${maxFiles} lượt 202`;
});
await tc.step("Tải thêm 1 tệp", "409 LIMIT_EXCEEDED", async () => {
  const r = await uploadPdf(tc, u, "baogia.pdf", { label: "POST /documents (vượt maxFiles)" });
  expectProblem(r, 409, "LIMIT_EXCEEDED");
});

await tc.finish();
