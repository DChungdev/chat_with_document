import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-009", { title: "POST /documents bị chặn khi chưa xác nhận thông báo" });
let u, v;

await tc.step("Tải baogia.pdf khi chưa xác nhận", "403 NOTICE_NOT_ACCEPTED", async () => {
  u = await setupUser(tc, { notice: false });
  const r = await uploadPdf(tc, u, "baogia.pdf", { label: "POST /documents (chưa xác nhận thông báo)" });
  expectProblem(r, 403, "NOTICE_NOT_ACCEPTED");
});
await tc.step("GET /documents", "Rỗng", async () => {
  const r = await tc.http("GET", `${API}/documents`, { token: u.token, label: "GET /documents" });
  expect(r.json.items).toHaveLength(0);
});
await tc.step("Xác nhận thông báo rồi tải lại", "202", async () => {
  await acceptNotice(tc, u);
  const r = await uploadPdf(tc, u, "baogia.pdf", { label: "POST /documents (sau khi xác nhận)" });
  expect(r.status).toBe(202);
});

await tc.finish();
