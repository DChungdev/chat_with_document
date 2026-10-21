# D5 — Ghép trích dẫn và kiểm tra hậu xử lý

| Thuộc tính | Giá trị |
|---|---|
| Workstream | D — RAG: truy xuất & trả lời |
| Sprint | S3 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | AI/BE |
| Story liên quan | US-301, US-203 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Chuyển nhãn `[Sx]` thành trích dẫn có cấu trúc và loại mọi nhãn không có thật.

## Phạm vi

- Phân tích nhãn `[Sx]` trong câu trả lời đã stream xong.
- Ánh xạ → `Citation` (document_id, tên tệp, trang, snippet) từ chunk đã truy xuất.
- Loại nhãn không thuộc tập chunk; loại bỏ nhãn khỏi văn bản hoặc đánh dấu không hợp lệ.
- Khử trùng lặp; sắp theo thứ tự xuất hiện.
- Nếu có khẳng định nhưng không có nhãn hợp lệ → hạ cờ `grounded` hoặc cảnh báo theo quy tắc [Đề xuất].
- Lưu `messages` + `citations`; phát sự kiện `citations`.

## Hướng dẫn kỹ thuật

- Trích dẫn sinh từ **ID chunk truy xuất**, không từ chuỗi do LLM tự ghi (ADR-03).
- Số trang lấy từ `page_start`/`page_end`; hiển thị ‘tr.N’ hoặc ‘tr.N–M’.
- Snippet cắt theo độ dài tối đa.

## Đầu ra / sản phẩm bàn giao

- `packages/core/answering/citations`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [D4](D4-llm-port-prompt.md) — LLMPort, adapter Claude và prompt chỉ dùng nguồn

**Mở khóa:**
- [B7](B7-api-hoi-dap-sse.md) — API hội thoại và hỏi đáp qua SSE
- [D7](D7-bo-cau-hoi-chuan-danh-gia.md) — Bộ câu hỏi chuẩn và script đánh giá
- [G1](G1-unit-test-nghiep-vu.md) — Unit test domain, retrieval và answering
- [G5](G5-test-trich-dan-xoa.md) — Test độ tin cậy trích dẫn và xóa dữ liệu

## Tiêu chí chấp nhận

- [ ] Nhãn hợp lệ → trích dẫn đúng tệp/trang.
- [ ] Nhãn bịa (`[S99]`) bị loại, không tạo trích dẫn tới trang không tồn tại.
- [ ] Câu trả lời đa nguồn có ≥ 2 trích dẫn từ các tệp khác nhau.

## Kiểm thử

- Unit test nhiều trường hợp nhãn (trùng, thiếu, bịa, dạng lệch).

## Tham chiếu

- [SAD.md](../../design/SAD.md) ADR-03, mục 3.4B(6)
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
