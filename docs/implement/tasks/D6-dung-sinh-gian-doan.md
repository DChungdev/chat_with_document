# D6 — Dừng sinh và xử lý gián đoạn

| Thuộc tính | Giá trị |
|---|---|
| Workstream | D — RAG: truy xuất & trả lời |
| Sprint | S6 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P1 |
| Người thực hiện đề xuất | AI/BE |
| Story liên quan | US-205 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Cho phép dừng câu trả lời đang stream và phục hồi khi gián đoạn.

## Phạm vi

- `POST /conversations/{id}/messages/{mid}/stop` → huỷ stream LLM.
- Message trạng thái `stopped` giữ phần đã nhận; `interrupted` khi mất kết nối.
- Hỗ trợ ‘Tạo lại’: gửi lại câu hỏi gốc, không mất câu hỏi.
- Telemetry `answer_stopped`.

## Hướng dẫn kỹ thuật

- Nền tảng trạng thái `interrupted` đã có từ B7; task này thêm `stop` và tạo lại.
- Giải phóng tài nguyên (đóng stream tới LLM) ngay khi dừng.

## Đầu ra / sản phẩm bàn giao

- Use case `stop_message`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B7](B7-api-hoi-dap-sse.md) — API hội thoại và hỏi đáp qua SSE

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Dừng giữa chừng → phần đã nhận được giữ, trạng thái `stopped`.
- [ ] Mất kết nối → `interrupted`.
- [ ] Tạo lại sinh message mới cho cùng câu hỏi.

## Kiểm thử

- Integration test dừng/đứt kết nối với FakeLLM chậm.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.4B(7), ADR-05
- US-205
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
