# E2 — SCR-01 Màn chào và thông báo dữ liệu

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S2 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE |
| Story liên quan | US-401 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Màn đầu tiên bắt người dùng đọc và đồng ý thông báo dữ liệu trước khi tải tệp.

## Phạm vi

- Hiển thị nội dung thông báo từ API (loại tài liệu được phép/cấm, cách xử lý dữ liệu).
- Checkbox đồng ý; nút ‘Tiếp tục’ bị tắt đến khi tích chọn.
- Gọi accept → vào màn chính; lưu trạng thái đã xác nhận.
- Nút ‘Thông báo dữ liệu’ trên header luôn mở được lại nội dung.
- Gửi sự kiện `data_notice_accepted`.

## Hướng dẫn kỹ thuật

- Nội dung thông báo **[TBD: OQ-012, OQ-013]** — đừng hard-code; lấy từ API.
- Hỗ trợ bàn phím và đọc màn hình (nhãn checkbox liên kết).

## Đầu ra / sản phẩm bàn giao

- Trang SCR-01.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B6](B6-compliance-thong-bao-du-lieu.md) — Compliance: xác nhận thông báo dữ liệu
- [E1](E1-khoi-tao-spa.md) — Khởi tạo SPA, routing, API client và design tokens

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Chưa tích → nút Tiếp tục bị tắt.
- [ ] Xác nhận thành công → chuyển SCR-02.
- [ ] Tải lại trang không phải xác nhận lại nếu phiên bản không đổi.
- [ ] Header luôn có nút xem lại thông báo.

## Kiểm thử

- Component test; e2e luồng xác nhận.

## Tham chiếu

- Prototype: [app.html](../../design/UI_UX_design/app.html)#SCR-01
- [User_Stories.html](../../requirements/User_Stories.html) US-401
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
