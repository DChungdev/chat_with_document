# C6 — Worker ingest end-to-end và ghi chỉ mục

| Thuộc tính | Giá trị |
|---|---|
| Workstream | C — Ingestion |
| Sprint | S2 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE/AI |
| Story liên quan | US-101, US-102 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Ghép các bước thành pipeline: lấy job → tải PDF → trích xuất → chunk → embed → ghi chunk → `ready`.

## Phạm vi

- Use case `IngestDocument(document_id)` chạy trong worker.
- Embed theo lô; ghi `chunks` kèm embedding và vị trí trang trong một giao dịch.
- Thành công → `documents.status=ready`; lỗi → `status=error` + `error_code`.
- Xử lý từng tài liệu độc lập; tệp lỗi không ảnh hưởng tệp khác.
- Phát metrics thời gian xử lý, lỗi theo `stage` (extract/chunk/embed/write).

## Hướng dẫn kỹ thuật

- Đặt `app.user_id` theo chủ sở hữu tài liệu trước khi ghi (RLS).
- Chạy lại job xóa chunk cũ trước (idempotent).
- Tài liệu bị xóa giữa chừng → job dừng gọn, không ghi chunk mồ côi.

## Đầu ra / sản phẩm bàn giao

- `apps/worker`, use case ingest.

## Phụ thuộc

**Cần hoàn thành trước:**
- [C1](C1-file-storage-s3.md) — FileStoragePort và adapter S3/MinIO
- [C2](C2-hang-doi-ingest.md) — Hàng đợi ingest trên PostgreSQL
- [C3](C3-trich-xuat-pdf.md) — Trích xuất văn bản PDF theo trang
- [C4](C4-chunking-so-trang.md) — Chunking giữ số trang
- [C5](C5-embedding-port-adapter.md) — EmbeddingPort và adapter

**Mở khóa:**
- [C7](C7-do-hieu-nang-ingest.md) — Đo hiệu năng xử lý PDF (≤ 60s)
- [D1](D1-vector-store-pgvector.md) — VectorStorePort và adapter pgvector
- [G2](G2-test-tich-hop.md) — Test tích hợp với Postgres và MinIO

## Tiêu chí chấp nhận

- [ ] Tải PDF mẫu → sau xử lý `ready`, có chunk với số trang đúng.
- [ ] PDF quét → `error` với `PDF_NO_TEXT`.
- [ ] Chạy lại job không tạo chunk trùng.
- [ ] Xóa tài liệu khi đang xử lý không để lại chunk.

## Kiểm thử

- Integration test end-to-end với MinIO + Postgres + FakeEmbedding.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.4A
- sequence_diagram_upload.drawio
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
