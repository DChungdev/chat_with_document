COMPOSE = docker compose -f deploy/docker-compose.yml
PY      = .venv/bin/python
# Trên Windows (Git Bash): PY = .venv/Scripts/python
ifeq ($(OS),Windows_NT)
PY = .venv/Scripts/python
endif

.PHONY: help dev down logs test test-integration lint fmt migrate seed reset-db install

help: ## Liệt kê lệnh
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##/\t/'

install: ## Cài môi trường dev cục bộ (python + web)
	python -m venv .venv && $(PY) -m pip install -e ".[dev]"
	cd apps/web && pnpm install

dev: ## Dựng toàn bộ môi trường dev (web, api, worker, postgres+pgvector, minio)
	$(COMPOSE) up --build

down: ## Dừng môi trường (giữ dữ liệu)
	$(COMPOSE) down

logs: ## Xem log
	$(COMPOSE) logs -f --tail=100

test: ## Unit test (python + web)
	$(PY) -m pytest
	cd apps/web && pnpm test

test-integration: ## Test tích hợp với Postgres thật (cần Docker)
	$(PY) -m pytest -m integration db/tests

lint: ## Lint + type-check + quy tắc kiến trúc
	$(PY) -m ruff check .
	$(PY) -m black --check .
	$(PY) -m mypy packages/core/docchat_core infra/docchat_infra apps/api/docchat_api apps/worker/docchat_worker
	$(PY) -c "from importlinter.cli import lint_imports_command as m; m()"
	cd apps/web && pnpm lint && pnpm typecheck

fmt: ## Tự định dạng
	$(PY) -m ruff check . --fix
	$(PY) -m black .
	cd apps/web && pnpm format

migrate: ## Chạy migration trong môi trường compose
	$(COMPOSE) run --rm migrate

seed: ## Nạp người dùng giả cho dev (KHÔNG dùng ở production)
	$(COMPOSE) exec -T postgres psql -U postgres -d docchat -v ON_ERROR_STOP=1 < db/seed/dev_users.sql

reset-db: ## Xóa sạch dữ liệu Postgres/MinIO và dựng lại
	$(COMPOSE) down -v
	$(COMPOSE) up -d --build
