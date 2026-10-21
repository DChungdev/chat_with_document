# A3 — Migration lược đồ cơ sở dữ liệu

| Thuộc tính | Giá trị |
|---|---|
| Workstream | A — Nền tảng & hạ tầng |
| Sprint | S1 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | DevOps/BE |
| Story liên quan | US-101, US-103, US-201, US-301, US-401, US-402, US-501 |
| Trạng thái | Đã triển khai — SQL qua kiểm cú pháp (pglast); chưa chạy trên Postgres thật (test tích hợp bị bỏ qua vì không có Docker) |

## Mô tả

Tạo toàn bộ lược đồ PostgreSQL cho MVP bằng migration có phiên bản.

## Phạm vi

- Công cụ migration (Alembic) trong `db/migrations`.
- Bảng: `users`, `data_notice_acceptances`, `documents`, `chunks`, `ingest_jobs`, `conversations`, `messages`, `citations`, `feedback`, `telemetry_events`, `audit_log` (chỉ thêm), `app_config`.
- Khóa ngoại với `ON DELETE CASCADE` từ `documents` → `chunks`; `citations` giữ cờ `valid`.
- Chỉ mục: `documents(user_id, status)`, `chunks(document_id)`, `messages(conversation_id, created_at)`, `ingest_jobs(status, run_at)`.
- Seed `app_config` mặc định: kích thước tệp tối đa, số tệp, độ dài câu hỏi (2000), top-k (8), ngưỡng, số tài liệu tối đa mỗi câu hỏi (10).

## Hướng dẫn kỹ thuật

- Tên cột, kiểu và ràng buộc phải khớp Database_Design_SQL / Database_Design_VectorDB (nếu đã có trong `docs/design`); nếu chưa có, tạo theo SAD mục 3.3 và cập nhật tài liệu thiết kế.
- `documents.status` ∈ {`processing`, `ready`, `error`}; `error_code` nullable.
- `chunks`: `page_start`, `page_end`, `content`, `embedding vector(N)` — **N lấy từ cấu hình** (phụ thuộc mô hình embedding, OQ-008), tạo cột bằng migration tham số hóa.
- `audit_log`: chặn UPDATE/DELETE bằng trigger hoặc quyền; chỉ ghi `user_id`, `action`, `document_id`, thời điểm, không ghi nội dung/tên tệp nhạy cảm.
- Migration phải chạy lùi (downgrade) được.

## Đầu ra / sản phẩm bàn giao

- Thư mục `db/migrations` + tài liệu lược đồ cập nhật.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A2](A2-docker-compose-dev.md) — Môi trường dev bằng Docker Compose

**Mở khóa:**
- [A4](A4-pgvector-hnsw-rls.md) — pgvector, chỉ mục HNSW và Row-Level Security
- [A5](A5-cau-hinh-feature-flag.md) — Cấu hình, secret và feature flag
- [B2](B2-ports-repository.md) — Ports và repository PostgreSQL
- [B10](B10-api-telemetry.md) — API telemetry
- [C2](C2-hang-doi-ingest.md) — Hàng đợi ingest trên PostgreSQL

## Tiêu chí chấp nhận

- [ ] `alembic upgrade head` trên DB trống thành công; `downgrade base` thành công.
- [ ] Xóa một `documents` làm mất mọi `chunks` liên quan.
- [ ] Không thể UPDATE/DELETE `audit_log` bằng role ứng dụng.
- [ ] Seed `app_config` có đủ khóa liệt kê ở phạm vi.

## Kiểm thử

- Test migration up/down trong CI (testcontainers Postgres+pgvector).
- Test cascade và ràng buộc audit.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.3, mục 6
- Database_Design_SQL.md, Database_Design_VectorDB.md (nếu có trong `docs/design`)
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
