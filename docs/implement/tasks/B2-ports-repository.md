# B2 — Ports và repository PostgreSQL

| Thuộc tính | Giá trị |
|---|---|
| Workstream | B — Backend lõi |
| Sprint | S1 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE |
| Story liên quan | US-402 |
| Trạng thái | Đã triển khai — port + repository PostgreSQL + bản trong bộ nhớ. Mọi câu SQL đã qua parser PostgreSQL (pglast); test tích hợp trên Postgres thật đã viết nhưng CHƯA chạy (không có Docker) |

## Mô tả

Khai báo các cổng (port) và triển khai repository PostgreSQL luôn ràng buộc theo `user_id`.

## Phạm vi

- Ports: `DocumentRepository`, `ChunkRepository`, `ConversationRepository`, `MessageRepository`, `JobQueue`, `VectorStorePort` (giao diện; adapter ở D1), `FileStoragePort` (giao diện; adapter ở C1), `LLMPort`, `EmbeddingPort`, `AuthProvider`.
- Triển khai repository bằng SQLAlchemy async + pool kết nối.
- Mọi phương thức nhận `user_id` bắt buộc (không có giá trị mặc định) và đặt `app.user_id` theo giao dịch (A4).
- Unit of Work để gom giao dịch ở tầng application.

## Hướng dẫn kỹ thuật

- Port là `Protocol`/ABC trong `packages/core/ports`; adapter trong `infra/persistence`.
- Không có phương thức 'lấy theo id' thiếu `user_id`.
- Cung cấp bản in-memory cho unit test.

## Đầu ra / sản phẩm bàn giao

- `packages/core/ports`, `infra/persistence`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A3](A3-migration-luoc-do-db.md) — Migration lược đồ cơ sở dữ liệu
- [B1](B1-domain-model.md) — Domain model và quy tắc trạng thái

**Mở khóa:**
- [B3](B3-xac-thuc-authprovider.md) — Xác thực JWT và AuthProvider
- [B4](B4-api-tai-lieu.md) — API tài liệu: tải lên, liệt kê, chi tiết
- [C5](C5-embedding-port-adapter.md) — EmbeddingPort và adapter

## Tiêu chí chấp nhận

- [ ] Repository không trả được dòng của user khác.
- [ ] Thiếu `user_id` là lỗi biên dịch/kiểu hoặc lỗi runtime rõ ràng.
- [ ] Có bản in-memory dùng được trong test.

## Kiểm thử

- Integration test với Postgres thật (testcontainers); kiểm chéo hai user.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.1, ADR-01, ADR-07
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
