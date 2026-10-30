import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-025", { title: "GET /citations/{id}" });
let u, v;

let cid;
await tc.step("Chuẩn bị: tạo câu trả lời có citation", "citation id", async () => {
  u = await setupUser(tc);
  const doc = await readyDoc(tc, u, "baogia.pdf");
  const conv = await newConv(tc, u);
  const r = await ask(tc, u, conv, Q_PAY, { documentIds: [doc.id], label: "POST …/messages" });
  cid = r.sse.citations[0].id;
  expect(cid).toBeTruthy();
});
await tc.step("GET /citations/{id}", "200; baogia.pdf, page=2, snippet chứa câu thanh toán, valid=true", async () => {
  const r = await tc.http("GET", `${API}/citations/${cid}`, { token: u.token, label: "GET /citations/{id}" });
  expect(r.status).toBe(200);
  expect(r.json.documentName).toBe("baogia.pdf");
  expect(r.json.page).toBe(2);
  expect(r.json.snippet).toContain("Thanh toán trong vòng 30 ngày");
  expect(r.json.valid).toBe(true);
  expect(r.json.snippet.length).toBeLessThanOrEqual(600);
  return `snippet ${r.json.snippet.length} ký tự`;
});

await tc.finish();
