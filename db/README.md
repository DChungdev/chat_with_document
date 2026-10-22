# Cơ sở dữ liệu

Nguồn sự thật của lược đồ là [Database_Design_SQL.md](../docs/design/Database_Design_SQL.md) và [Database_Design_VectorDB.md](../docs/design/Database_Design_VectorDB.md). Các tệp trong `migrations/sql/` được trích từ đó; **sửa tài liệu thiết kế và migration cùng nhau**.

| Tệp | Nội dung |
|---|---|
| `init/01-roles.sql` | Chạy **một lần bằng superuser**: vai trò, owner CSDL, `CREATE EXTENSION vector`. Chỉ cho dev/test (mật khẩu `docchat_dev`) |
| `migrations/sql/V001…V006` | extension+kiểu, bảng lõi, RLS+quyền, view/hàm/trigger, dữ liệu tham chiếu, cấu hình ingest |
| `migrations/sql/V00x.down.sql` | Hoàn tác — **chỉ dev/test** (production forward-only) |
| `migrations/versions/` | Revision Alembic: mỗi revision chạy một tệp SQL |
| `seed/dev_users.sql` | Người dùng giả; **không** chạy ở production |
| `tests/` | Kiểm tĩnh bằng pglast (không cần Docker) và test tích hợp (`-m integration`) |

```bash
alembic upgrade head          # dùng MIGRATOR_DATABASE_URL
EMBEDDING_DIM=768 alembic upgrade head   # nếu mô hình embedding khác 1024 chiều
```

Tham số mẫu (thay khi chạy, chỉ nhận số nguyên dương): `EMBEDDING_DIM` (mặc định 1024), `HNSW_M` (16), `HNSW_EF_CONSTRUCTION` (64).
Đổi chiều vector sau khi đã có dữ liệu cần cột mới + re-embed (VectorDB mục 8), không `ALTER` tại chỗ.

`V006` hiện là cấu hình mặc định cho ingest. Tinh chỉnh chỉ mục HNSW (VectorDB mục 4.3) sẽ là migration sau (V007), chỉ làm sau khi đo trên dữ liệu thật.
Bảng `alembic_version` nằm ở schema `public` để `downgrade` V001 (xóa schema `docchat`) không kéo theo nó.
