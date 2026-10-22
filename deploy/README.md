# Triển khai và vận hành

Phạm vi: A2 (môi trường dev) và A7 (staging, pipeline triển khai, runbook). Tham chiếu: [SAD.md](../docs/design/SAD.md) mục 3.5, 3.6, 5.2.

> **Trạng thái:** manifest và pipeline dưới đây **chưa được chạy thử trên cluster thật** (chưa có cluster, đám mây/vùng còn là `[TBD: OQ-012]`). Chúng đã qua kiểm tra cú pháp YAML nhưng cần diễn tập deploy/rollback/khôi phục trên staging trước khi coi là xong (tiêu chí chấp nhận của A7).

## 1. Dev cục bộ (Docker Compose)

```bash
make dev                 # = docker compose -f deploy/docker-compose.yml up --build
make seed                # người dùng giả (Lan/Minh/Ops) — chỉ dev
make test-integration    # test Postgres thật
```

| Dịch vụ | Cổng host | Ghi chú |
|---|---|---|
| web | 5173 | Vite dev server, proxy `/api` → api |
| api | 8000 | `/health`, `/ready`, `/metrics` |
| postgres | 127.0.0.1:5432 | PG16 + pgvector; `db/init/*.sql` chạy khi khởi tạo volume |
| minio | 127.0.0.1:9000/9001 | bucket `docchat-documents` tạo tự động |

Vai trò CSDL (tạo bởi `db/init/01-roles.sql`, mật khẩu dev `docchat_dev`): `migrator` (chủ sở hữu, chạy migration), `docchat_api` → `app_api`, `docchat_worker` → `app_worker`, `docchat_report` → `app_report`. `migrator` không phải superuser nên RLS áp dụng với nó.

## 2. Kiến trúc triển khai (Kubernetes + kustomize)

```
deploy/k8s/
├── base/            api, worker, web, ingress, networkpolicy, pdb, ConfigMap
├── migrate/         Job `alembic upgrade head`, chạy trước mỗi lần deploy
└── overlays/
    ├── staging/     namespace docchat-staging
    └── production/  namespace docchat-production
```

Không nằm trong manifest (managed service, `[TBD: OQ-012]`): PostgreSQL 16 + pgvector, object storage S3-compatible, IdP, LLM/Embedding.

### Điều kiện trước lần deploy đầu

1. **PostgreSQL**: khởi tạo bằng quy trình tương đương `db/init/01-roles.sql` nhưng **dùng mật khẩu thật từ secret manager** (không dùng `docchat_dev`). Cần quyền cài extension (superuser hoặc vai trò tương đương của nhà cung cấp) để `CREATE EXTENSION vector`.
2. **Secret `docchat-secrets`** trong namespace (tạo ngoài repo, ví dụ External Secrets/sealed-secrets):

   | Khóa | Dùng bởi |
   |---|---|
   | `DATABASE_URL` | api (vai trò `docchat_api`) |
   | `WORKER_DATABASE_URL` | worker (vai trò `docchat_worker`) |
   | `MIGRATOR_DATABASE_URL` | job migrate (vai trò `migrator`) |
   | `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_ENDPOINT_URL` (tùy chọn) | api, worker |
   | `JWT_SECRET`, `TELEMETRY_SALT` | api |
   | `LLM_API_KEY`, `EMBEDDING_API_KEY` (tùy chọn) | api, worker |

3. **TLS**: Secret `docchat-tls` (cert-manager) và ingress-nginx. Host thật thay trong `overlays/*/kustomization.yaml`.
4. **NetworkPolicy**: thay CIDR giữ chỗ (TEST-NET) trong `base/networkpolicy.yaml` bằng địa chỉ thật của DB, object storage, LLM, Embedding, IdP. Khi chưa thay, egress bị chặn (an toàn theo mặc định nhưng ứng dụng sẽ không kết nối được).
5. **Mã hóa at-rest** và **sao lưu**: bật ở dịch vụ managed (xem mục 4); không cấu hình trong manifest.
6. `EMBEDDING_DIM` trong ConfigMap phải bằng giá trị đã dùng khi chạy migration (kích thước cột `vector(N)`).

## 3. Pipeline

