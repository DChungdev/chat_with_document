# B11 — Xóa tài liệu

| Thuộc tính | Giá trị |
|---|---|
| Workstream | B — Backend lõi |
| Sprint | S2 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE |
| Story liên quan | US-103 |
| Trạng thái | Hoàn thành — có unit test; thiếu bảng dọn dẹp nên PDF mồ côi chỉ được ghi log `storage_orphaned` |

## Mô tả

Xóa tài liệu và mọi dữ liệu dẫn xuất, đồng thời giữ tính hợp lệ của lịch sử trích dẫn.

## Phạm vi

- `DELETE /api/v1/documents/{id}`.
- Xóa `chunks` (cascade), xóa PDF gốc trong object storage, đánh dấu `citations.valid=false`.
- Ghi `audit_log` (user, hành động, document_id, thời điểm; không ghi nội dung).
- Huỷ job ingest đang chờ nếu tài liệu còn `processing`.
- Câu hỏi mới không dùng tài liệu đã xóa.

## Hướng dẫn kỹ thuật

- Làm theo thứ tự an toàn: giao dịch DB trước, xóa tệp S3 sau (có retry); nếu xóa S3 lỗi → ghi job dọn dẹp.
- Thời hạn xóa vật lý toàn bộ kể cả bản sao lưu **[TBD: OQ-012]**.

## Đầu ra / sản phẩm bàn giao

- Use case `delete_document`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B4](B4-api-tai-lieu.md) — API tài liệu: tải lên, liệt kê, chi tiết
- [C1](C1-file-storage-s3.md) — FileStoragePort và adapter S3/MinIO

**Mở khóa:**
- [E5](E5-scr06-xac-nhan-xoa.md) — SCR-06 Hộp thoại xác nhận xóa tài liệu
- [G5](G5-test-trich-dan-xoa.md) — Test độ tin cậy trích dẫn và xóa dữ liệu

## Tiêu chí chấp nhận

- [ ] Xóa xong, GET trả 404; chunk không còn.
- [ ] Citation cũ có `valid=false`.
- [ ] Có dòng audit.
- [ ] Xóa tài liệu của user khác → 404.

## Kiểm thử

- Integration test với MinIO; test xóa khi đang `processing`.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.4D
- US-103
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
