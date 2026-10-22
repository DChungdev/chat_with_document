# E5 — SCR-06 Hộp thoại xác nhận xóa tài liệu

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S2 |
| Cỡ ước lượng | S (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE |
| Story liên quan | US-103 |
| Trạng thái | Hoàn thành ở chế độ local — có vitest + Playwright (Edge) + axe; chưa chạy trên Chrome/Firefox/Safari, chưa có Claude/backend PG thật |

## Mô tả

Xóa một tài liệu trong ≤ 2 thao tác (⋯ → Xóa → Xác nhận).

## Phạm vi

- Dialog xác nhận nêu rõ hậu quả (câu hỏi mới không còn dùng tài liệu này).
- Gọi `DELETE`, cập nhật danh sách, toast thành công.
- Liên kết hướng dẫn báo cáo khi tải nhầm tài liệu nhạy cảm.
- Sự kiện `document_deleted`.

## Hướng dẫn kỹ thuật

- Focus trap và Esc đóng; focus trả về nút ⋯.
- Xử lý lỗi xóa (thử lại).

## Đầu ra / sản phẩm bàn giao

- Dialog xóa.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B11](B11-xoa-tai-lieu.md) — Xóa tài liệu
- [E4](E4-scr03-danh-sach-tai-lieu.md) — SCR-03 Danh sách tài liệu và trạng thái

**Mở khóa:**
- [G6](G6-e2e-luong-p0.md) — E2E các luồng P0 (Playwright)

## Tiêu chí chấp nhận

- [ ] Xác nhận → tệp biến mất khỏi danh sách.
- [ ] Hủy → không thay đổi.
- [ ] Lỗi API hiển thị thông báo và cho thử lại.

## Kiểm thử

- Component test; e2e xóa.

## Tham chiếu

- Prototype: [app.html](../../design/UI_UX_design/app.html)#SCR-06
- [User_Stories.html](../../requirements/User_Stories.html) US-103
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
