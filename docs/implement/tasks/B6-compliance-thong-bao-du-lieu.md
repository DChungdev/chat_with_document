# B6 — Compliance: xác nhận thông báo dữ liệu

| Thuộc tính | Giá trị |
|---|---|
| Workstream | B — Backend lõi |
| Sprint | S2 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE |
| Story liên quan | US-401 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Bắt buộc người dùng xác nhận thông báo sử dụng dữ liệu trước khi tải tệp.

## Phạm vi

- Bảng/dịch vụ `data_notice_acceptances` (user, phiên bản thông báo, thời điểm).
- `GET /api/v1/compliance/notice` (nội dung + phiên bản; nội dung cấu hình được — **[TBD: OQ-012, OQ-013]**).
- `POST /api/v1/compliance/notice/accept`.
- Chặn `POST /documents` nếu chưa xác nhận phiên bản hiện hành → `403 NOTICE_NOT_ACCEPTED`.
- Ghi `audit_log` khi xác nhận.

## Hướng dẫn kỹ thuật

- Đổi phiên bản thông báo buộc xác nhận lại.
- Nội dung thông báo lấy từ `app_config`, không hard-code.

## Đầu ra / sản phẩm bàn giao

- Router `compliance`, use case.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B3](B3-xac-thuc-authprovider.md) — Xác thực JWT và AuthProvider

**Mở khóa:**
- [E2](E2-scr01-thong-bao-du-lieu.md) — SCR-01 Màn chào và thông báo dữ liệu

## Tiêu chí chấp nhận

- [ ] Chưa xác nhận → upload bị chặn.
- [ ] Xác nhận → upload được.
- [ ] Tăng phiên bản → phải xác nhận lại.
- [ ] Có dòng audit.

## Kiểm thử

- Integration test luồng xác nhận.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.1 (`application.compliance`)
- US-401
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
