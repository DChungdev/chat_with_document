# A2 — Môi trường dev bằng Docker Compose

| Thuộc tính | Giá trị |
|---|---|
| Workstream | A — Nền tảng & hạ tầng |
| Sprint | S0 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | DevOps/BE |
| Story liên quan | — (nền tảng) |
| Trạng thái | Đã viết, CHƯA chạy thử — máy phát triển không có Docker |

## Mô tả

Một lệnh `docker compose up` dựng toàn bộ môi trường phát triển cục bộ.

## Phạm vi

- Service: `web`, `api`, `worker`, `postgres` (PostgreSQL 16 + pgvector), `minio` (S3-compatible), tùy chọn `mailhog` không cần.
- Volume lưu dữ liệu Postgres/MinIO; healthcheck cho từng service.
- Biến môi trường qua `.env`; bucket MinIO tự tạo khi khởi động.
- Hot reload cho api và web.
- Script `make dev` / `make test` / `make reset-db`.

## Hướng dẫn kỹ thuật

- Image Postgres: `pgvector/pgvector:pg16`; bật extension `vector` trong migration (A3), không trong compose.
- API và worker dùng chung image build từ cùng Dockerfile, khác lệnh khởi động.
- Mạng nội bộ compose; chỉ publish cổng web và api ra host.
- LLM/Embedding dùng adapter giả lập mặc định trong dev (cấu hình `LLM_PROVIDER=fake`).

## Đầu ra / sản phẩm bàn giao

- `deploy/docker-compose.yml`, `Makefile`, `.env.example`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A1](A1-khoi-tao-monorepo-ci.md) — Khởi tạo monorepo, lint/format và CI

**Mở khóa:**
- [A3](A3-migration-luoc-do-db.md) — Migration lược đồ cơ sở dữ liệu
- [A7](A7-staging-pipeline-trien-khai.md) — Staging và pipeline triển khai
- [C1](C1-file-storage-s3.md) — FileStoragePort và adapter S3/MinIO

## Tiêu chí chấp nhận

- [ ] `docker compose up` thành công trong ≤ 5 phút trên máy mới; mọi healthcheck xanh.
- [ ] `api` kết nối được Postgres và MinIO.
- [ ] Sửa mã api/web tự reload.
- [ ] `make reset-db` đưa DB về trạng thái sạch.

## Kiểm thử

- Chạy trên máy sạch (hoặc CI job) và kiểm `GET /health` của api trả 200.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.5 (Deployment View — Dev)
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
