# B10 — API telemetry

| Thuộc tính | Giá trị |
|---|---|
| Workstream | B — Backend lõi |
| Sprint | S4 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE |
| Story liên quan | US-501 |
| Trạng thái | Hoàn thành — có unit test; trigger allow-list ở CSDL kiểm ở test tích hợp |

## Mô tả

Nhận và lưu sự kiện đo lường nội bộ theo schema allow-list (không có nội dung).

## Phạm vi

- `POST /api/v1/telemetry/events` nhận lô sự kiện.
- Allow-list tên sự kiện và thuộc tính (Blueprint 3.6): vd. `data_notice_accepted`, `upload_succeeded`, `question_sent`, `answer_completed`, `answer_failed`, `answer_stopped`, `citation_opened`, `task_marked_done`, `answer_feedback`.
- Thuộc tính ngoài allow-list bị loại; từ chối nếu chứa chuỗi dài bất thường.
- `user_id` băm một chiều có muối trước khi lưu.
- Ghi bảng `telemetry_events`.

## Hướng dẫn kỹ thuật

- Muối lưu ở secret; xoay muối là việc vận hành.
- Không gửi sang dịch vụ phân tích ngoài (ADR-10).
- Ghi bất đồng bộ nhẹ, lỗi telemetry không ảnh hưởng người dùng.

## Đầu ra / sản phẩm bàn giao

- Router `telemetry`, `application.telemetry`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A3](A3-migration-luoc-do-db.md) — Migration lược đồ cơ sở dữ liệu

**Mở khóa:**
- [E10](E10-telemetry-client.md) — TelemetryClient và sự kiện
- [F1](F1-truy-van-met-bao-cao.md) — Truy vấn MET-001/MET-002 và endpoint báo cáo
- [G4](G4-test-khong-ro-noi-dung.md) — Test không rò nội dung vào log và telemetry

## Tiêu chí chấp nhận

- [ ] Sự kiện hợp lệ được lưu.
- [ ] Thuộc tính lạ bị loại.
- [ ] `user_id` không xuất hiện dạng rõ trong bảng.
- [ ] Payload có `question` bị từ chối.

## Kiểm thử

- Unit test validator; integration test.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 5.4, ADR-10
- UIUX_Blueprint_SDD.md mục 3.6
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
