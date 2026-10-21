# E12 — Tiếp cận (a11y) và kiểm thử đa trình duyệt

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S5 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE/QA |
| Story liên quan | — (nền tảng) |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Đảm bảo giao diện dùng được bằng bàn phím/trình đọc màn hình và chạy đúng trên trình duyệt hỗ trợ.

## Phạm vi

- Rà soát WCAG 2.1 AA: tương phản, focus nhìn thấy, thứ tự tab, nhãn ARIA, vùng live cho stream trả lời.
- Kiểm bàn phím toàn luồng: tải, hỏi, mở nguồn, xóa.
- Chạy axe tự động trong CI.
- Kiểm thử thủ công Chrome, Edge, Safari (2 phiên bản gần nhất).

## Hướng dẫn kỹ thuật

- Vùng stream dùng `aria-live=polite` nhưng tránh đọc từng token (gom theo câu).
- Tôn trọng `prefers-reduced-motion`.

## Đầu ra / sản phẩm bàn giao

- Báo cáo a11y + sửa lỗi.

## Phụ thuộc

**Cần hoàn thành trước:**
- [E6](E6-scr04-khung-chat-sse.md) — SCR-04 Khung chat và streaming SSE
- [E7](E7-scr05-chip-trich-dan-panel-nguon.md) — Chip trích dẫn và panel nguồn
- [E8](E8-scr08-trang-thai-loi-kill-switch.md) — Trạng thái lỗi và banner kill switch

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Không còn lỗi axe mức nghiêm trọng.
- [ ] Toàn bộ luồng P0 làm được chỉ bằng bàn phím.
- [ ] Chạy đúng trên 3 trình duyệt mục tiêu.

## Kiểm thử

- axe + Playwright; checklist thủ công.

## Tham chiếu

- [UIUX_Blueprint_SDD.md](../../design/UIUX_Blueprint_SDD.md) (trợ năng)
- SAD DC-01
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
