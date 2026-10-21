# E1 — Khởi tạo SPA, routing, API client và design tokens

| Thuộc tính | Giá trị |
|---|---|
| Workstream | E — Frontend |
| Sprint | S1 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | FE |
| Story liên quan | — (nền tảng) |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Khung frontend React + TypeScript + Vite dùng chung cho mọi màn hình.

## Phạm vi

- Cấu trúc thư mục theo tính năng; routing (react-router).
- API client có kiểu (sinh từ OpenAPI nếu có), tự gắn JWT, xử lý `401` (kích hoạt overlay SCR-07) và lỗi RFC 7807.
- Design tokens (màu, khoảng cách, chữ) rút từ prototype; theme sáng/tối theo `prefers-color-scheme`.
- Thành phần nền: Button, Dialog, Toast, Banner, Badge trạng thái (biểu tượng + chữ).
- Cấu hình test (Vitest + Testing Library) và Storybook tùy chọn.

## Hướng dẫn kỹ thuật

- Desktop-first; hỗ trợ Chrome/Edge/Safari 2 phiên bản gần nhất.
- Không lưu token trong localStorage nếu có lựa chọn an toàn hơn (cookie httpOnly) — theo OQ-014.
- Không đưa nội dung người dùng vào bất kỳ công cụ phân tích bên thứ ba.

## Đầu ra / sản phẩm bàn giao

- `apps/web` khung + thư viện thành phần nền.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A1](A1-khoi-tao-monorepo-ci.md) — Khởi tạo monorepo, lint/format và CI

**Mở khóa:**
- [E2](E2-scr01-thong-bao-du-lieu.md) — SCR-01 Màn chào và thông báo dữ liệu
- [E3](E3-scr02-man-chinh-rong-tai-len.md) — SCR-02 Màn chính trạng thái rỗng và tải lên
- [E6](E6-scr04-khung-chat-sse.md) — SCR-04 Khung chat và streaming SSE
- [E9](E9-scr07-het-phien.md) — SCR-07 Overlay hết phiên và giữ bản nháp
- [E11](E11-scr09-bao-cao-danh-gia.md) — SCR-09 Báo cáo đánh giá MVP

## Tiêu chí chấp nhận

- [ ] `pnpm dev` chạy; build production thành công.
- [ ] Trạng thái nhận biết được bằng chữ/biểu tượng, không chỉ màu.
- [ ] Lỗi 401 từ API kích hoạt luồng hết phiên.
- [ ] Theme sáng/tối hoạt động.

## Kiểm thử

- Unit test API client (mock fetch); test render thành phần nền.

## Tham chiếu

- [UIUX_Blueprint_SDD.md](../../design/UIUX_Blueprint_SDD.md) mục 3.1
- Prototype: [app.html](../../design/UI_UX_design/app.html)
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
