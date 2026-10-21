# A7 — Staging và pipeline triển khai

| Thuộc tính | Giá trị |
|---|---|
| Workstream | A — Nền tảng & hạ tầng |
| Sprint | S5 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | DevOps/BE |
| Story liên quan | — (nền tảng) |
| Trạng thái | Đã viết manifest, pipeline CD và runbook — CHƯA diễn tập (chưa có cluster/staging, OQ-012) |

## Mô tả

Môi trường staging giống production thu nhỏ và pipeline deploy tự động, phục vụ UAT và bộ câu hỏi chuẩn.

## Phạm vi

- Dockerfile production (đa giai đoạn) cho api/worker/web.
- Manifest triển khai (Kubernetes hoặc dịch vụ container được quản lý — **[TBD]**), reverse proxy + TLS 1.2+.
- Pipeline CD: build image → push registry → deploy staging tự động từ `main`; promote production thủ công.
- Mã hóa at-rest cho Postgres và object storage; secret từ secret manager.
- Egress allow-list chỉ tới LLM/Embedding/IdP; sao lưu Postgres hằng ngày + WAL (RPO ≤ 15 phút).
- Runbook: deploy, rollback, bật/tắt kill switch, khôi phục DB.

## Hướng dẫn kỹ thuật

- Dữ liệu thật chỉ vào staging/production sau khi pháp chế duyệt (OQ-012/013).
- API ≥ 2 bản sao ở prod; worker 1–2; theo SAD 3.6.
- Chọn nền tảng đám mây/vùng khi OQ-012 được chốt; thiết kế manifest trung lập nhà cung cấp.

## Đầu ra / sản phẩm bàn giao

- Manifest triển khai + runbook trong `deploy/`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A2](A2-docker-compose-dev.md) — Môi trường dev bằng Docker Compose
- [A6](A6-logging-metrics-tracing.md) — Logging có allow-list, metrics và tracing

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Deploy staging tự động thành công từ `main`.
- [ ] Rollback về bản trước trong ≤ 15 phút theo runbook.
- [ ] Sao lưu chạy và khôi phục thử thành công.
- [ ] Chỉ cổng 443 mở ra Internet.

## Kiểm thử

- Diễn tập deploy/rollback và khôi phục DB trên staging.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.5, 3.6, 5.2
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
