# A4 — pgvector, chỉ mục HNSW và Row-Level Security

| Thuộc tính | Giá trị |
|---|---|
| Workstream | A — Nền tảng & hạ tầng |
| Sprint | S1 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | DevOps/BE |
| Story liên quan | US-402 |
| Trạng thái | Đã triển khai — RLS/HNSW trong migration, helper `user_transaction` có unit test; chưa kiểm trên Postgres thật |

## Mô tả

Bật tìm kiếm vector và cô lập dữ liệu đa người dùng ở tầng CSDL (phòng thủ nhiều lớp).

## Phạm vi

- Bật extension `vector`; tạo chỉ mục HNSW (cosine) trên `chunks.embedding`.
- Bật RLS cho `documents`, `chunks`, `conversations`, `messages`, `citations`, `feedback`: chính sách `user_id = current_setting('app.user_id')::uuid`.
- Role ứng dụng không phải owner/superuser (để RLS có hiệu lực); role riêng cho worker và migration.
- Helper trong persistence: mỗi giao dịch thực hiện `SET LOCAL app.user_id = ...`.
- Worker ghi chunk cho đúng `user_id` của tài liệu (đặt `app.user_id` theo job).

## Hướng dẫn kỹ thuật

- Dùng `FORCE ROW LEVEL SECURITY` để owner cũng bị áp dụng khi cần.
- Thiếu `app.user_id` → truy vấn trả 0 dòng (không lỗi lộ dữ liệu).
- Tham số HNSW (`m`, `ef_construction`, `ef_search`) đặt trong cấu hình; giá trị khởi điểm m=16, ef_construction=64 [Đề xuất].
- Vai trò `evaluator` không có quyền đọc nội dung (`content`, `question`).

## Đầu ra / sản phẩm bàn giao

- Migration RLS + helper đặt `app.user_id`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A3](A3-migration-luoc-do-db.md) — Migration lược đồ cơ sở dữ liệu

**Mở khóa:**
- [D1](D1-vector-store-pgvector.md) — VectorStorePort và adapter pgvector

## Tiêu chí chấp nhận

- [ ] User A không SELECT/UPDATE/DELETE được dòng của B ngay cả khi viết SQL thô bằng role ứng dụng.
- [ ] Không đặt `app.user_id` → 0 dòng.
- [ ] Truy vấn top-k dùng chỉ mục HNSW (EXPLAIN).

## Kiểm thử

- Test SQL trực tiếp với hai user; xem EXPLAIN truy vấn vector.

## Tham chiếu

- [SAD.md](../../design/SAD.md) ADR-02, ADR-07, mục 5.1
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
