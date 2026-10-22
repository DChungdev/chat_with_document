# C1 — FileStoragePort và adapter S3/MinIO

| Thuộc tính | Giá trị |
|---|---|
| Workstream | C — Ingestion |
| Sprint | S1 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE/AI |
| Story liên quan | US-101, US-103 |
| Trạng thái | Hoàn thành — có test với S3 giả lập (moto); chưa thử với MinIO/S3 thật (compose đã cấu hình sẵn) |

## Mô tả

Lưu và xóa PDF gốc trong object storage sau một cổng trừu tượng.

## Phạm vi

- Port `FileStoragePort`: `put`, `get_stream`, `delete`, `exists`.
- Adapter S3-compatible (boto3/aioboto3) cho MinIO (dev) và S3 (prod).
- Khóa đối tượng `user_id/document_id.pdf`; bật mã hóa SSE.
- Timeout, retry có backoff; adapter in-memory cho test.

## Hướng dẫn kỹ thuật

- Không dùng tên tệp gốc làm khóa đối tượng.
- Truyền dạng stream, không nạp cả tệp vào RAM.
- Bucket riêng tư, không public.

## Đầu ra / sản phẩm bàn giao

- `infra/storage`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A2](A2-docker-compose-dev.md) — Môi trường dev bằng Docker Compose

**Mở khóa:**
- [B4](B4-api-tai-lieu.md) — API tài liệu: tải lên, liệt kê, chi tiết
- [B11](B11-xoa-tai-lieu.md) — Xóa tài liệu
- [C6](C6-worker-ingest-ghi-chi-muc.md) — Worker ingest end-to-end và ghi chỉ mục

## Tiêu chí chấp nhận

- [ ] put → get trả đúng nội dung.
- [ ] delete xong `exists` = false.
- [ ] Khóa đối tượng không chứa tên tệp người dùng.

## Kiểm thử

- Integration test với MinIO; unit test adapter in-memory.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.1, 3.2
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
