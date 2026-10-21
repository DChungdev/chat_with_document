# G3 — Test cô lập người dùng (US-402)

| Thuộc tính | Giá trị |
|---|---|
| Workstream | G — Chất lượng & bảo mật |
| Sprint | S4 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | QA |
| Story liên quan | US-402 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Chứng minh user A không thể thấy hay dùng dữ liệu của user B.

## Phạm vi

- Hai user: A tải PDF & hỏi; B thử mọi đường truy cập (danh sách, chi tiết, xóa, citations, hội thoại, truy vấn vector, `documentIds` của A trong câu hỏi).
- Kết quả mong đợi: 404/rỗng, không rò thông tin.
- Test tầng SQL thô với role ứng dụng (RLS).
- Chạy tự động trong CI.

## Hướng dẫn kỹ thuật

- Thất bại là blocker phát hành.
- Gồm cả vai trò `evaluator` không đọc được nội dung.

## Đầu ra / sản phẩm bàn giao

- Bộ test cô lập.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B3](B3-xac-thuc-authprovider.md) — Xác thực JWT và AuthProvider
- [D1](D1-vector-store-pgvector.md) — VectorStorePort và adapter pgvector
- [B8](B8-api-xem-nguon-dan.md) — API xem nguồn dẫn

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Mọi đường truy cập chéo bị chặn.
- [ ] Test chạy trong CI.
- [ ] Phản hồi không phân biệt ‘không tồn tại’ và ‘không có quyền’.

## Kiểm thử

- Chính task này là test.

## Tham chiếu

- [SAD.md](../../design/SAD.md) ADR-07, mục 5.1
- US-402
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
