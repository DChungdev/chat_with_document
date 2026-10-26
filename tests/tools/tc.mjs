// Khung chạy test case: ghi video, chụp ảnh từng bước, sinh report.md + result.json.
// Dùng:  import { startCase, expect } from "../../tools/tc.mjs";   (từ tests/reports/<ID>/run.mjs)
// Chạy:  node tests/reports/<ID>/run.mjs        (BASE_URL mặc định http://127.0.0.1:8000)
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
export const REPO = path.resolve(here, "..", "..");
const WEB = path.join(REPO, "apps", "web");
const require = createRequire(path.join(WEB, "package.json"));
const pw = require("@playwright/test");
export const { expect } = pw;
export const requireWeb = require; // để case dùng thêm gói của apps/web (vd "@axe-core/playwright")
export const BASE_URL = process.env.BASE_URL ?? "http://127.0.0.1:8000";
export const fixture = (name) => path.join(WEB, "e2e", "fixtures", name);

let userCounter = 0;
export const uniqueUser = (prefix = "tc") =>
  `${prefix}${Date.now().toString(36)}${userCounter++}`;

const slug = (s) =>
  s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .toLowerCase()
    .slice(0, 50);
const esc = (s) =>
  String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);
const fmt = (ms) => `${(ms / 1000).toFixed(1)}s`;

/**
 * Mở một phiên test cho 1 test case. Artifact ghi vào tests/reports/<id>/ :
 *   screenshots/NN-*.png · video/<id>.webm · report.md · result.json
 * @param {string} id     Mã test case, ví dụ "E2E-001" (tên thư mục artifact)
 * @param {{title?: string, viewport?: {width:number,height:number}, headless?: boolean}} [opts]
 */
