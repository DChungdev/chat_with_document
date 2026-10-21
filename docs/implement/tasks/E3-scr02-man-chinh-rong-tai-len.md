# E3 — SCR-02 Màn chính trạng thái rỗng và tải lên

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S2 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE |
| Story liên quan | US-101, US-201 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Màn chính khi chưa có tài liệu: khu vực tải PDF, giới hạn tệp và ô chat bị tắt kèm lý do.

## Phạm vi

- Nút ‘Tải PDF đầu tiên’ và chọn nhiều tệp.
- Validate phía client: định dạng, kích thước, số lượng (giới hạn lấy từ cấu hình/API).
- Hiển thị giới hạn cho phép; lỗi nêu rõ lý do.
- Ô chat tắt kèm câu hướng dẫn ‘tải PDF trước’.
- Gửi sự kiện `upload_started`/`upload_succeeded`/`upload_failed`.

## Hướng dẫn kỹ thuật

- Giới hạn tệp **[TBD: OQ-008]** đọc từ cấu hình, không hard-code.
- Khóa tải lên nếu chưa xác nhận thông báo (điều hướng về SCR-01).
- DropZone kéo-thả là P2 (US-105) — chừa chỗ.

## Đầu ra / sản phẩm bàn giao

- Trang SCR-02, thành phần Upload.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B4](B4-api-tai-lieu.md) — API tài liệu: tải lên, liệt kê, chi tiết
- [E1](E1-khoi-tao-spa.md) — Khởi tạo SPA, routing, API client và design tokens

**Mở khóa:**
- [E4](E4-scr03-danh-sach-tai-lieu.md) — SCR-03 Danh sách tài liệu và trạng thái

## Tiêu chí chấp nhận

- [ ] Chọn PDF hợp lệ → tệp xuất hiện ở danh sách trạng thái ‘Đang xử lý’ trong ≤ 2 giây.
- [ ] Tệp sai định dạng/quá giới hạn bị từ chối kèm lý do, không ảnh hưởng tệp khác.
- [ ] Ô chat tắt khi chưa có tài liệu sẵn sàng.

## Kiểm thử

- Component test validate; e2e tải một tệp.

## Tham chiếu

- Prototype: [app.html](../../design/UI_UX_design/app.html)#SCR-02
- [User_Stories.html](../../requirements/User_Stories.html) US-101
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
