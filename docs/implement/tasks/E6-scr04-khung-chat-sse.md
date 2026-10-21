# E6 — SCR-04 Khung chat và streaming SSE

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S3 |
| Cỡ ước lượng | XL (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE |
| Story liên quan | US-201, US-202, US-203 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Giao diện hỏi đáp: gửi câu hỏi, nhận câu trả lời stream, nhãn AI cố định.

## Phạm vi

- Ô nhập: Enter gửi, Shift+Enter xuống dòng; giới hạn độ dài (cấu hình, UI giả định 2000 ký tự).
- SSE client bằng `fetch` stream (vì `POST`); phân tích sự kiện `token`, `citations`, `done`, `error`.
- Chỉ báo ‘đang tạo câu trả lời’; render dần Markdown an toàn (chống XSS).
- Nhãn ‘Câu trả lời do AI tạo, hãy kiểm tra nguồn trước khi sử dụng’ cố định trên **100%** câu trả lời, không đóng được.
- Chặn gửi khi chưa có tài liệu sẵn sàng, kèm hướng dẫn tải PDF.
- Tự cuộn tới tin nhắn mới nhưng không đè khi người dùng đang cuộn lên; nút ‘Cuộn xuống’.
- Sự kiện `question_sent`, `answer_completed`.

## Hướng dẫn kỹ thuật

- Hủy `AbortController` khi rời trang để đóng stream.
- Giữ bản nháp câu hỏi nếu mất phiên (SCR-07).
- Dừng/Tạo lại/Đánh giá là P1 (US-205, US-502) — để chỗ gắn.
- Thử câu hỏi ngoài phạm vi để thấy thông điệp ‘không tìm thấy’.

## Đầu ra / sản phẩm bàn giao

- Thành phần Chat, hook `useAskStream`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B7](B7-api-hoi-dap-sse.md) — API hội thoại và hỏi đáp qua SSE
- [E1](E1-khoi-tao-spa.md) — Khởi tạo SPA, routing, API client và design tokens

**Mở khóa:**
- [E7](E7-scr05-chip-trich-dan-panel-nguon.md) — Chip trích dẫn và panel nguồn
- [E8](E8-scr08-trang-thai-loi-kill-switch.md) — Trạng thái lỗi và banner kill switch
- [E10](E10-telemetry-client.md) — TelemetryClient và sự kiện
- [E12](E12-a11y-da-trinh-duyet.md) — Tiếp cận (a11y) và kiểm thử đa trình duyệt
- [G6](G6-e2e-luong-p0.md) — E2E các luồng P0 (Playwright)

## Tiêu chí chấp nhận

- [ ] Gửi câu hỏi hiển thị ngay trong khung chat và bắt đầu nhận token.
- [ ] Nhãn AI hiện trên mọi câu trả lời.
- [ ] Chưa có tài liệu sẵn sàng → không gửi được, có lời hướng dẫn.
- [ ] Nội dung độc hại trong câu trả lời không thực thi (XSS).

## Kiểm thử

- Unit test parser SSE; component test luồng stream với server giả; e2e hỏi–đáp.

## Tham chiếu

- Prototype: [app.html](../../design/UI_UX_design/app.html)#SCR-04
- [User_Stories.html](../../requirements/User_Stories.html) US-201, US-202
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
