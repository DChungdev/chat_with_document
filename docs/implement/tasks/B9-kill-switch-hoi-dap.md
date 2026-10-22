# B9 — Kill switch hỏi đáp

| Thuộc tính | Giá trị |
|---|---|
| Workstream | B — Backend lõi |
| Sprint | S3 |
| Cỡ ước lượng | S (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE |
| Story liên quan | US-201 |
| Trạng thái | Hoàn thành — chặn ở ChatService + `PUT /admin/flags/qa-enabled` (role ops); trạng thái cờ có trong `GET /config` (không có `GET /status` riêng) |

## Mô tả

Tắt khẩn cấp tính năng hỏi đáp mà không cần deploy.

## Phạm vi

- Khi `qa_enabled=false`, mọi endpoint hỏi đáp trả `503` mã `QA_DISABLED`.
- Endpoint công khai nhẹ (`GET /api/v1/status`) cho FE biết trạng thái để hiện banner (SCR-08).
- Tải/xem/xóa tài liệu vẫn hoạt động.

## Hướng dẫn kỹ thuật

- Kiểm cờ ở đầu use case chat, trước mọi truy cập dữ liệu/dịch vụ ngoài.

## Đầu ra / sản phẩm bàn giao

- Dependency/guard kill switch.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A5](A5-cau-hinh-feature-flag.md) — Cấu hình, secret và feature flag

**Mở khóa:**
- [B7](B7-api-hoi-dap-sse.md) — API hội thoại và hỏi đáp qua SSE

## Tiêu chí chấp nhận

- [ ] Cờ tắt → 503 `QA_DISABLED`.
- [ ] Cờ tắt → upload vẫn OK.
- [ ] Bật lại → hoạt động bình thường.

## Kiểm thử

- Integration test bật/tắt cờ.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 5.2
- SCR-08
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
