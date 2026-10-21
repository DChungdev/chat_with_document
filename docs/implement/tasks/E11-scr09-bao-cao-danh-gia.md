# E11 — SCR-09 Báo cáo đánh giá MVP

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S4 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE |
| Story liên quan | US-501 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Trang báo cáo cho Minh: MET-001/MET-002, so sánh baseline/mục tiêu.

## Phạm vi

- Hiển thị dữ liệu đầu vào, kết quả MET-001/002, so với baseline/mục tiêu.
- Ghi rõ ‘chưa thể kết luận’ khi mục tiêu chưa được duyệt.
- Chỉ vai trò `evaluator` truy cập; không hiển thị nội dung tài liệu/câu hỏi.
- Biểu đồ đơn giản, có bảng số liệu thay thế cho trợ năng.

## Hướng dẫn kỹ thuật

- Hình thức báo cáo (trang web hay dashboard riêng) **[TBD: OQ-005]**; làm trang web đơn giản trước.
- Tham khảo skill dataviz nếu dựng biểu đồ.

## Đầu ra / sản phẩm bàn giao

- Trang SCR-09.

## Phụ thuộc

**Cần hoàn thành trước:**
- [F1](F1-truy-van-met-bao-cao.md) — Truy vấn MET-001/MET-002 và endpoint báo cáo
- [E1](E1-khoi-tao-spa.md) — Khởi tạo SPA, routing, API client và design tokens

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Minh xem được số liệu MET-001/002 từ dữ liệu thử.
- [ ] Người dùng thường không vào được.
- [ ] Hiện cảnh báo khi mục tiêu chưa duyệt.

## Kiểm thử

- Component test với dữ liệu giả; e2e kiểm quyền.

## Tham chiếu

- Prototype: [report.html](../../design/UI_UX_design/report.html)
- [User_Stories.html](../../requirements/User_Stories.html) US-501
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
