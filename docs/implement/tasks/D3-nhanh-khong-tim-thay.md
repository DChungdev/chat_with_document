# D3 — Nhánh ‘không tìm thấy’ không qua LLM

| Thuộc tính | Giá trị |
|---|---|
| Workstream | D — RAG: truy xuất & trả lời |
| Sprint | S3 |
| Cỡ ước lượng | S (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | AI/BE |
| Story liên quan | US-202 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Khi không đủ căn cứ, trả lời ngay mà không gọi LLM để chặn bịa đặt và tiết kiệm chi phí (ADR-04).

## Phạm vi

- Nếu `RetrievalResult` rỗng → trả thông điệp ‘không tìm thấy trong tài liệu đã tải’, `grounded=false`, không có trích dẫn.
- Thông điệp cấu hình/đa ngôn ngữ được.
- Ghi metric tỷ lệ `grounded=false`.

## Hướng dẫn kỹ thuật

- Phát qua cùng kênh SSE như câu trả lời thường để UI thống nhất.
- Không đưa kiến thức ngoài vào câu trả lời.

## Đầu ra / sản phẩm bàn giao

- `answering/not_found`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [D2](D2-retrieval-nguong-ngu-canh.md) — Retrieval: ngưỡng liên quan và dựng ngữ cảnh

**Mở khóa:**
- [B7](B7-api-hoi-dap-sse.md) — API hội thoại và hỏi đáp qua SSE

## Tiêu chí chấp nhận

- [ ] Câu hỏi ngoài phạm vi (‘Thời tiết hôm nay?’) → ‘không tìm thấy’, LLM không bị gọi.
- [ ] `grounded=false`.
- [ ] Metric tăng.

## Kiểm thử

- Unit test với LLM giả đếm số lần gọi = 0.

## Tham chiếu

- [SAD.md](../../design/SAD.md) ADR-04
- US-202
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
