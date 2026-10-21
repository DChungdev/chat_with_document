# Chat với tài liệu

Tải PDF, hỏi bằng ngôn ngữ tự nhiên, nhận câu trả lời AI có nguồn dẫn kiểm chứng được.
Thiết kế: [SAD](docs/design/SAD.md) · Kế hoạch: [Implement_Plan](docs/implement/Implement_Plan.md) · Task: [docs/implement/tasks](docs/implement/tasks/README.md)

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `packages/core` | domain, ports, retrieval, answering, cấu hình — **không** import hạ tầng (kiểm bằng import-linter) |
| `infra` | adapter: persistence, storage, llm, embedding, auth, observability |
| `apps/api` | FastAPI (routing, xác thực, SSE) |
| `apps/worker` | ingestion worker |
| `apps/web` | React + TypeScript + Vite |
| `db` | migration (Alembic chạy các tệp SQL), khởi tạo vai trò, dữ liệu dev, test CSDL |
| `deploy` | Docker, Compose, Kubernetes, runbook — xem [deploy/README.md](deploy/README.md) |

## Bắt đầu

Cần: Python 3.12+, Node 20+ và pnpm, Docker (cho `make dev` và test tích hợp).

```bash
make install            # .venv + pnpm install
cp .env.example .env
make dev                # web :5173, api :8000, postgres+pgvector, minio
make test               # unit test python + web
make test-integration   # Postgres thật (testcontainers)
make lint               # ruff, black, mypy, import-linter, eslint, prettier
```

Không có `make` (Windows): chạy trực tiếp các lệnh trong [Makefile](Makefile), ví dụ `.venv\Scripts\python -m pytest`.

## Quy ước

- Nhánh `main` được bảo vệ; mọi thay đổi qua PR, CI phải xanh (`.github/workflows/ci.yml`).
- Giới hạn nghiệp vụ (kích thước PDF, top-k, ...) đọc từ bảng `app_config`, không hard-code.
- **Không** ghi nội dung tài liệu/câu hỏi/tên tệp vào log hay telemetry — dùng `log_safe` và logger allow-list ở `infra/docchat_infra/observability`.
- Mọi truy vấn dữ liệu người dùng đi qua `user_transaction` (đặt `app.user_id` cho Row-Level Security).
- Migration production là forward-only; `*.down.sql` chỉ để dev/test. Chi tiết: [db/README.md](db/README.md).
