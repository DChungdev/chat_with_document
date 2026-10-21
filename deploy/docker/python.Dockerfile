# syntax=docker/dockerfile:1
# Một Dockerfile cho api, worker và migrate. Build từ gốc repo:
#   docker build -f deploy/docker/python.Dockerfile --target api .

ARG PYTHON_VERSION=3.12

# ---------- base ----------
FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

# ---------- dev: cài editable, mã nguồn được bind-mount bởi docker compose ----------
FROM base AS dev
COPY pyproject.toml ./
COPY packages ./packages
COPY infra ./infra
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker
RUN pip install -e ".[dev]"
COPY alembic.ini ./
COPY db ./db

# ---------- build: wheel không editable cho production ----------
FROM base AS build
COPY pyproject.toml ./
COPY packages ./packages
COPY infra ./infra
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker
RUN pip wheel --wheel-dir /wheels .

# ---------- runtime chung (không root, không compiler) ----------
FROM base AS runtime
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app
COPY --from=build /wheels /wheels
RUN pip install /wheels/*.whl && rm -rf /wheels
USER 10001

FROM runtime AS api
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status==200 else 1)"
CMD ["uvicorn", "docchat_api.main:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--proxy-headers"]

FROM runtime AS worker
EXPOSE 9101
CMD ["python", "-m", "docchat_worker.main"]

# Job migration một lần: cần alembic.ini + db/
FROM runtime AS migrate
COPY --chown=10001:10001 alembic.ini ./
COPY --chown=10001:10001 db ./db
CMD ["alembic", "upgrade", "head"]
