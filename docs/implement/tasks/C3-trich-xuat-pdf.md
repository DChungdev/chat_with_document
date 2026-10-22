# C3 — Trích xuất văn bản PDF theo trang

| Thuộc tính | Giá trị |
|---|---|
| Workstream | C — Ingestion |
| Sprint | S1 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE/AI |
| Story liên quan | US-101 |
| Trạng thái | Hoàn thành — có test trên PDF tổng hợp (tiếng Việt, quét, mật khẩu, hỏng, quá trang); chưa thử PDF thật nhiều cột/bảng |

## Mô tả

Trích văn bản từng trang và phân loại lỗi PDF.

## Phạm vi

- Dùng `pypdf`/`pdfminer.six`; trả danh sách (số trang, văn bản).
- Chuẩn hóa khoảng trắng, loại header/footer lặp đơn giản (tùy chọn).
- Phân loại lỗi: PDF hỏng (`PDF_CORRUPT`), có mật khẩu (`PDF_ENCRYPTED`), không có văn bản/PDF quét (`PDF_NO_TEXT`), quá số trang.
- Không OCR trong MVP (ADR-09, OQ-008).

## Hướng dẫn kỹ thuật

- Chạy trong thread/process pool để không chặn event loop.
- Giới hạn thời gian và bộ nhớ mỗi tệp.
- Tách adapter `PdfExtractor` sau interface để có thể thay/ thêm OCR sau.

## Đầu ra / sản phẩm bàn giao

- `ingestion/extractor`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [C2](C2-hang-doi-ingest.md) — Hàng đợi ingest trên PostgreSQL

**Mở khóa:**
- [C4](C4-chunking-so-trang.md) — Chunking giữ số trang
- [C6](C6-worker-ingest-ghi-chi-muc.md) — Worker ingest end-to-end và ghi chỉ mục

## Tiêu chí chấp nhận

- [ ] PDF văn bản thường → đủ trang, đúng thứ tự.
- [ ] PDF quét → `PDF_NO_TEXT`.
- [ ] PDF có mật khẩu → `PDF_ENCRYPTED`.
- [ ] PDF hỏng không làm worker crash.

## Kiểm thử

- Bộ PDF mẫu (tiếng Việt, tiếng Anh, nhiều cột, quét, mã hóa, hỏng) trong fixtures.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.4A, ADR-09
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
