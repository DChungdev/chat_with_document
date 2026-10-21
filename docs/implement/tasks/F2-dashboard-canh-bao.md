# F2 — Dashboard và cảnh báo vận hành

| Thuộc tính | Giá trị |
|---|---|
| Workstream | F — Đo lường |
| Sprint | S5 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | DevOps |
| Story liên quan | — (nền tảng) |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Giám sát sức khỏe hệ thống và cảnh báo sớm.

## Phạm vi

- Dashboard Grafana: p95 độ trễ API, thời gian tới token đầu, độ dài hàng đợi ingest, thời gian xử lý PDF, tỷ lệ lỗi theo giai đoạn, tỷ lệ `grounded=false`.
- Cảnh báo: p95 token đầu > 5s; `answer_failed` cao; hàng đợi ingest tồn đọng; lỗi nhà cung cấp LLM/Embedding.
- Kênh nhận cảnh báo (email/chat) cấu hình được.
- Diễn tập kill switch.

## Hướng dẫn kỹ thuật

- Ngưỡng cảnh báo là đề xuất; hiệu chỉnh sau khi có dữ liệu staging.
- Dashboard không hiển thị nội dung người dùng.

## Đầu ra / sản phẩm bàn giao

- Cấu hình dashboard + rule cảnh báo.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A6](A6-logging-metrics-tracing.md) — Logging có allow-list, metrics và tracing

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Dashboard hiển thị đủ metric.
- [ ] Cảnh báo kích hoạt khi mô phỏng vượt ngưỡng.
- [ ] Diễn tập kill switch thành công.

## Kiểm thử

- Mô phỏng sự cố trên staging.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 5.3
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
