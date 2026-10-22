# G1 — Unit test domain, retrieval và answering

| Thuộc tính | Giá trị |
|---|---|
| Workstream | G — Chất lượng & bảo mật |
| Sprint | S4 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | QA |
| Story liên quan | — (nền tảng) |
| Trạng thái | Hoàn thành — 386 test, coverage 94.8%, ngưỡng cứng 80% trong CI (yêu cầu tối thiểu 70%) |

## Mô tả

Đạt bao phủ ≥ 70% logic nghiệp vụ.

## Phạm vi

- Test domain (trạng thái), retrieval (ngưỡng, nhãn), answering (prompt, trích dẫn, ‘không tìm thấy’).
- Dùng port giả (`FakeLLM`, `FakeEmbedding`, `FakeVectorStore`).
- Báo cáo coverage trong CI, ngưỡng thất bại < 70%.

## Hướng dẫn kỹ thuật

- Test tham số hóa; tránh phụ thuộc mạng.
- Đặt fixtures dùng chung trong `packages/core/tests`.

## Đầu ra / sản phẩm bàn giao

- Bộ unit test + cấu hình coverage.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B1](B1-domain-model.md) — Domain model và quy tắc trạng thái
- [D2](D2-retrieval-nguong-ngu-canh.md) — Retrieval: ngưỡng liên quan và dựng ngữ cảnh
- [D5](D5-ghep-trich-dan.md) — Ghép trích dẫn và kiểm tra hậu xử lý

**Mở khóa:**
- Không có

## Tiêu chí chấp nhận

- [ ] Coverage logic nghiệp vụ ≥ 70%.
- [ ] CI chặn khi coverage dưới ngưỡng.
- [ ] Test chạy < 2 phút.

## Kiểm thử

- Chính task này là test; xác minh bằng báo cáo coverage.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 2.4 (khả bảo trì/kiểm thử)
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
