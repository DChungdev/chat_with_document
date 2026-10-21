# G6 — E2E các luồng P0 (Playwright)

| Thuộc tính | Giá trị |
|---|---|
| Workstream | G — Chất lượng & bảo mật |
| Sprint | S5 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | QA |
| Story liên quan | US-101, US-102, US-103, US-201, US-202, US-301, US-302, US-401 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Kịch bản người dùng Lan từ đầu đến cuối chạy tự động.

## Phạm vi

- Luồng: xác nhận thông báo → tải PDF → chờ ‘Sẵn sàng’ → hỏi → xem câu trả lời & chip → mở panel nguồn → xóa tài liệu.
- Luồng ngoài phạm vi: nhận ‘không tìm thấy’.
- Luồng lỗi: tệp sai định dạng, kill switch bật, hết phiên.
- Chạy với FakeLLM/FakeEmbedding trong CI; một lượt smoke với dịch vụ thật trên staging.

## Hướng dẫn kỹ thuật

- Dữ liệu và môi trường dựng lại được; trace/video khi thất bại.

## Đầu ra / sản phẩm bàn giao

- Bộ e2e Playwright.

## Phụ thuộc

**Cần hoàn thành trước:**
- [E6](E6-scr04-khung-chat-sse.md) — SCR-04 Khung chat và streaming SSE
- [E7](E7-scr05-chip-trich-dan-panel-nguon.md) — Chip trích dẫn và panel nguồn
- [E5](E5-scr06-xac-nhan-xoa.md) — SCR-06 Hộp thoại xác nhận xóa tài liệu

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Mọi luồng liệt kê chạy xanh.
- [ ] Smoke trên staging thành công.
- [ ] Thất bại để lại trace phục vụ gỡ lỗi.

## Kiểm thử

- Chính task này là test; chạy lặp để loại flaky.

## Tham chiếu

- User_Stories.html (AC của US P0)
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
