# C7 — Đo hiệu năng xử lý PDF (≤ 60s)

| Thuộc tính | Giá trị |
|---|---|
| Workstream | C — Ingestion |
| Sprint | S4 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE/QA |
| Story liên quan | US-101 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Xác nhận mục tiêu xử lý PDF ≤ 60s và tìm điểm nghẽn.

## Phạm vi

- Bộ PDF chuẩn theo kích cỡ (10, 50, 200 trang) cùng giới hạn trong cấu hình.
- Script benchmark đo thời gian từng giai đoạn.
- Tối ưu nếu vượt: kích thước lô embed, song song hóa, số worker.
- Ghi kết quả vào báo cáo.

## Hướng dẫn kỹ thuật

- Đo với embedding thật khi đã chọn nhà cung cấp.
- Giới hạn trang tối đa phụ thuộc kết quả (OQ-008).

## Đầu ra / sản phẩm bàn giao

- Báo cáo hiệu năng ingest.

## Phụ thuộc

**Cần hoàn thành trước:**
- [C6](C6-worker-ingest-ghi-chi-muc.md) — Worker ingest end-to-end và ghi chỉ mục

**Mở khóa:**
- [G7](G7-test-hieu-nang.md) — Test hiệu năng (token đầu, xử lý PDF)

## Tiêu chí chấp nhận

- [ ] Báo cáo thời gian theo giai đoạn.
- [ ] PDF điển hình (mục tiêu theo OQ-008) xử lý ≤ 60s ở p95.
- [ ] Đề xuất giới hạn trang nếu vượt.

## Kiểm thử

- Chạy benchmark lặp lại trên staging.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 2.4 (hiệu năng)
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
