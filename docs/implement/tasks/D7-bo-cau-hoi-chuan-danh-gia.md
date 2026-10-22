# D7 — Bộ câu hỏi chuẩn và script đánh giá

| Thuộc tính | Giá trị |
|---|---|
| Workstream | D — RAG: truy xuất & trả lời |
| Sprint | S4 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | AI/QA |
| Story liên quan | US-202 |
| Trạng thái | Đã có bộ 52 câu tổng hợp + harness + script; chạy với nhà cung cấp GIẢ LẬP. CHƯA có bộ câu hỏi thật (OQ-009) nên chưa kết luận chất lượng thật |

## Mô tả

Đo chất lượng RAG một cách lặp lại được (OQ-009).

## Phạm vi

- Tập tài liệu thử đã được duyệt + bộ câu hỏi với đáp án và trang nguồn kỳ vọng (gồm cả câu hỏi ngoài phạm vi).
- Script chạy toàn pipeline và tính: độ chính xác câu trả lời (chấm tay hoặc LLM-judge), tỷ lệ trích dẫn đúng trang, tỷ lệ ‘không tìm thấy’ đúng/sai.
- Xuất báo cáo (CSV/Markdown) so sánh giữa các cấu hình.
- Chạy được trong CI/staging bằng một lệnh.

## Hướng dẫn kỹ thuật

- Ngưỡng đạt `[TBD: OQ-009]`; dùng ngưỡng đề xuất ≥ 90% trích dẫn hợp lệ trong lúc chờ.
- Dữ liệu thử không chứa thông tin nhạy cảm thật.
- Bao gồm tiếng Việt và PDF nhiều cột.

## Đầu ra / sản phẩm bàn giao

- `eval/` + báo cáo baseline.

## Phụ thuộc

**Cần hoàn thành trước:**
- [D5](D5-ghep-trich-dan.md) — Ghép trích dẫn và kiểm tra hậu xử lý

**Mở khóa:**
- [D8](D8-hieu-chinh-nguong-k.md) — Hiệu chỉnh ngưỡng, k và chunking

## Tiêu chí chấp nhận

- [ ] Có ≥ 50 cặp hỏi–đáp [Đề xuất] gồm cả câu ngoài phạm vi.
- [ ] Script chạy lặp lại cho kết quả ổn định.
- [ ] Báo cáo hiển thị các chỉ số nêu trên.

## Kiểm thử

- Chạy script trên staging, lưu kết quả cơ sở (baseline).

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 2.4, R-A-04
- OQ-009
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
