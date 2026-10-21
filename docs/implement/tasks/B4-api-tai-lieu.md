# B4 — API tài liệu: tải lên, liệt kê, chi tiết

| Thuộc tính | Giá trị |
|---|---|
| Workstream | B — Backend lõi |
| Sprint | S2 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE |
| Story liên quan | US-101, US-102 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Cung cấp endpoint tải PDF (bất đồng bộ) và xem danh sách/trạng thái tài liệu.

## Phạm vi

- `POST /api/v1/documents` (multipart, hỗ trợ nhiều tệp, header `Idempotency-Key`) → `202` trong ≤ 2s.
- Kiểm tra: chữ ký tệp `%PDF-`, MIME, kích thước/số lượng từ `AppConfig`, đã xác nhận thông báo dữ liệu (B6).
- Ghi PDF qua `FileStoragePort`, tạo `documents(status=processing)`, đưa job vào hàng đợi trong cùng giao dịch.
- Xử lý từng tệp độc lập: tệp lỗi trả lỗi riêng, các tệp còn lại vẫn nhận.
- `GET /api/v1/documents` (tên, kích thước, thời điểm tải, trạng thái, `error_code`); `GET /documents/{id}`.

## Hướng dẫn kỹ thuật

- Idempotency: lưu khóa + băm nội dung; lặp lại trả cùng kết quả.
- Không lưu tên tệp vào log; tên tệp chỉ ở DB.
- Phản hồi lỗi theo B5; mã lỗi: `FILE_TYPE_INVALID`, `FILE_TOO_LARGE`, `TOO_MANY_FILES`, `NOTICE_NOT_ACCEPTED`.
- Danh sách có phân trang đơn giản, sắp theo thời điểm tải giảm dần.

## Đầu ra / sản phẩm bàn giao

- Router `documents`, use case `application.documents`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B2](B2-ports-repository.md) — Ports và repository PostgreSQL
- [B3](B3-xac-thuc-authprovider.md) — Xác thực JWT và AuthProvider
- [C1](C1-file-storage-s3.md) — FileStoragePort và adapter S3/MinIO

**Mở khóa:**
- [B5](B5-loi-rfc7807-rate-limit.md) — Chuẩn lỗi RFC 7807 và rate limit
- [B11](B11-xoa-tai-lieu.md) — Xóa tài liệu
- [E3](E3-scr02-man-chinh-rong-tai-len.md) — SCR-02 Màn chính trạng thái rỗng và tải lên
- [E4](E4-scr03-danh-sach-tai-lieu.md) — SCR-03 Danh sách tài liệu và trạng thái
- [G2](G2-test-tich-hop.md) — Test tích hợp với Postgres và MinIO
- [G8](G8-ra-soat-bao-mat.md) — Rà soát bảo mật

## Tiêu chí chấp nhận

- [ ] Tải PDF hợp lệ → 202 và xuất hiện `processing`.
- [ ] Tệp .txt đổi đuôi .pdf bị từ chối (kiểm chữ ký).
- [ ] Gửi lại cùng `Idempotency-Key` không tạo bản ghi trùng.
- [ ] Lô 3 tệp có 1 tệp lỗi → 2 tệp được nhận.

## Kiểm thử

- Integration test API với MinIO+Postgres; test idempotency; test giới hạn.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.4A
- API_Design.md (nếu có)
- User story US-101, US-102
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
