# E9 — SCR-07 Overlay hết phiên và giữ bản nháp

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S2 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE |
| Story liên quan | US-402 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Khi phiên hết hạn, yêu cầu đăng nhập lại mà không mất câu hỏi đang soạn.

## Phạm vi

- Overlay hết phiên khi API trả `401`.
- Lưu bản nháp câu hỏi (sessionStorage/bộ nhớ) và khôi phục sau đăng nhập.
- Nút ‘Đăng nhập lại’ — khung trung lập, nối với cơ chế thật khi chốt OQ-014.

## Hướng dẫn kỹ thuật

- Nội dung bản nháp chỉ lưu cục bộ, không gửi telemetry.
- Xóa bản nháp sau khi gửi thành công hoặc đăng xuất.

## Đầu ra / sản phẩm bàn giao

- Overlay SCR-07.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B3](B3-xac-thuc-authprovider.md) — Xác thực JWT và AuthProvider
- [E1](E1-khoi-tao-spa.md) — Khởi tạo SPA, routing, API client và design tokens

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] 401 → overlay hiển thị, không mất bản nháp.
- [ ] Sau đăng nhập lại bản nháp được khôi phục.
- [ ] Không có dữ liệu nhạy cảm trong storage sau đăng xuất.

## Kiểm thử

- Component test; e2e với token hết hạn.

## Tham chiếu

- Prototype: [app.html](../../design/UI_UX_design/app.html)#SCR-07
- [User_Stories.html](../../requirements/User_Stories.html) US-402
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
