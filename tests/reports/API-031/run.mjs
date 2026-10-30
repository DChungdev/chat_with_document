import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-031", { title: "PUT /admin/flags/qa-enabled: phân quyền" });
let u, v;

let user, evl, ops;
const put = (who, enabled, label) => tc.http("PUT", `${API}/admin/flags/qa-enabled`, { token: who.token, json: { enabled }, label });
try {
  await tc.step("User: PUT {enabled:false}", "403; /config vẫn qaEnabled=true", async () => {
    user = await setupUser(tc); evl = await setupUser(tc, { roles: ["user", "evaluator"] }); ops = await setupUser(tc, { roles: ["user", "ops"] });
    const r = await put(user, false, "user: PUT qa-enabled false");
    expectProblem(r, 403);
    const c = await tc.http("GET", `${API}/config`, { token: user.token, label: "GET /config" });
    expect(c.json.qaEnabled).toBe(true);
  });
  await tc.step("Evaluator: PUT {enabled:false}", "403", async () => {
    const r = await put(evl, false, "evaluator: PUT qa-enabled false");
    expectProblem(r, 403);
  });
  await tc.step("Ops: false rồi true", "Cả hai 204; /config phản ánh", async () => {
    const a = await put(ops, false, "ops: PUT qa-enabled false");
    expect(a.status).toBe(204);
    const c1 = await tc.context.request.get(`${API}/config`, { headers: auth(user) });
    expect((await c1.json()).qaEnabled).toBe(false);
    const b = await put(ops, true, "ops: PUT qa-enabled true");
    expect(b.status).toBe(204);
    const c2 = await tc.http("GET", `${API}/config`, { token: user.token, label: "GET /config (đã bật lại)" });
    expect(c2.json.qaEnabled).toBe(true);
  });
  await tc.step("Body sai {enabled:\"abc\"}", "400 VALIDATION_ERROR", async () => {
    const r = await tc.http("PUT", `${API}/admin/flags/qa-enabled`, { token: ops.token, json: { enabled: "abc" }, label: "ops: PUT body sai" });
    expectProblem(r, 400, "VALIDATION_ERROR");
  });
} finally {
  await tc.step("Dọn dẹp: bảo đảm qaEnabled=true", "204", async () => {
    const r = await put(ops ?? (await setupUser(tc, { roles: ["user", "ops"] })), true, "ops: PUT qa-enabled true (dọn dẹp)");
    expect(r.status).toBe(204);
  }, { continueOnFail: true });
}

await tc.finish();
