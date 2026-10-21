# B5 — Chuẩn lỗi RFC 7807 và rate limit

| Thuộc tính | Giá trị |
|---|---|
| Workstream | B — Backend lõi |
| Sprint | S2 |
| Cỡ ước lượng | S (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE |
| Story liên quan | — (nền tảng) |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Thống nhất định dạng lỗi và chống lạm dụng theo người dùng.

## Phạm vi

- Exception handler trả `application/problem+json` (`type`, `title`, `status`, `code`, `detail`, `trace_id`).
- Rate limit theo `user_id`: 30 câu hỏi/phút, 20 tải lên/giờ [Đề xuất]; trả `429` kèm `Retry-After`.
- Danh mục mã lỗi dùng chung cho FE.

## Hướng dẫn kỹ thuật

- Lưu bộ đếm trong Postgres hoặc bộ nhớ tiến trình (MVP); không thêm Redis.
- `detail` không chứa nội dung người dùng.

## Đầu ra / sản phẩm bàn giao

- Middleware lỗi + rate limit.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B4](B4-api-tai-lieu.md) — API tài liệu: tải lên, liệt kê, chi tiết

**Mở khóa:**
- [G8](G8-ra-soat-bao-mat.md) — Rà soát bảo mật

## Tiêu chí chấp nhận

- [ ] Lỗi miền ánh xạ đúng mã HTTP.
- [ ] Vượt rate limit → 429 + `Retry-After`.
- [ ] Mọi lỗi có `trace_id`.

## Kiểm thử

- Unit/integration test handler và giới hạn.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 5.1 (chống lạm dụng)
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
