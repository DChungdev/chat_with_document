import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-018", { title: "Kill switch: 503 QA_DISABLED" });
let u, v;

let ops, doc, conv;
const flag = (enabled, label) => tc.http("PUT", `${API}/admin/flags/qa-enabled`, { token: ops.token, json: { enabled }, label });
try {
  await tc.step("Chuẩn bị: user có baogia ready + hội thoại; tài khoản ops", "OK", async () => {
    u = await setupUser(tc);
    ops = await setupUser(tc, { roles: ["user", "ops"] });
    doc = await readyDoc(tc, u, "baogia.pdf");
    conv = await newConv(tc, u);
  });
  await tc.step("Ops tắt qa-enabled", "204", async () => {
    const r = await flag(false, "PUT /admin/flags/qa-enabled {enabled:false}");
    expect(r.status).toBe(204);
  });
  await tc.step("GET /config", "qaEnabled=false", async () => {
    const r = await tc.http("GET", `${API}/config`, { token: u.token, label: "GET /config (đã tắt)" });
    expect(r.json.qaEnabled).toBe(false);
  });
  await tc.step("Hỏi", "503 QA_DISABLED problem+json", async () => {
    const r = await ask(tc, u, conv, Q_PAY, { documentIds: [doc.id], label: "POST …/messages (kill switch bật)" });
    expectProblem(r, 503, "QA_DISABLED");
  });
  await tc.step("GET /documents và tải tệp mới khi đã tắt", "Vẫn hoạt động (200/202)", async () => {
    const g = await tc.http("GET", `${API}/documents`, { token: u.token, label: "GET /documents (đã tắt hỏi đáp)" });
    expect(g.status).toBe(200);
    const p = await uploadPdf(tc, u, "hopdong.pdf", { label: "POST /documents (đã tắt hỏi đáp)" });
    expect(p.status).toBe(202);
  });
} finally {
  await tc.step("Bật lại qa-enabled và hỏi lại", "204; hỏi trả 200 SSE", async () => {
    const r = await flag(true, "PUT /admin/flags/qa-enabled {enabled:true}");
    expect(r.status).toBe(204);
    const a = await ask(tc, u, conv, Q_PAY, { documentIds: [doc.id], label: "POST …/messages (đã bật lại)" });
    expect(a.status).toBe(200);
  }, { continueOnFail: true });
}

await tc.finish();
