# A6 — Logging có allow-list, metrics và tracing

| Thuộc tính | Giá trị |
|---|---|
| Workstream | A — Nền tảng & hạ tầng |
| Sprint | S1 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | DevOps/BE |
| Story liên quan | — (nền tảng) |
| Trạng thái | Hoàn thành — có unit test; quét log bằng canary là G4 |

## Mô tả

Thiết lập khả năng quan sát ngay từ đầu, bảo đảm không rò nội dung người dùng (PRD 5.2).

## Phạm vi

- Logger JSON có cấu trúc với **allow-list trường** (vd. `ts`, `level`, `trace_id`, `route`, `status`, `duration_ms`, `user_hash`, `stage`, `error_code`).
- Bất kỳ trường ngoài allow-list bị loại hoặc thay bằng `[redacted]`.
- Metrics Prometheus: độ trễ API, thời gian tới token đầu, độ dài hàng đợi ingest, thời gian xử lý PDF, tỷ lệ lỗi theo `stage`, tỷ lệ `grounded=false`.
- OpenTelemetry tracing, propagate `trace_id` sang worker; **không** gắn nội dung vào span.
- Endpoint `/metrics` (chỉ mạng nội bộ) và `/health`.

## Hướng dẫn kỹ thuật

- Tuyệt đối không log `question`, `snippet`, nội dung PDF, tên tệp.
- Cung cấp helper `log_safe()`; chặn trực tiếp log `request.body`.
- `user_hash` là băm một chiều có muối của `user_id`.

## Đầu ra / sản phẩm bàn giao

- Module `infra/observability`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A1](A1-khoi-tao-monorepo-ci.md) — Khởi tạo monorepo, lint/format và CI

**Mở khóa:**
- [A7](A7-staging-pipeline-trien-khai.md) — Staging và pipeline triển khai
- [F2](F2-dashboard-canh-bao.md) — Dashboard và cảnh báo vận hành
- [G4](G4-test-khong-ro-noi-dung.md) — Test không rò nội dung vào log và telemetry

## Tiêu chí chấp nhận

- [ ] Log thử với trường `question` → không xuất hiện trong đầu ra.
- [ ] `/metrics` hiển thị các metric nêu trên (giá trị 0 ban đầu).
- [ ] `trace_id` xuất hiện ở log api và worker cho cùng một job.

## Kiểm thử

- Unit test filter allow-list; test quét log sau chạy e2e (xem G4).

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 5.3, DC-06
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
