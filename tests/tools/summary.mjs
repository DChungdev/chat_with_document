// Gom tests/reports/*/result.json → tests/reports/SUMMARY.md
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const reports = path.join(root, "reports");
const rows = [];
for (const id of fs.readdirSync(reports).sort()) {
  const f = path.join(reports, id, "result.json");
  if (!fs.existsSync(f)) continue;
  const r = JSON.parse(fs.readFileSync(f, "utf8"));
  const shotDir = path.join(reports, id, "screenshots");
  const shots = fs.existsSync(shotDir) ? fs.readdirSync(shotDir).length : 0;
  rows.push({ id, title: r.title, result: r.result, steps: r.steps.length, shots, video: !!r.video, defects: r.defects.length });
}
const count = (k) => rows.filter((r) => r.result === k).length;
let md = `# Tổng hợp kết quả kiểm thử\n\nTạo lúc ${new Date().toISOString()} · ${rows.length} test case đã chạy (PASS ${count("PASS")} · FAIL ${count("FAIL")} · NOT RUN ${count("NOT RUN")})\n\n`;
md += `| ID | Tên | Kết quả | Bước | Ảnh | Video | Lỗi | Báo cáo |\n|---|---|---|---|---|---|---|---|\n`;
for (const r of rows) {
  const res = r.result === "PASS" ? "✅ PASS" : r.result === "FAIL" ? "❌ FAIL" : r.result;
  md += `| ${r.id} | ${r.title} | ${res} | ${r.steps} | ${r.shots} | ${r.video ? "✔" : "✘"} | ${r.defects} | [report](${r.id}/report.md) |\n`;
}
fs.writeFileSync(path.join(reports, "SUMMARY.md"), md);
console.log(`SUMMARY.md: ${rows.length} case`);
