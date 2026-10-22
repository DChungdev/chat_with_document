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
| `eval` | bộ câu hỏi chuẩn tổng hợp + harness + công cụ hiệu chỉnh retrieval (`python eval/run_eval.py`, `python eval/tune.py`) — xem [báo cáo](docs/implement/reports/) |
| `db` | migration (Alembic chạy các tệp SQL), khởi tạo vai trò, dữ liệu dev, test CSDL |
| `deploy` | Docker, Compose, Kubernetes, runbook — xem [deploy/README.md](deploy/README.md) |

## Chạy local — KHÔNG cần Docker, PostgreSQL hay khóa API

Cần: Python 3.12+, Node 20+ và pnpm.

```bash
make install        # .venv + pnpm install (một lần)
make local          # build giao diện rồi chạy API + worker + giao diện tại http://127.0.0.1:8000
```

Không có `make` (Windows PowerShell/Git Bash):

```powershell
python -m venv .venv ; .venv\Scripts\python -m pip install -e ".[dev]"
cd apps\web ; pnpm install ; pnpm build ; cd ..\..
$env:ENVIRONMENT = "dev" ; .venv\Scripts\python -m docchat_api.devserver
```

Mở http://127.0.0.1:8000 → nhập tên bất kỳ (dev login) → xác nhận thông báo dữ liệu → tải PDF → hỏi.
Tài liệu API tương tác: http://127.0.0.1:8000/docs · Báo cáo đo lường (đăng nhập vai trò `evaluator`): `#/report`.

Chế độ này chạy **một tiến trình**: API + worker ingest + kho dữ liệu/tệp/vector **trong bộ nhớ** (tắt là mất dữ liệu),
embedding và LLM **giả lập** (câu trả lời là trích đoạn từ tài liệu, không phải Claude). Phù hợp để thử luồng và phát triển giao diện.
Dùng Claude/embedding thật: đặt `LLM_PROVIDER=anthropic`, `LLM_API_KEY=...` (và `EMBEDDING_PROVIDER=http` + biến liên quan trong `.env.example`)
— khi đó nội dung tài liệu **rời khỏi máy**, chỉ dùng dữ liệu thử đã được phép. Phát triển giao diện có hot reload:
chạy devserver với `--no-static` và `cd apps/web && pnpm dev` (cổng 5173, proxy `/api` sang :8000).

Kiểm thử toàn bộ không cần Docker: `make test` (pytest + vitest), `make e2e` (Playwright trên chế độ local).

## Chạy đầy đủ với Docker (PostgreSQL + pgvector + MinIO)

Cần thêm Docker (cho `make dev` và test tích hợp).

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
