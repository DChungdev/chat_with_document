# E10 — TelemetryClient và sự kiện

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S4 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE |
| Story liên quan | US-501 |
| Trạng thái | Hoàn thành ở chế độ local — có vitest + Playwright (Edge) + axe; chưa chạy trên Chrome/Firefox/Safari, chưa có Claude/backend PG thật |

## Mô tả

Thu sự kiện đo MET-001/MET-002 từ giao diện theo allow-list.

## Phạm vi

- `TelemetryClient.track(name, props)` kiểm allow-list phía client, gom lô, gửi `POST /telemetry/events`.
- Gắn sự kiện: `data_notice_accepted`, `upload_*`, `question_sent`, `answer_completed`, `answer_failed`, `citation_opened`, `document_deleted`, `task_marked_done`.
- Điều khiển `task_marked_done` (‘Tôi đã có thông tin cần tìm’) — vị trí chốt theo OQ-005.
- Hàng đợi offline ngắn, mất kết nối không ảnh hưởng UI.

## Hướng dẫn kỹ thuật

- Tuyệt đối không gửi nội dung câu hỏi/câu trả lời/tên tệp.
- Thêm `session_id` ngẫu nhiên, không định danh cá nhân.
- Lỗi telemetry bị nuốt, không hiện cho người dùng.

## Đầu ra / sản phẩm bàn giao

- Module telemetry FE.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B10](B10-api-telemetry.md) — API telemetry
- [E6](E6-scr04-khung-chat-sse.md) — SCR-04 Khung chat và streaming SSE

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Mỗi hành động chính phát đúng một sự kiện.
- [ ] Payload không chứa trường ngoài allow-list.
- [ ] Mất mạng không gây lỗi UI.

## Kiểm thử

- Unit test allow-list; kiểm payload trong e2e.

## Tham chiếu

- [UIUX_Blueprint_SDD.md](../../design/UIUX_Blueprint_SDD.md) mục 3.6
- [User_Stories.html](../../requirements/User_Stories.html) US-501
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
