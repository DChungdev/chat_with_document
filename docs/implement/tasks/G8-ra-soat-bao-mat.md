# G8 — Rà soát bảo mật

| Thuộc tính | Giá trị |
|---|---|
| Workstream | G — Chất lượng & bảo mật |
| Sprint | S5 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | QA/Security |
| Story liên quan | — (nền tảng) |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Rà soát các rủi ro bảo mật đặc thù của hệ thống RAG.

## Phạm vi

- Prompt injection qua nội dung PDF (bộ test tấn công).
- Tệp tải lên độc hại (PDF giả, zip bomb, kích thước lớn); quét mã độc [Đề xuất].
- Rate limit và chống lạm dụng.
- Quản lý secret, cấu hình CORS/CSP, kiểm thử XSS ở phần hiển thị Markdown.
- Rà soát phụ thuộc (SCA) và image.

## Hướng dẫn kỹ thuật

- Có thể dùng skill security-review của Claude Code cho phần diff.
- Ghi kết quả và hạn mức chấp nhận rủi ro.

## Đầu ra / sản phẩm bàn giao

- Báo cáo bảo mật.

## Phụ thuộc

**Cần hoàn thành trước:**
- [D4](D4-llm-port-prompt.md) — LLMPort, adapter Claude và prompt chỉ dùng nguồn
- [B5](B5-loi-rfc7807-rate-limit.md) — Chuẩn lỗi RFC 7807 và rate limit
- [B4](B4-api-tai-lieu.md) — API tài liệu: tải lên, liệt kê, chi tiết

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Không còn lỗ hổng nghiêm trọng/cao chưa xử lý.
- [ ] Prompt injection không làm LLM bỏ qua ràng buộc nguồn.
- [ ] Báo cáo rà soát được lưu.

## Kiểm thử

- Kiểm thử thủ công + công cụ tự động.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 5.1
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
