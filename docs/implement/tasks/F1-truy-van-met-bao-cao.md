# F1 — Truy vấn MET-001/MET-002 và endpoint báo cáo

| Thuộc tính | Giá trị |
|---|---|
| Workstream | F — Đo lường |
| Sprint | S4 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE/FE |
| Story liên quan | US-501 |
| Trạng thái | Hoàn thành — endpoint, SQL fn_mvp_report (V008) và bản bộ nhớ có test; test trên PostgreSQL thật đã viết nhưng CHƯA chạy (không có Docker). Chưa có số liệu thật; conclusive=false cho tới khi chốt mục tiêu/baseline [TBD: OQ-009] |

## Mô tả

Tính chỉ số đánh giá MVP từ `telemetry_events` mà không xử lý thủ công.

## Phạm vi

- Định nghĩa MET-001/MET-002 theo BRD/PRD đã duyệt (nếu chưa duyệt → ghi rõ giả định và ‘chưa thể kết luận’).
- View/truy vấn SQL tổng hợp theo người dùng băm, theo ngày.
- `GET /api/v1/reports/mvp` chỉ vai trò `evaluator`; chỉ trả số liệu tổng hợp.
- So sánh với baseline/mục tiêu từ `app_config`.

## Hướng dẫn kỹ thuật

- Tuyệt đối không join sang bảng nội dung (`messages`, `chunks`).
- Cần xác nhận định nghĩa chỉ số với Minh/PO trước khi khóa (OQ-005).
- Kèm dữ liệu thử để kiểm chứng.

## Đầu ra / sản phẩm bàn giao

- Truy vấn + endpoint báo cáo.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B10](B10-api-telemetry.md) — API telemetry

**Mở khóa:**
- [E11](E11-scr09-bao-cao-danh-gia.md) — SCR-09 Báo cáo đánh giá MVP

## Tiêu chí chấp nhận

- [ ] Với bộ sự kiện giả, MET-001/002 tính ra đúng giá trị kỳ vọng.
- [ ] Người dùng thường nhận 403.
- [ ] Phản hồi không chứa nội dung người dùng.

## Kiểm thử

- Unit test SQL với dữ liệu mẫu; integration test quyền.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 5.4
- User_Stories.html US-501
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
