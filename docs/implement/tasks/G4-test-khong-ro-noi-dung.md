# G4 — Test không rò nội dung vào log và telemetry

| Thuộc tính | Giá trị |
|---|---|
| Workstream | G — Chất lượng & bảo mật |
| Sprint | S4 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | QA |
| Story liên quan | — (nền tảng) |
| Trạng thái | Hoàn thành (test_no_content_leak.py: log, metrics, telemetry, audit, đường lỗi nhà cung cấp); chưa quét log của hạ tầng thật/trace backend |

## Mô tả

Bảo đảm tuân thủ PRD 5.2.

## Phạm vi

- Chạy kịch bản e2e với chuỗi ‘canary’ đặc biệt trong câu hỏi, nội dung PDF và tên tệp.
- Quét toàn bộ log (api, worker, proxy) và bảng `telemetry_events`, span trace: không có canary.
- Tích hợp vào CI.

## Hướng dẫn kỹ thuật

- Canary khác nhau cho từng nguồn để xác định điểm rò.
- Thất bại là blocker phát hành.

## Đầu ra / sản phẩm bàn giao

- Test quét canary.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A6](A6-logging-metrics-tracing.md) — Logging có allow-list, metrics và tracing
- [B10](B10-api-telemetry.md) — API telemetry
- [G2](G2-test-tich-hop.md) — Test tích hợp với Postgres và MinIO

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Không tìm thấy canary ở log/telemetry/trace.
- [ ] Chạy tự động trong CI.
- [ ] Có hướng dẫn xử lý khi phát hiện rò.

## Kiểm thử

- Chính task này là test.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 5.3, DC-06
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