| Workflow | Khi nào | Làm gì |
|---|---|---|
| `ci.yml` | mọi PR, push main | lint, type, kiến trúc (import-linter), unit, integration (testcontainers), web, build thử image |
| `cd.yml` | push main → **staging** tự động; `workflow_dispatch` → staging/production | build & push ảnh `ghcr.io/<owner>/docchat/{api,worker,migrate,web}:<sha>` → áp ConfigMap → **migration** → deploy → chờ rollout; lỗi thì `rollout undo` |

Cấu hình GitHub: secret `KUBE_CONFIG_B64` theo từng Environment (`staging`, `production`); đặt **Required reviewers** cho `production`.

## 4. Runbook

### 4.1 Deploy / promote
- Staging: merge vào `main`.
- Production: Actions → CD → *Run workflow* → `environment=production`, `tag=<sha đã chạy ổn trên staging>`. Chờ người duyệt.

### 4.2 Rollback (mục tiêu ≤ 15 phút)
```bash
# Cách nhanh: quay về revision trước
kubectl -n docchat-production rollout undo deployment/api deployment/worker deployment/web
# Hoặc deploy lại tag cũ: Actions → CD → environment=production, tag=<sha cũ>
```
Migration là forward-only (`Database_Design_SQL.md` mục 11): rollback ứng dụng **không** hoàn tác migration. Mọi migration phải tương thích ngược với bản ứng dụng liền trước (thêm cột/bảng trước, bỏ sau một release).

### 4.3 Kill switch hỏi đáp (PRD 5.1)
Tắt (hiệu lực sau ≤ `APP_CONFIG_TTL_SECONDS`, mặc định 30 giây; không cần deploy):
```sql
UPDATE app_config SET value = 'false' WHERE key = 'qa_enabled';   -- dưới vai trò migrator/DBA
```
Bật lại: `'true'`. API hỏi đáp sẽ trả `503 QA_DISABLED` (task B9); tải/xóa tài liệu vẫn hoạt động. Diễn tập kill switch là một phần của F2.

### 4.4 Sao lưu & khôi phục (RPO ≤ 15 phút)
Yêu cầu với dịch vụ PostgreSQL (SQL design 12.1): sao lưu đầy đủ hằng ngày + WAL liên tục, PITR 7 ngày, kiểm thử khôi phục hằng tháng trên staging (RTO ≤ 1 giờ `[TBD: OQ-011]`). Khôi phục: tạo instance mới từ PITR → chạy `alembic current` bằng `migrator` để xác nhận phiên bản → trỏ `docchat-secrets` sang instance mới → restart deployment. **Thời hạn giữ bản sao lưu phải khớp chính sách xóa dữ liệu `[TBD: OQ-012]`.**

### 4.5 Xoay secret
Cập nhật secret trong secret manager → `kubectl -n <ns> rollout restart deployment/api deployment/worker`. Xoay `TELEMETRY_SALT` làm các `user_hash` cũ/mới không so sánh được với nhau.

### 4.6 Sự cố thường gặp
| Triệu chứng | Kiểm tra |
|---|---|
| Pod api `NotReady` | `/ready` lỗi ⇒ không kết nối được CSDL: secret, NetworkPolicy egress, trạng thái DB |
| Tải PDF mãi `processing` | worker chạy không (`kubectl logs deploy/worker`); metric `docchat_ingest_queue_length`; job kẹt: xem truy vấn giám sát ở `Database_Design_SQL.md` 12.3 |
| Truy vấn không thấy dữ liệu của người dùng | quên `SET LOCAL app.user_id` (RLS trả 0 dòng) — lỗi lập trình, không phải mất dữ liệu |
| Job migrate lỗi | `kubectl -n <ns> logs job/docchat-migrate`; deploy đã bị chặn, hệ thống vẫn chạy bản cũ |

## 5. Việc còn mở cho A7
- Staging/production sẽ **không khởi động** cho tới khi có: `AUTH_PROVIDER=oidc` kèm `OIDC_JWKS_URL/OIDC_ISSUER/OIDC_AUDIENCE` (OQ-014) và `STORAGE_BACKEND=s3` (task C1) — API cố ý từ chối cấu hình `dev`/`memory` ở hai môi trường này.
- Chọn nền tảng/vùng và dịch vụ managed `[TBD: OQ-012]`; điền host, CIDR egress.
- Dựng staging thật, diễn tập deploy, rollback ≤ 15 phút, khôi phục DB.
- Xác nhận chỉ cổng 443 mở ra Internet (kiểm bằng quét cổng từ ngoài).
- Cảnh báo/dashboard thuộc F2.
