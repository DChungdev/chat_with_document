# E4 — SCR-03 Danh sách tài liệu và trạng thái

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S2 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE |
| Story liên quan | US-102, US-101 |
| Trạng thái | Hoàn thành ở chế độ local — có vitest + Playwright (Edge) + axe; chưa chạy trên Chrome/Firefox/Safari, chưa có Claude/backend PG thật |

## Mô tả

Danh sách tài liệu với trạng thái xử lý cập nhật tự động.

## Phạm vi

- Mỗi dòng: tên, kích thước, thời điểm tải, trạng thái (Đang xử lý / Sẵn sàng / Lỗi) bằng biểu tượng + chữ; thanh tiến trình khi xử lý.
- Polling `GET /documents` (khoảng 2–3 giây khi có tài liệu `processing`, dừng khi không còn); không cần tải lại trang.
- Lỗi hiển thị riêng từng tệp với mã/thông điệp thân thiện.
- Menu ⋯ → Xóa (mở SCR-06).
- Cho phép hỏi trên tệp ‘Sẵn sàng’ khi tệp khác còn đang xử lý.

## Hướng dẫn kỹ thuật

- Checkbox chọn tệp là US-104 (P1): để cấu trúc dữ liệu sẵn nhưng ẩn/khóa.
- Dùng cache dữ liệu (React Query) để polling gọn.

## Đầu ra / sản phẩm bàn giao

- Thành phần DocumentList.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B4](B4-api-tai-lieu.md) — API tài liệu: tải lên, liệt kê, chi tiết
- [E3](E3-scr02-man-chinh-rong-tai-len.md) — SCR-02 Màn chính trạng thái rỗng và tải lên

**Mở khóa:**
- [E5](E5-scr06-xac-nhan-xoa.md) — SCR-06 Hộp thoại xác nhận xóa tài liệu

## Tiêu chí chấp nhận

- [ ] Trạng thái tự chuyển ‘Sẵn sàng’ không cần reload.
- [ ] Lỗi ở một tệp không ảnh hưởng hiển thị tệp khác.
- [ ] Trạng thái không chỉ dựa vào màu.

## Kiểm thử

- Component test với dữ liệu giả; e2e polling với API giả.

## Tham chiếu

- Prototype: [app.html](../../design/UI_UX_design/app.html)#SCR-03
- [User_Stories.html](../../requirements/User_Stories.html) US-102
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
