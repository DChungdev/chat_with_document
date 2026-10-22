// G7: tải trên staging (hạ tầng THẬT: Postgres, LLM, embedding). Chạy:
//   k6 run -e BASE=https://staging.example -e TOKEN_FILE=tokens.json deploy/perf/k6-chat.js
// tokens.json: ["<jwt người dùng 1>", ...] — mỗi VU dùng 1 người dùng đã có ≥1 tài liệu ready và đã xác nhận thông báo.
// Ngưỡng bám mục tiêu SAD 5.1: p95 token đầu ≤ 5s (với 20 người dùng đồng thời), tỷ lệ lỗi < 1%.
import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";
import { SharedArray } from "k6/data";

const tokens = new SharedArray("tokens", () => JSON.parse(open(__ENV.TOKEN_FILE)));
const firstToken = new Trend("first_token_ms", true);
const failed = new Rate("answer_failed");
const BASE = __ENV.BASE;
const QUESTIONS = ["Điều khoản thanh toán là gì?", "Thời hạn bảo hành bao lâu?", "Phí bảo trì bao nhiêu?"];

export const options = {
  scenarios: { chat: { executor: "constant-vus", vus: Number(__ENV.VUS || 20), duration: __ENV.DURATION || "5m" } },
  thresholds: {
    first_token_ms: ["p(95)<15000"], // tổng thời gian trả lời; siết lại về 5s khi dùng xk6-sse đo token đầu
    answer_failed: ["rate<0.01"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const h = { Authorization: `Bearer ${tokens[(__VU - 1) % tokens.length]}`, "Content-Type": "application/json" };
  const conv = http.post(`${BASE}/api/v1/conversations`, null, { headers: h });
  if (!check(conv, { "tạo hội thoại 201": (r) => r.status === 201 })) return failed.add(1);
  const id = conv.json("id");
  const t0 = Date.now();
  // k6 không đọc SSE theo từng sự kiện. TTFB (timings.waiting) là sự kiện `message` gửi ngay, KHÔNG phải token đầu,
  // nên dùng tổng thời gian trả lời (timings.duration) làm CHẶN TRÊN của thời gian tới token đầu.
  // Cần xk6-sse để đo chính xác sự kiện `token` đầu tiên.
  const r = http.post(`${BASE}/api/v1/conversations/${id}/messages`, JSON.stringify({ question: QUESTIONS[Math.floor(Math.random() * QUESTIONS.length)] }), { headers: h });
  const ok = check(r, { "200": (x) => x.status === 200, "có done": (x) => x.body.includes("event: done") });
  failed.add(!ok);
  firstToken.add(r.timings.duration); // chặn trên — xem chú thích
  sleep(1 + Math.random() * 2);
  void t0;
}
