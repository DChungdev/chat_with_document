# B7 — API hội thoại và hỏi đáp qua SSE

| Thuộc tính | Giá trị |
|---|---|
| Workstream | B — Backend lõi |
| Sprint | S3 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE |
| Story liên quan | US-201, US-202, US-203 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Endpoint tạo hội thoại và hỏi đáp streaming có trích dẫn.

## Phạm vi

- `POST /api/v1/conversations`; `GET /conversations/{id}` (lịch sử).
- `POST /conversations/{id}/messages` {câu hỏi, `documentIds[]`} → SSE các sự kiện `token`, `citations`, `done`, `error`.
- Kiểm kill switch → JWT → quyền sở hữu **mọi** `documentId` và trạng thái `ready` → độ dài câu hỏi.
- Lưu tin nhắn người dùng (`sending`) **trước** khi gọi dịch vụ ngoài.
- Điều phối: embed câu hỏi → retrieval → (không tìm thấy | LLM stream) → ghép trích dẫn → lưu `messages` + `citations`.
- Ngắt kết nối → message `interrupted`, giữ phần đã nhận.

## Hướng dẫn kỹ thuật

- Header SSE: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, tắt buffering ở proxy.
- Mỗi sự kiện có `id`; `done` mang `messageId`, `grounded`.
- Đo thời gian tới token đầu đẩy vào metrics (A6).
- Hết thời gian chờ LLM → `error` + message `failed`, câu hỏi vẫn được lưu.
- Chưa có tài liệu `ready` → `409`/mã lỗi rõ ràng để UI hướng dẫn tải PDF.

## Đầu ra / sản phẩm bàn giao

- Router `conversations`, use case `application.chat`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [D4](D4-llm-port-prompt.md) — LLMPort, adapter Claude và prompt chỉ dùng nguồn
- [D5](D5-ghep-trich-dan.md) — Ghép trích dẫn và kiểm tra hậu xử lý
- [D3](D3-nhanh-khong-tim-thay.md) — Nhánh ‘không tìm thấy’ không qua LLM
- [B9](B9-kill-switch-hoi-dap.md) — Kill switch hỏi đáp

**Mở khóa:**
- [B8](B8-api-xem-nguon-dan.md) — API xem nguồn dẫn
- [D6](D6-dung-sinh-gian-doan.md) — Dừng sinh và xử lý gián đoạn
- [E6](E6-scr04-khung-chat-sse.md) — SCR-04 Khung chat và streaming SSE
- [G7](G7-test-hieu-nang.md) — Test hiệu năng (token đầu, xử lý PDF)

## Tiêu chí chấp nhận

- [ ] Hỏi hợp lệ → nhận chuỗi `token`, `citations`, `done`.
- [ ] Dùng `documentId` của user khác → 404.
- [ ] Không còn chunk đạt ngưỡng → `done` với `grounded=false`, không gọi LLM.
- [ ] Đứt kết nối giữa chừng → message `interrupted` trong DB.
- [ ] Câu hỏi được lưu kể cả khi LLM lỗi.

## Kiểm thử

- Integration test với `FakeLLM`; test đứt kết nối; test đo token đầu.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.4B, ADR-04, ADR-05
- sequence_diagram_chat.drawio
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
