# G7 — Test hiệu năng (token đầu, xử lý PDF)

| Thuộc tính | Giá trị |
|---|---|
| Workstream | G — Chất lượng & bảo mật |
| Sprint | S5 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | QA |
| Story liên quan | US-201 |
| Trạng thái | Một phần — script đo cục bộ (adapter giả) + k6 cho staging + báo cáo docs/implement/reports/performance.md. CHƯA đo được p95 ≤ 5s thật (cần Claude + pgvector trên staging) |

## Mô tả

Xác nhận mục tiêu hiệu năng của PRD 5.1.

## Phạm vi

- Đo thời gian tới token đầu với ≤ 10 PDF: mục tiêu ≤ 5s ở p95.
- Đo thời gian xử lý PDF: ≤ 60s.
- Tải thử vài chục người dùng đồng thời [Đề xuất].
- Báo cáo kết quả và điểm nghẽn.

## Hướng dẫn kỹ thuật

- Chạy trên staging với dịch vụ LLM/embedding thật.
- Ngưỡng là đề xuất đến khi OQ-011 được chốt.

## Đầu ra / sản phẩm bàn giao

- Báo cáo hiệu năng.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B7](B7-api-hoi-dap-sse.md) — API hội thoại và hỏi đáp qua SSE
- [C7](C7-do-hieu-nang-ingest.md) — Đo hiệu năng xử lý PDF (≤ 60s)

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] p95 token đầu ≤ 5s hoặc có kế hoạch khắc phục.
- [ ] Thời gian xử lý PDF đạt mục tiêu.
- [ ] Báo cáo lưu trong tài liệu.

## Kiểm thử

- Chạy k6/Locust trên staging.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 2.4, DC-03
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
