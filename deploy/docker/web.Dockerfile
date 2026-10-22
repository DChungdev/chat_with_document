# syntax=docker/dockerfile:1
# Build từ gốc repo: docker build -f deploy/docker/web.Dockerfile --target prod .

# ---------- dev: dùng bởi docker compose (mã nguồn bind-mount) ----------
FROM node:20-alpine AS dev
RUN corepack enable
WORKDIR /app/apps/web
CMD ["sh", "-c", "pnpm install --frozen-lockfile && pnpm dev"]

# ---------- build ----------
FROM node:20-alpine AS build
RUN corepack enable
WORKDIR /app/apps/web
COPY apps/web/package.json apps/web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY apps/web ./
RUN pnpm build

# ---------- prod: nginx phục vụ SPA, không root ----------
FROM nginxinc/nginx-unprivileged:1.27-alpine AS prod
COPY deploy/docker/web.nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/docker/web.security.conf /etc/nginx/web.security.conf
COPY --from=build /app/apps/web/dist /usr/share/nginx/html
EXPOSE 8080
