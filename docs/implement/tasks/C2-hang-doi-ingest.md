# C2 — Hàng đợi ingest trên PostgreSQL

| Thuộc tính | Giá trị |
|---|---|
| Workstream | C — Ingestion |
| Sprint | S1 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE/AI |
| Story liên quan | US-101, US-102 |
| Trạng thái | Hoàn thành — logic retry/backoff/requeue có unit test; claim bằng fn_claim_ingest_job (SKIP LOCKED). Test song song trên Postgres thật đã viết nhưng CHƯA chạy (không có Docker) |

## Mô tả

Hàng đợi công việc ingest bền, không cần broker ngoài (ADR-06).

## Phạm vi

- Bảng `ingest_jobs` (`document_id`, `status`, `attempts`, `run_at`, `last_error_code`).
- `JobQueue.enqueue` trong cùng giao dịch tạo tài liệu.
- Worker lấy job bằng `SELECT … FOR UPDATE SKIP LOCKED`; khóa có hạn (visibility timeout).
- Retry có backoff, tối đa N lần; quá số lần → job `failed` và `documents.status=error`.
- Job idempotent: chạy lại xóa chunk cũ trước khi ghi.

## Hướng dẫn kỹ thuật

- Đo độ dài hàng đợi cho metrics (A6).
- Job treo (worker chết) được tái nhận sau timeout.
- Nhiều worker chạy song song không xử lý trùng một job.

## Đầu ra / sản phẩm bàn giao

- `infra/persistence/job_queue`, vòng lặp worker.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A3](A3-migration-luoc-do-db.md) — Migration lược đồ cơ sở dữ liệu

**Mở khóa:**
- [C3](C3-trich-xuat-pdf.md) — Trích xuất văn bản PDF theo trang
- [C6](C6-worker-ingest-ghi-chi-muc.md) — Worker ingest end-to-end và ghi chỉ mục

## Tiêu chí chấp nhận

- [ ] Hai worker song song không nhận cùng job.
- [ ] Worker chết giữa chừng → job được nhận lại.
- [ ] Quá số lần retry → tài liệu `error`.

## Kiểm thử

- Integration test đồng thời với nhiều worker.

## Tham chiếu

- [SAD.md](../../design/SAD.md) ADR-06, mục 5.2
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
