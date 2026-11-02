// Sinh tests/CHECKLIST.md từ tests/cases/*.md và tests/reports/*/result.json
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const groups = { API: "API", E2E: "E2E giao diện", SEC: "Bảo mật", ACC: "Khả năng tiếp cận", UI: "UI/UX", RAG: "Chất lượng RAG", OPS: "Vận hành", PERF: "Hiệu năng (chỉ báo)" };
const cases = fs.readdirSync(path.join(root, "cases")).filter((f) => /^[A-Z0-9]+-\d+\.md$/.test(f)).sort();
const info = (id) => {
  const t = fs.readFileSync(path.join(root, "cases", `${id}.md`), "utf8");
  return { title: t.match(/^# \S+ — (.+)$/m)?.[1] ?? "", prio: t.match(/\*\*Ưu tiên\*\* \| (\S+)/)?.[1] ?? "" };
};
const res = (id) => {
  const f = path.join(root, "reports", id, "result.json");
  return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf8")) : null;
};
let pass = 0, fail = 0, todo = 0;
let body = "";
for (const [g, name] of Object.entries(groups)) {
  const ids = cases.map((f) => f.replace(".md", "")).filter((id) => id.startsWith(g + "-"));
  body += `\n## ${name}\n\n| ✔ | ID | Tên | Ưu tiên | Kết quả | Report |\n|---|---|---|---|---|---|\n`;
  for (const id of ids) {
    const { title, prio } = info(id);
    const r = res(id);
    let box = "[ ]", st = "Chưa chạy", link = "";
    if (r) {
      link = `[report](reports/${id}/report.md)`;
      if (r.result === "PASS") { box = "[x]"; st = "✅ PASS"; pass++; }
      else { box = "[ ]"; st = "❌ FAIL"; fail++; }
    } else todo++;
    body += `| ${box} | [${id}](cases/${id}.md) | ${title} | ${prio} | ${st} | ${link} |\n`;
  }
}
const head = `# Checklist thực thi test case\n\nCập nhật: ${new Date().toISOString().slice(0, 10)} · URL http://127.0.0.1:8000 · Tổng ${cases.length} case: ✅ ${pass} PASS · ❌ ${fail} FAIL · ⬜ ${todo} chưa chạy\n\n> \`[x]\` = đã chạy và PASS; \`[ ]\` = FAIL hoặc chưa chạy (xem cột Kết quả). Sinh lại bằng \`node tests/tools/checklist.mjs\` sau mỗi lần chạy.\n`;
fs.writeFileSync(path.join(root, "CHECKLIST.md"), head + body);
console.log(`CHECKLIST.md: ${cases.length} case (PASS ${pass}, FAIL ${fail}, chưa chạy ${todo})`);
