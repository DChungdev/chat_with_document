# A1 — Khởi tạo monorepo, lint/format và CI

| Thuộc tính | Giá trị |
|---|---|
| Workstream | A — Nền tảng & hạ tầng |
| Sprint | S0 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | DevOps/BE |
| Story liên quan | — (nền tảng) |
| Trạng thái | Đã triển khai — kiểm cục bộ: ruff, black, mypy, import-linter, pytest, web lint/test/build đều qua; CI trên GitHub chưa chạy |

## Mô tả

Dựng khung repo theo cấu trúc SAD/Implement Plan mục 3 và pipeline CI cơ bản để mọi task sau có nơi đặt mã và được kiểm tự động.

## Phạm vi

- Tạo cấu trúc `apps/web`, `apps/api`, `apps/worker`, `packages/core`, `infra`, `db/migrations`, `deploy`.
- Cấu hình Python 3.12 (uv hoặc poetry) cho api/worker/core; Node LTS + pnpm cho web.
- Lint/format: ruff + black + mypy (Python); eslint + prettier + tsc (web).
- Pre-commit hook chạy lint/format.
- CI (GitHub Actions): lint, type-check, unit test, build cho từng thành phần; cache dependency.
- README gốc hướng dẫn cài đặt, chạy test, quy ước nhánh/PR.

## Hướng dẫn kỹ thuật

- Quy tắc phụ thuộc: `packages/core` (domain, retrieval, answering, ports) **không import** `infra`/`apps`; kiểm bằng import-linter hoặc test kiến trúc.
- Mỗi package có test mẫu để CI không rỗng.
- PR bắt buộc review; nhánh `main` được bảo vệ, CI bắt buộc xanh.
- Không commit secret; thêm `.env.example`, `.gitignore`.

## Đầu ra / sản phẩm bàn giao

- Repo có khung thư mục + CI + README.

## Phụ thuộc

**Cần hoàn thành trước:**
- Không có

**Mở khóa:**
- [A2](A2-docker-compose-dev.md) — Môi trường dev bằng Docker Compose
- [A6](A6-logging-metrics-tracing.md) — Logging có allow-list, metrics và tracing
- [B1](B1-domain-model.md) — Domain model và quy tắc trạng thái
- [E1](E1-khoi-tao-spa.md) — Khởi tạo SPA, routing, API client và design tokens

## Tiêu chí chấp nhận

- [ ] Clone mới + chạy lệnh cài đặt trong README là chạy được lint và test.
- [ ] CI xanh trên `main` với test mẫu cho mọi package.
- [ ] Import-linter fail khi `core` import `infra`.
- [ ] Pre-commit chặn commit sai định dạng.

## Kiểm thử

- Chạy CI trên PR thử, thử cố ý vi phạm lint và quy tắc import để xác nhận bị chặn.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.1 (Module View), ADR-01
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
