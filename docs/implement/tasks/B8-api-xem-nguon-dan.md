# B8 — API xem nguồn dẫn

| Thuộc tính | Giá trị |
|---|---|
| Workstream | B — Backend lõi |
| Sprint | S3 |
| Cỡ ước lượng | S (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE |
| Story liên quan | US-302 |
| Trạng thái | Hoàn thành — có unit test; JOIN chunks kiểm ở test tích hợp |

## Mô tả

Trả đoạn gốc cho một trích dẫn để người dùng xác minh.

## Phạm vi

- `GET /api/v1/citations/{id}` → tên tệp, trang, snippet, `valid`.
- Nếu tài liệu đã xóa → `valid=false` với thông điệp ‘Nguồn không còn khả dụng’ (không trả 500/rỗng).
- Kiểm quyền sở hữu.

## Hướng dẫn kỹ thuật

- Ghi telemetry `citation_opened` được thực hiện ở FE/B10, không log snippet.
- Snippet cắt theo độ dài tối đa cấu hình.

## Đầu ra / sản phẩm bàn giao

- Router `citations`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B7](B7-api-hoi-dap-sse.md) — API hội thoại và hỏi đáp qua SSE

**Mở khóa:**
- [E7](E7-scr05-chip-trich-dan-panel-nguon.md) — Chip trích dẫn và panel nguồn
- [G3](G3-test-co-lap-nguoi-dung.md) — Test cô lập người dùng (US-402)

## Tiêu chí chấp nhận

- [ ] Citation hợp lệ → đủ trường.
- [ ] Sau khi xóa tài liệu → `valid=false`.
- [ ] Citation của user khác → 404.

## Kiểm thử

- Integration test.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.4C
- US-302
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
