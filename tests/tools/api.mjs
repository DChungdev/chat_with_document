// Helper dùng chung cho các case API (dựa trên tc.http của tc.mjs).
import fs from "node:fs";
import { expect } from "./tc.mjs";

export const API = "/api/v1";

/** Đăng nhập dev (tên duy nhất) và, mặc định, xác nhận thông báo dữ liệu. Không chụp ảnh (bước chuẩn bị). */
export async function setupUser(tc, { notice = true, roles = ["user"], prefix = "tc" } = {}) {
  const u = await tc.apiLogin(tc.uniqueUser(prefix), roles);
  if (notice) await acceptNotice(tc, u);
  return u;
}

export async function acceptNotice(tc, u) {
  const n = await tc.context.request.get(`${API}/data-notice`, { headers: auth(u) });
  const version = (await n.json()).version;
  const r = await tc.context.request.post(`${API}/data-notice/acceptances`, { headers: auth(u), data: { version } });
  expect(r.status()).toBe(201);
}

export const auth = (u) => ({ Authorization: `Bearer ${u.token}` });
export const uuid = () => crypto.randomUUID();

/** Tải PDF (fixture hoặc buffer) với bằng chứng. Trả về phản hồi của tc.http. */
export function uploadPdf(tc, u, fixtureName, { label, key = uuid(), name, mime = "application/pdf", buffer, headers = {} } = {}) {
  const buf = buffer ?? fs.readFileSync(tc.fixture(fixtureName));
  return tc.http("POST", `${API}/documents`, {
    token: u.token,
    headers: { "Idempotency-Key": key, ...headers },
    multipart: { file: { name: name ?? fixtureName, mimeType: mime, buffer: buf } },
    label: label ?? `POST /documents (${name ?? fixtureName})`,
  });
}

/** Poll (không chụp ảnh) tới khi tài liệu ở trạng thái cuối. */
export async function pollDoc(tc, u, id, { timeout = 25_000, until = ["ready", "error"] } = {}) {
  const t0 = Date.now();
  for (;;) {
    const r = await tc.context.request.get(`${API}/documents/${id}`, { headers: auth(u) });
    const j = await r.json();
    if (until.includes(j.status)) return j;
    if (Date.now() - t0 > timeout) throw new Error(`Hết thời gian chờ tài liệu ${id}; trạng thái cuối: ${j.status}`);
    await new Promise((res) => setTimeout(res, 300));
  }
}

/** Tải một PDF mẫu và chờ tới khi xong; chụp bằng chứng cho trạng thái cuối. Trả về Document. */
export async function readyDoc(tc, u, fixtureName, opts = {}) {
  const up = await uploadPdf(tc, u, fixtureName, { label: `POST /documents (${fixtureName})`, ...opts });
  expect(up.status).toBe(202);
  await pollDoc(tc, u, up.json.id);
  const g = await tc.http("GET", `${API}/documents/${up.json.id}`, { token: u.token, label: `GET /documents/{id} (${fixtureName} sau khi xử lý)` });
  return g.json;
}

export async function newConv(tc, u, label = "POST /conversations") {
  const r = await tc.http("POST", `${API}/conversations`, { token: u.token, headers: { "Idempotency-Key": uuid() }, label });
  expect(r.status).toBe(201);
  return r.json.id;
}

export function parseSse(text) {
  const events = [];
  for (const block of text.split(/\r?\n\r?\n/)) {
    if (!block.trim()) continue;
    let name = "message";
    const data = [];
    for (const line of block.split(/\r?\n/)) {
      if (line.startsWith("event:")) name = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trim());
    }
    let parsed = null;
    try {
      parsed = JSON.parse(data.join("\n"));
    } catch {
      parsed = data.join("\n");
    }
    events.push({ name, data: parsed });
  }
  const tokens = events.filter((e) => e.name === "token").map((e) => e.data.text).join("");
  const cit = events.find((e) => e.name === "citations");
  const done = events.find((e) => e.name === "done");
  const err = events.find((e) => e.name === "error");
  const msg = events.find((e) => e.name === "message");
  return { events, text: tokens, citations: cit?.data?.citations ?? [], done: done?.data, error: err?.data, messageId: msg?.data?.messageId };
}

/** Hỏi đáp qua SSE (đọc hết luồng). Trả {status, headers, json, sse}. */
export async function ask(tc, u, convId, question, { documentIds, clientMessageId, label } = {}) {
  const body = { question };
  if (documentIds) body.documentIds = documentIds;
  if (clientMessageId !== undefined) body.clientMessageId = clientMessageId;
  const r = await tc.http("POST", `${API}/conversations/${convId}/messages`, {
    token: u.token,
    json: body,
    label: label ?? `POST /conversations/{id}/messages — "${question.slice(0, 40)}"`,
  });
  const ct = r.headers["content-type"] ?? "";
  return { ...r, sse: ct.includes("text/event-stream") ? parseSse(r.text) : null };
}

export const Q_PAY = "Thanh toán trong vòng bao nhiêu ngày kể từ ngày nhận hóa đơn?";
export const Q_WARR = "Thiết bị camera được bảo hành bao lâu kể từ ngày nghiệm thu?";
export const Q_OUT = "Thời tiết Hà Nội hôm nay thế nào?";

export function expectProblem(r, status, code) {
  expect(r.status, `HTTP ${r.status}: ${r.text.slice(0, 200)}`).toBe(status);
  expect(r.headers["content-type"] ?? "").toContain("application/problem+json");
  if (code) expect(r.json.code).toBe(code);
}

/** Hiển thị bằng chứng tự do (không phải HTTP đơn lẻ) lên trang chính để bước tự chụp ảnh. */
export async function showEvidence(tc, title, lines) {
  const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);
  await tc.page.setContent(`<!doctype html><meta charset=utf-8><style>body{font:13px/1.45 Consolas,monospace;margin:0;padding:16px;background:#0f172a;color:#e2e8f0}
    h2{margin:0 0 8px;font:600 15px system-ui;color:#93c5fd}pre{white-space:pre-wrap;word-break:break-word;background:#1e293b;padding:10px;border-radius:6px}</style>
    <h2>${esc(title)}</h2><pre>${esc(Array.isArray(lines) ? lines.join("\n") : lines).slice(0, 4000)}</pre>`);
  await tc.page.waitForTimeout(600);
}

/** Mở SSE bằng fetch stream TRONG trình duyệt, bấm "stop" ngay khi nhận messageId. Trả {messageId, text, stopStatus}. */
export async function askAndStop(tc, u, convId, question, documentIds) {
  await tc.page.goto(`${tc.baseURL}/health`);
  return tc.page.evaluate(
    async ({ token, convId, question, documentIds }) => {
      const resp = await fetch(`/api/v1/conversations/${convId}/messages`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ question, documentIds, clientMessageId: crypto.randomUUID() }),
      });
      const reader = resp.body.getReader();
      const dec = new TextDecoder();
      let text = "";
      let stopStatus = null;
      let messageId = null;
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        text += dec.decode(value, { stream: true });
        if (!messageId) {
          const m = text.match(/"messageId":\s*"([0-9a-f-]{36})"/);
          if (m) {
            messageId = m[1];
            const s = await fetch(`/api/v1/messages/${messageId}/stop`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
            stopStatus = s.status;
          }
        }
      }
      return { status: resp.status, messageId, text, stopStatus };
    },
    { token: u.token, convId, question, documentIds },
  );
}
