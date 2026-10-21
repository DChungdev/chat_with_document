# B3 — Xác thực JWT và AuthProvider

| Thuộc tính | Giá trị |
|---|---|
| Workstream | B — Backend lõi |
| Sprint | S1 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE |
| Story liên quan | US-402 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Xác thực mọi yêu cầu API qua JWT/OIDC đứng sau `AuthProvider` trung lập nhà cung cấp (OQ-014 chưa chốt).

## Phạm vi

- Middleware/dependency FastAPI xác thực JWT; trích `user_id`, vai trò (`user`, `evaluator`).
- Adapter `DevAuthProvider` (khóa tĩnh) để phát triển; adapter OIDC (JWKS) làm khung, hoàn thiện khi chốt IdP.
- Phiên hết hạn/không hợp lệ → `401` kèm mã lỗi RFC 7807.
- Truy cập tài nguyên người khác → `404` (không lộ sự tồn tại).
- Tạo `users` lần đầu đăng nhập (just-in-time).

## Hướng dẫn kỹ thuật

- Mọi endpoint trừ `/health` yêu cầu xác thực.
- Kiểm `exp`, `aud`, `iss`; đồng hồ lệch ±60s.
- Vai trò `evaluator` chỉ vào endpoint báo cáo tổng hợp.
- Không log token.

## Đầu ra / sản phẩm bàn giao

- `infra/auth`, dependency `current_user`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B2](B2-ports-repository.md) — Ports và repository PostgreSQL

**Mở khóa:**
- [B4](B4-api-tai-lieu.md) — API tài liệu: tải lên, liệt kê, chi tiết
- [B6](B6-compliance-thong-bao-du-lieu.md) — Compliance: xác nhận thông báo dữ liệu
- [E9](E9-scr07-het-phien.md) — SCR-07 Overlay hết phiên và giữ bản nháp
- [G3](G3-test-co-lap-nguoi-dung.md) — Test cô lập người dùng (US-402)

## Tiêu chí chấp nhận

- [ ] Token hợp lệ → truy cập; hết hạn/sai chữ ký → 401.
- [ ] User A gọi tài nguyên của B → 404.
- [ ] Đổi `AuthProvider` không sửa code endpoint.

## Kiểm thử

- Unit test dependency; integration test với hai user.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 5.1, DC-08, R-A-03
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
