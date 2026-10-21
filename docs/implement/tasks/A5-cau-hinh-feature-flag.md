# A5 — Cấu hình, secret và feature flag

| Thuộc tính | Giá trị |
|---|---|
| Workstream | A — Nền tảng & hạ tầng |
| Sprint | S1 |
| Cỡ ước lượng | S (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | DevOps/BE |
| Story liên quan | US-201 |
| Trạng thái | Hoàn thành — có unit test |

## Mô tả

Cung cấp lớp cấu hình tập trung: giới hạn nghiệp vụ trong `app_config` và kill switch `qa_enabled`.

## Phạm vi

- Module `Settings` đọc biến môi trường (pydantic-settings) cho secret/endpoint.
- Service `AppConfig` đọc giá trị từ bảng `app_config` với cache TTL ngắn.
- Feature flag `qa_enabled` (mặc định true) đổi được không cần deploy.
- Không log giá trị secret.

## Hướng dẫn kỹ thuật

- Secret chỉ từ biến môi trường/secret manager, không nằm trong DB hay mã nguồn.
- Giới hạn PDF (`OQ-008`) luôn đọc qua `AppConfig`, không hard-code.
- Cache TTL 30 giây [Đề xuất]; có hàm invalidate cho test.

## Đầu ra / sản phẩm bàn giao

- `packages/core/config`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A3](A3-migration-luoc-do-db.md) — Migration lược đồ cơ sở dữ liệu

**Mở khóa:**
- [B9](B9-kill-switch-hoi-dap.md) — Kill switch hỏi đáp

## Tiêu chí chấp nhận

- [ ] Đổi `qa_enabled` trong DB có hiệu lực sau ≤ TTL.
- [ ] Khóa thiếu trong `app_config` dùng giá trị mặc định có cảnh báo log.
- [ ] Secret không xuất hiện trong log.

## Kiểm thử

- Unit test AppConfig với DB giả; test redact secret.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 5.2 (kill switch), mục 6
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
