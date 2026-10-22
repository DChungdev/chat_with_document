# D8 — Hiệu chỉnh ngưỡng, k và chunking

| Thuộc tính | Giá trị |
|---|---|
| Workstream | D — RAG: truy xuất & trả lời |
| Sprint | S4 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | AI |
| Story liên quan | US-202, US-301 |
| Trạng thái | Đã có công cụ hiệu chỉnh + báo cáo (docs/implement/reports/retrieval_tuning.md) trên nhà cung cấp GIẢ LẬP; CHƯA ghi giá trị nào vào app_config vì chưa có embedding thật |

## Mô tả

Điều chỉnh tham số theo kết quả D7 để cân bằng bỏ sót và bịa đặt.

## Phạm vi

- Quét lưới: ngưỡng tương đồng, k, kích thước/chồng chunk.
- Chọn cấu hình theo mục tiêu: trích dẫn hợp lệ ≥ 90%, ít ‘không tìm thấy’ sai.
- Ghi cấu hình chốt vào `app_config` và tài liệu quyết định.

## Hướng dẫn kỹ thuật

- Mỗi lần đổi chunking cần ingest lại tập thử.
- Ghi lại đánh đổi (ADR-04).

## Đầu ra / sản phẩm bàn giao

- Báo cáo hiệu chỉnh + cấu hình.

## Phụ thuộc

**Cần hoàn thành trước:**
- [D7](D7-bo-cau-hoi-chuan-danh-gia.md) — Bộ câu hỏi chuẩn và script đánh giá

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Có bảng so sánh các cấu hình.
- [ ] Cấu hình được chọn đạt mục tiêu hoặc ghi rõ khoảng cách.
- [ ] Giá trị lưu vào cấu hình và kiểm bằng D7.

## Kiểm thử

- Chạy lại D7 với cấu hình chọn.

## Tham chiếu

- [SAD.md](../../design/SAD.md) ADR-04, mục 6
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
