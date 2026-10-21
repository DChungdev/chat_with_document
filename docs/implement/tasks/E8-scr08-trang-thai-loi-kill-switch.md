# E8 — Trạng thái lỗi và banner kill switch

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S3 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE |
| Story liên quan | US-201, US-202 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Hiển thị rõ các trạng thái bất thường của hỏi đáp.

## Phạm vi

- Trạng thái ‘Không tìm thấy trong tài liệu đã tải’ (`grounded=false`).
- Message `Interrupted`/`Failed` với nút thử lại; câu hỏi gốc không mất.
- Banner khi `QA_DISABLED` (SCR-08) và tắt ô chat; nhận biết qua `GET /status` và mã `503`.
- Sự kiện `answer_failed`.

## Hướng dẫn kỹ thuật

- Thông điệp lỗi thân thiện, không lộ chi tiết kỹ thuật.
- Banner không che nội dung; có thể truy cập bằng bàn phím.

## Đầu ra / sản phẩm bàn giao

- Thành phần trạng thái lỗi và banner.

## Phụ thuộc

**Cần hoàn thành trước:**
- [E6](E6-scr04-khung-chat-sse.md) — SCR-04 Khung chat và streaming SSE

**Mở khóa:**
- [E12](E12-a11y-da-trinh-duyet.md) — Tiếp cận (a11y) và kiểm thử đa trình duyệt

## Tiêu chí chấp nhận

- [ ] Mô phỏng lỗi LLM → hiển thị thông báo + thử lại.
- [ ] Kill switch bật → banner và ô chat tắt.
- [ ] ‘Không tìm thấy’ có biểu hiện khác câu trả lời bình thường.

## Kiểm thử

- Component test cho từng trạng thái; e2e với API giả.

## Tham chiếu

- Prototype: [app.html](../../design/UI_UX_design/app.html)#SCR-08
- [User_Stories.html](../../requirements/User_Stories.html) US-201
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
