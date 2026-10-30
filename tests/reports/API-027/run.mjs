import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-027", { title: "Citation của người khác → 404" });
let u, v;

let A, B, cid;
await tc.step("Chuẩn bị: A có citation; B là tài khoản khác", "OK", async () => {
  A = await setupUser(tc); B = await setupUser(tc);
  const doc = await readyDoc(tc, A, "baogia.pdf");
  const conv = await newConv(tc, A);
  const r = await ask(tc, A, conv, Q_PAY, { documentIds: [doc.id], label: "A: POST …/messages" });
  cid = r.sse.citations[0].id;
});
await tc.step("B: GET /citations/{id của A}", "404 NOT_FOUND", async () => {
  const r = await tc.http("GET", `${API}/citations/${cid}`, { token: B.token, label: "B: GET /citations/{id của A}" });
  expectProblem(r, 404, "NOT_FOUND");
});
await tc.step("A: cùng yêu cầu", "200", async () => {
  const r = await tc.http("GET", `${API}/citations/${cid}`, { token: A.token, label: "A: GET /citations/{id}" });
  expect(r.status).toBe(200);
});

await tc.finish();
