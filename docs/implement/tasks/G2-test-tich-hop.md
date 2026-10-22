# G2 — Test tích hợp với Postgres và MinIO

| Thuộc tính | Giá trị |
|---|---|
| Workstream | G — Chất lượng & bảo mật |
| Sprint | S4 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | QA |
| Story liên quan | — (nền tảng) |
| Trạng thái | Một phần — test tích hợp PostgreSQL/pgvector/RLS đã viết (30 test, marker integration) nhưng CHƯA chạy ở máy này (không có Docker); CI có job integration |

## Mô tả

Test tích hợp bằng hạ tầng thật chạy trong container.

## Phạm vi

- Cấu hình testcontainers Postgres+pgvector và MinIO.
- Kịch bản: tải → ingest → tìm kiếm → hỏi (FakeLLM) → xóa.
- Dữ liệu fixtures PDF mẫu.
- Chạy trong CI (job riêng).

## Hướng dẫn kỹ thuật

- Mỗi test cô lập dữ liệu (schema/DB riêng hoặc rollback).
- Thời gian chạy hợp lý, có thể chạy song song.

## Đầu ra / sản phẩm bàn giao

- Bộ integration test.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B4](B4-api-tai-lieu.md) — API tài liệu: tải lên, liệt kê, chi tiết
- [C6](C6-worker-ingest-ghi-chi-muc.md) — Worker ingest end-to-end và ghi chỉ mục
- [D1](D1-vector-store-pgvector.md) — VectorStorePort và adapter pgvector

**Mở khóa:**
- [G4](G4-test-khong-ro-noi-dung.md) — Test không rò nội dung vào log và telemetry

## Tiêu chí chấp nhận

- [ ] Kịch bản đầy đủ chạy xanh trong CI.
- [ ] Test ổn định (không flaky) qua 10 lần chạy liên tiếp.

## Kiểm thử

- Chạy 10 lần trong CI để phát hiện flaky.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.4
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