export async function startCase(id, opts = {}) {
  const dir = path.join(REPO, "tests", "reports", id);
  const shotDir = path.join(dir, "screenshots");
  const videoDir = path.join(dir, "video");
  // Làm sạch lần chạy trước để báo cáo luôn phản ánh đúng một lần chạy
  for (const d of [shotDir, videoDir]) fs.rmSync(d, { recursive: true, force: true });
  fs.mkdirSync(shotDir, { recursive: true });
  fs.mkdirSync(videoDir, { recursive: true });

  const viewport = opts.viewport ?? { width: 1280, height: 720 };
  const launch = { headless: opts.headless ?? process.env.HEADED !== "1" };
  let browser;
  let browserName;
  const engine = opts.browserType ?? "chromium"; // "chromium" | "webkit" (≈ Safari) | "firefox"
  if (engine === "chromium") {
    try {
      browser = await pw.chromium.launch({ ...launch, channel: process.env.E2E_CHANNEL ?? "msedge" });
      browserName = "Microsoft Edge (Chromium)";
    } catch {
      browser = await pw.chromium.launch(launch);
      browserName = "Chromium (Playwright)";
    }
  } else {
    browser = await pw[engine].launch(launch);
    browserName = engine === "webkit" ? "WebKit (Playwright, đại diện Safari)" : "Firefox (Playwright)";
  }
  const context = await browser.newContext({
    baseURL: BASE_URL,
    locale: "vi-VN",
    viewport,
    recordVideo: { dir: videoDir, size: viewport },
  });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on("console", (m) => m.type() === "error" && consoleErrors.push(m.text()));
  page.on("pageerror", (e) => consoleErrors.push(`pageerror: ${e.message}`));

  const apiMode = opts.api ?? id.startsWith("API-");
  const httpShots = [];
  const steps = [];
  const defects = [];
  const notes = [];
  let seq = 0;
  let failed = false;
  const startedAt = new Date();

  async function shot(name, p = page) {
    const file = `${String(++seq).padStart(2, "0")}-${slug(name) || "buoc"}.png`;
    try {
      await p.screenshot({ path: path.join(shotDir, file) });
      return `screenshots/${file}`;
    } catch (e) {
      notes.push(`Không chụp được ảnh "${name}": ${e.message}`);
      return null;
    }
  }

  const tc = {
    id,
    page,
    context,
    browser,
    baseURL: BASE_URL,
    expect,
    fixture,
    uniqueUser,
    consoleErrors,
    note: (t) => notes.push(t),
    defect: (t) => defects.push(t),
    shot,

    /**
     * Một bước test. Tự chụp ảnh sau bước (kể cả khi lỗi). Sau lỗi đầu tiên các bước còn lại
     * được đánh dấu "Bỏ qua" (trừ khi { continueOnFail: true }).
     * @param {string} name      Hành động, ví dụ "Tải baogia.pdf lên"
     * @param {string} expected  Kết quả mong đợi (ghi vào báo cáo)
     * @param {() => Promise<string|void>} fn  Trả về chuỗi mô tả kết quả thực tế (tuỳ chọn)
     */
    async step(name, expected, fn, o = {}) {
      const n = steps.length + 1;
      if (failed && !o.continueOnFail) {
        steps.push({ n, name, expected, status: "SKIP", actual: "Bỏ qua do bước trước thất bại", shots: [] });
        return;
      }
      const t0 = Date.now();
      const before = httpShots.length;
      let status = "PASS";
      let actual = "";
      try {
        const r = await fn();
        actual = typeof r === "string" ? r : "Đúng như mong đợi";
      } catch (e) {
        status = "FAIL";
        failed = true;
        actual = String(e.message ?? e).split("\n").slice(0, 6).join("\n");
      }
      const shots = httpShots.slice(before);
      if (!shots.length || status === "FAIL" || o.screenshot) {
        const s = await shot(`${status === "FAIL" ? "fail-" : ""}${name}`, o.page ?? page);
        if (s) shots.push(s);
      }
      steps.push({ n, name, expected, status, actual, shots, ms: Date.now() - t0 });
    },

    /** Quét axe-core WCAG 2.1 A/AA trên trang hiện tại; trả về danh sách vi phạm đã rút gọn. */
    async axe(p = page, tags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]) {
      const AxeBuilder = require("@axe-core/playwright").default ?? require("@axe-core/playwright");
      const r = await new AxeBuilder({ page: p }).withTags(tags).analyze();
      return r.violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        nodes: v.nodes.map((n) => n.target.join(" ")).slice(0, 5),
      }));
    },

    /** Đăng nhập dev qua giao diện (form "Tên của bạn"). */
    async login(name = uniqueUser(), role = "user") {
      await page.goto("/");
      await page.getByLabel("Tên của bạn").fill(name);
      if (role !== "user") await page.getByLabel("Vai trò").selectOption(role);
      await page.getByRole("button", { name: "Đăng nhập" }).click();
      await expect(page.getByRole("heading", { name: "Chat với tài liệu", level: 1 })).toBeVisible();
      return name;
    },
    async acceptNotice() {
      const dlg = page.getByRole("dialog", { name: /Chào mừng/ });
      await expect(dlg).toBeVisible();
      await dlg.getByRole("checkbox").check();
      await dlg.getByRole("button", { name: "Tiếp tục" }).click();
      await expect(dlg).toBeHidden();
    },
    async upload(...files) {
      await page.getByTestId("file-input").setInputFiles(files.map(fixture));
    },
    async waitReady(name) {
      await expect(page.locator(".doc-item", { hasText: name }).getByText("Sẵn sàng")).toBeVisible({
        timeout: 20_000,
      });
    },
    async ask(question) {
      const box = page.getByLabel("Câu hỏi của bạn");
      await box.fill(question);
      await box.press("Enter");
    },
    async waitAnswer(status = "complete") {
      const a = page.getByTestId("ai-message").last();
      await expect(a).toHaveAttribute("data-status", status, { timeout: 20_000 });
      return a;
    },

    /** Lấy token dev (không qua UI). roles: ["user"] | ["user","ops"] | ["user","evaluator"] */
    async apiLogin(name = uniqueUser(), roles = ["user"]) {
      const r = await context.request.post("/api/v1/dev/login", { data: { name, roles } });
      const j = await r.json();
      return { token: j.accessToken, subject: j.subject, name };
    },

    /**
     * Gọi API và hiển thị request/response lên một trang bằng chứng để chụp ảnh + vào video.
     * Không đưa JWT đầy đủ vào ảnh (chỉ 8 ký tự đầu).
     * @param {string} method @param {string} url đường dẫn (vd "/api/v1/documents")
     * @param {{token?: string, headers?: object, json?: any, multipart?: object, data?: any, label?: string}} [o]
     * @returns {Promise<{status:number, headers:object, text:string, json:any}>}
     */
    async http(method, url, o = {}) {
      const headers = { ...(o.headers ?? {}) };
      if (o.token) headers.Authorization = `Bearer ${o.token}`;
      const init = { method, headers, failOnStatusCode: false };
      if (o.json !== undefined) init.data = o.json;
      if (o.multipart) init.multipart = o.multipart;
      if (o.data !== undefined) init.data = o.data;
      const t0 = Date.now();
      const resp = await context.request.fetch(url, init);
      const ms = Date.now() - t0;
      const text = await resp.text();
      let json = null;
      try {
        json = JSON.parse(text);
      } catch {
        /* không phải JSON (ví dụ SSE) */
      }
      const rh = resp.headers();
      const shownReq = { ...headers };
      if (shownReq.Authorization) shownReq.Authorization = shownReq.Authorization.slice(0, 15) + "…";
      const body =
        o.json !== undefined
          ? JSON.stringify(o.json, null, 2)
          : o.multipart
            ? "(multipart) " + Object.keys(o.multipart).join(", ")
            : "";
      const pretty = json ? JSON.stringify(json, null, 2) : text;
      const html = `<!doctype html><meta charset=utf-8><style>
        body{font:13px/1.45 Consolas,monospace;margin:0;padding:16px;background:#0f172a;color:#e2e8f0}
        h2{margin:0 0 8px;font:600 15px system-ui;color:#93c5fd} .ok{color:#4ade80} .bad{color:#f87171}
        pre{white-space:pre-wrap;word-break:break-word;background:#1e293b;padding:10px;border-radius:6px;margin:6px 0 14px;max-height:230px;overflow:hidden}
        </style><h2>${esc(o.label ?? "HTTP")}</h2>
        <div><b>${esc(method)} ${esc(BASE_URL + url)}</b></div>
        <pre>${esc(Object.entries(shownReq).map(([k, v]) => k + ": " + v).join("\n"))}${body ? "\n\n" + esc(body) : ""}</pre>
        <div>→ <b class="${resp.status() < 400 ? "ok" : "bad"}">HTTP ${resp.status()}</b> · ${ms} ms · ${esc(rh["content-type"] ?? "")}</div>
        <pre>${esc(Object.entries(rh).filter(([k]) => /^(x-request-id|location|retry-after|cache-control|x-accel|content-security|strict-transport|x-content-type|access-control)/i.test(k)).map(([k, v]) => k + ": " + v).join("\n"))}</pre>
        <pre style="max-height:300px">${esc(pretty.slice(0, 3500))}</pre>`;
      // Chế độ API: vẽ lên trang chính để video ghi lại; chế độ UI: dùng trang tạm để không phá luồng giao diện
      const ev = apiMode ? page : await context.newPage();
      if (!apiMode) await ev.setViewportSize(viewport);
      await ev.setContent(html);
      const hs = await shot(`${o.label ?? method + " " + url}`, ev);
      if (hs) httpShots.push(hs);
      if (apiMode) await ev.waitForTimeout(700);
      else await ev.close();
      return { status: resp.status(), headers: rh, text, json };
    },

    /** Kết thúc: đóng trình duyệt (chốt video), ghi report.md và result.json. Trả về kết quả. */
    async finish(meta = {}) {
      const endedAt = new Date();
      const rest = steps.filter((s) => s.status !== "SKIP");
      const result = steps.some((s) => s.status === "FAIL")
        ? "FAIL"
        : rest.length === 0
          ? "NOT RUN"
          : "PASS";
      const video = page.video();
      await context.close();
      let videoRel = null;
      try {
        const src = await video.path();
        const dest = path.join(videoDir, `${id}.webm`);
        fs.renameSync(src, dest);
        videoRel = `video/${id}.webm`;
      } catch (e) {
        notes.push(`Không lấy được video: ${e.message}`);
      }
      await browser.close();

      const title = meta.title ?? opts.title ?? id;
      const counts = ["PASS", "FAIL", "SKIP"].map((k) => `${k}: ${steps.filter((s) => s.status === k).length}`);
      const icon = { PASS: "✅ PASS", FAIL: "❌ FAIL", SKIP: "⏭ SKIP" };
      let md = `# Test report — ${id}: ${title}\n\n`;
      md += `| Mục | Giá trị |\n|---|---|\n`;
      md += `| **Kết quả** | **${result}** |\n| Test case | [${id}](../../cases/${id}.md) |\n`;
      md += `| URL kiểm thử | ${BASE_URL} |\n| Trình duyệt | ${browserName} (${viewport.width}×${viewport.height}) |\n`;
      md += `| Bắt đầu / kết thúc | ${startedAt.toISOString()} → ${endedAt.toISOString()} (${fmt(endedAt - startedAt)}) |\n`;
      md += `| Số bước | ${counts.join(" · ")} |\n`;
      md += `| Video | ${videoRel ? `[${videoRel}](${videoRel})` : "không có"} |\n\n`;
      if (videoRel) md += `<video src="${videoRel}" controls width="720"></video>\n\n`;
      md += `## Kết quả từng bước\n\n`;
      for (const s of steps) {
        md += `### Bước ${s.n}. ${s.name} — ${icon[s.status]}\n\n`;
        md += `- **Mong đợi:** ${s.expected}\n- **Thực tế:** ${s.actual.replace(/\n/g, "\n  ")}\n`;
        for (const sh of s.shots ?? []) md += `\n![Bước ${s.n}](${sh})\n`;
        md += `\n`;
      }
      if (consoleErrors.length)
        md += `## Lỗi console của trình duyệt (${consoleErrors.length})\n\n${consoleErrors
          .slice(0, 10)
          .map((e) => `- \`${e.slice(0, 200).replace(/`/g, "'")}\``)
          .join("\n")}\n\n`;
      if (defects.length) md += `## Lỗi phát hiện\n\n${defects.map((d) => `- ${d}`).join("\n")}\n\n`;
      if (notes.length || meta.notes) md += `## Ghi chú\n\n${[...notes, ...(meta.notes ?? [])].map((n) => `- ${n}`).join("\n")}\n`;
      fs.writeFileSync(path.join(dir, "report.md"), md);
      fs.writeFileSync(
        path.join(dir, "result.json"),
        JSON.stringify({ id, title, result, baseUrl: BASE_URL, startedAt, endedAt, steps, defects, notes, consoleErrors, video: videoRel }, null, 2),
      );
      console.log(`${id}: ${result}  →  tests/reports/${id}/report.md`);
      return result;
    },
  };
  return tc;
}
