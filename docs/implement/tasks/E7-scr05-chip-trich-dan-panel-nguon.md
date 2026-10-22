# E7 — Chip trích dẫn và panel nguồn

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S3 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE |
| Story liên quan | US-301, US-302, US-203 |
| Trạng thái | Hoàn thành ở chế độ local — có vitest + Playwright (Edge) + axe; chưa chạy trên Chrome/Firefox/Safari, chưa có Claude/backend PG thật |

## Mô tả

Hiển thị trích dẫn dưới câu trả lời và panel xem đoạn gốc để kiểm chứng.

## Phạm vi

- Chip ‘tên tệp · tr.N’ dưới câu trả lời; nhiều chip từ nhiều tệp.
- Bấm chip mở panel bên phải: đoạn gốc + tên tệp + trang; gọi `GET /citations/{id}`.
- Dưới 1024px panel thành bottom sheet.
- Esc đóng và trả focus về chip; không điều hướng ra khỏi trang.
- Nguồn không còn khả dụng → hiển thị ‘Nguồn không còn khả dụng’.
- Sự kiện `citation_opened`.

## Hướng dẫn kỹ thuật

- Highlight cụm từ trùng nếu có thể (không bắt buộc).
- Chip có nhãn đọc màn hình đầy đủ.
- Nút ‘Mở PDF tại trang này’ là P2 (US-303) — chừa chỗ.

## Đầu ra / sản phẩm bàn giao

- Thành phần CitationChip, SourcePanel.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B8](B8-api-xem-nguon-dan.md) — API xem nguồn dẫn
- [E6](E6-scr04-khung-chat-sse.md) — SCR-04 Khung chat và streaming SSE

**Mở khóa:**
- [E12](E12-a11y-da-trinh-duyet.md) — Tiếp cận (a11y) và kiểm thử đa trình duyệt
- [G6](G6-e2e-luong-p0.md) — E2E các luồng P0 (Playwright)

## Tiêu chí chấp nhận

- [ ] Mỗi câu trả lời có căn cứ hiển thị ≥ 1 chip.
- [ ] Panel hiển thị đúng đoạn gốc/tệp/trang.
- [ ] Tài liệu đã xóa → thông báo rõ, không trống.
- [ ] Đóng bằng Esc trả focus.

## Kiểm thử

- Component test; e2e mở/đóng panel.

## Tham chiếu

- Prototype: [app.html](../../design/UI_UX_design/app.html)#SCR-05
- [User_Stories.html](../../requirements/User_Stories.html) US-302
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
