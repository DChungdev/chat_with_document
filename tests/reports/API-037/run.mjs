import fs from "node:fs";
import { startCase, expect } from "../../tools/tc.mjs";
import { API, auth, uuid, setupUser, acceptNotice, uploadPdf, pollDoc, readyDoc, newConv, ask, parseSse, showEvidence, askAndStop, expectProblem, Q_PAY, Q_WARR, Q_OUT } from "../../tools/api.mjs";

const tc = await startCase("API-037", { title: "POST /messages/{id}/regenerate (P1)" });
let u, v;

let conv, doc, stopped, other;
await tc.step("Chuẩn bị: tạo message bị dừng", "stopped", async () => {
  u = await setupUser(tc);
  other = await setupUser(tc);
  doc = await readyDoc(tc, u, "baogia.pdf");
  conv = await newConv(tc, u);
  stopped = await askAndStop(tc, u, conv, Q_PAY, [doc.id]);
  expect(parseSse(stopped.text).done?.status).toBe("stopped");
  await showEvidence(tc, "Message đã bị dừng", [`messageId=${stopped.messageId}`, `stop → ${stopped.stopStatus}`]);
});
let sse;
await tc.step("POST /messages/{id}/regenerate", "200 SSE; messageId mới; done status=complete", async () => {
  const r = await tc.http("POST", `${API}/messages/${stopped.messageId}/regenerate`, { token: u.token, label: "POST /messages/{id}/regenerate" });
  expect(r.status).toBe(200);
  sse = parseSse(r.text);
  expect(sse.messageId).toBeTruthy();
  expect(sse.messageId).not.toBe(stopped.messageId);
  expect(sse.done.status).toBe("complete");
});
await tc.step("Văn bản mới", "Chứa “30 ngày”", async () => {
  expect(sse.text).toContain("30 ngày");
});
await tc.step("regenerate message của người khác", "404", async () => {
  const r = await tc.http("POST", `${API}/messages/${stopped.messageId}/regenerate`, { token: other.token, label: "B: POST /messages/{id}/regenerate" });
  expectProblem(r, 404);
});

await tc.finish();
