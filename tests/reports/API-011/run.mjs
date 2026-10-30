import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-011", { title: "GET /documents: phân trang và trạng thái" });
let u, v;

let ids = [];
await tc.step("Tải baogia, hopdong, scan và đợi xử lý xong", "Các tệp tới trạng thái cuối", async () => {
  u = await setupUser(tc);
  for (const f of ["baogia.pdf", "hopdong.pdf", "scan.pdf"]) {
    const r = await uploadPdf(tc, u, f);
    expect(r.status).toBe(202);
    ids.push(r.json.id);
  }
  for (const id of ids) await pollDoc(tc, u, id);
});
let next;
await tc.step("GET /documents?limit=2", "200; 2 phần tử; nextCursor khác null", async () => {
  const r = await tc.http("GET", `${API}/documents?limit=2`, { token: u.token, label: "GET /documents?limit=2" });
  expect(r.status).toBe(200);
  expect(r.json.items).toHaveLength(2);
  expect(r.json.nextCursor).toBeTruthy();
  next = r.json;
});
await tc.step("GET /documents?limit=2&cursor=…", "Phần tử còn lại, không trùng trang 1", async () => {
  const r = await tc.http("GET", `${API}/documents?limit=2&cursor=${encodeURIComponent(next.nextCursor)}`, { token: u.token, label: "GET /documents (trang 2)" });
  expect(r.status).toBe(200);
  expect(r.json.items).toHaveLength(1);
  const seen = new Set(next.items.map((d) => d.id));
  expect(seen.has(r.json.items[0].id)).toBe(false);
});
await tc.step("GET /documents?limit=1000", "Bị chặn/kẹp ≤ 100 (ghi thực tế)", async () => {
  const r = await tc.http("GET", `${API}/documents?limit=1000`, { token: u.token, label: "GET /documents?limit=1000" });
  expect(r.status === 200 ? r.json.items.length : 0).toBeLessThanOrEqual(100);
  expect(r.status).toBeLessThan(500);
  return `HTTP ${r.status}${r.status === 200 ? `, ${r.json.items.length} phần tử` : ` code=${r.json.code}`}`;
});
await tc.step("Kiểm tra trạng thái từng tệp", "baogia, hopdong: ready; scan: error NO_TEXT", async () => {
  const r = await tc.http("GET", `${API}/documents?limit=10`, { token: u.token, label: "GET /documents (toàn bộ)" });
  const by = Object.fromEntries(r.json.items.map((d) => [d.name, d]));
  expect(by["baogia.pdf"].status).toBe("ready");
  expect(by["hopdong.pdf"].status).toBe("ready");
  expect(by["scan.pdf"].status).toBe("error");
  expect(by["scan.pdf"].errorCode).toBe("NO_TEXT");
});

await tc.finish();
