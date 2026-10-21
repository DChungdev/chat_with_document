# G5 — Test độ tin cậy trích dẫn và xóa dữ liệu

| Thuộc tính | Giá trị |
|---|---|
| Workstream | G — Chất lượng & bảo mật |
| Sprint | S4 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | QA |
| Story liên quan | US-301, US-302, US-103 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Đảm bảo không có trích dẫn tới trang không tồn tại và xóa tài liệu hoạt động đúng.

## Phạm vi

- Test trích dẫn: mọi `(tài liệu, trang)` trong citations thuộc tập chunk đã truy xuất và nằm trong số trang thực.
- Test nhãn bịa bị loại.
- Test xóa: chunk mất, PDF gốc mất, citation cũ `valid=false`, câu hỏi mới không dùng tài liệu đã xóa.

## Hướng dẫn kỹ thuật

- Dùng bộ câu hỏi chuẩn D7 làm đầu vào cho nhánh trích dẫn.

## Đầu ra / sản phẩm bàn giao

- Bộ test trích dẫn/xóa.

## Phụ thuộc

**Cần hoàn thành trước:**
- [D5](D5-ghep-trich-dan.md) — Ghép trích dẫn và kiểm tra hậu xử lý
- [B11](B11-xoa-tai-lieu.md) — Xóa tài liệu

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] 0 trích dẫn tới trang không tồn tại trên bộ test.
- [ ] Sau xóa không còn dữ liệu dẫn xuất.
- [ ] Citation cũ trả ‘Nguồn không còn khả dụng’.

## Kiểm thử

- Chính task này là test.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 2.4, 3.4D
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
