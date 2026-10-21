# C4 — Chunking giữ số trang

| Thuộc tính | Giá trị |
|---|---|
| Workstream | C — Ingestion |
| Sprint | S1 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE/AI |
| Story liên quan | US-301 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Cắt văn bản thành chunk ~800 token, chồng 100, giữ `page_start`/`page_end` để trích dẫn chính xác.

## Phạm vi

- Bộ đếm token (tokenizer cấu hình được; xấp xỉ theo ký tự nếu chưa chốt).
- Chunk có thể vắt qua trang: ghi cả `page_start` và `page_end`.
- Tham số `chunk_size`, `overlap` đọc từ cấu hình.
- Mỗi chunk có `ordinal` ổn định trong tài liệu.

## Hướng dẫn kỹ thuật

- Cắt ưu tiên ranh giới đoạn/câu.
- Chunk rỗng hoặc quá ngắn bị bỏ.
- Hàm thuần, dễ test; không phụ thuộc hạ tầng.

## Đầu ra / sản phẩm bàn giao

- `ingestion/chunker`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [C3](C3-trich-xuat-pdf.md) — Trích xuất văn bản PDF theo trang

**Mở khóa:**
- [C6](C6-worker-ingest-ghi-chi-muc.md) — Worker ingest end-to-end và ghi chỉ mục

## Tiêu chí chấp nhận

- [ ] Mọi chunk có `page_start ≤ page_end` nằm trong số trang thực.
- [ ] Kích thước chunk ≤ giới hạn.
- [ ] Chồng lặp đúng giá trị cấu hình.
- [ ] Cùng đầu vào → cùng đầu ra.

## Kiểm thử

- Unit test với văn bản nhiều trang và chunk vắt trang.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.4A, mục 6
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
