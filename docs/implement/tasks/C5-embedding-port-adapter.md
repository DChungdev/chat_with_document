# C5 — EmbeddingPort và adapter

| Thuộc tính | Giá trị |
|---|---|
| Workstream | C — Ingestion |
| Sprint | S2 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE/AI |
| Story liên quan | US-101, US-201 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Tạo vector cho chunk/câu hỏi qua cổng thay thế được; nhà cung cấp chọn sau OQ-012/013.

## Phạm vi

- Port `EmbeddingPort`: `embed_texts(list[str])`, `embed_query(str)`, thuộc tính `dimension`.
- Adapter `FakeEmbedding` (xác định, dựa trên băm) để dev/test.
- Adapter nhà cung cấp thật (**[TBD]**, mô hình đa ngữ hỗ trợ tiếng Việt) – gọi theo lô.
- Timeout, retry backoff, circuit breaker; giới hạn kích thước lô.

## Hướng dẫn kỹ thuật

- `dimension` quyết định kiểu cột `vector(N)` ở A3.
- Không log văn bản được embed.
- Chỉ gửi văn bản chunk/câu hỏi tối thiểu cần thiết (SAD 5.1).

## Đầu ra / sản phẩm bàn giao

- `infra/embedding`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [B2](B2-ports-repository.md) — Ports và repository PostgreSQL

**Mở khóa:**
- [C6](C6-worker-ingest-ghi-chi-muc.md) — Worker ingest end-to-end và ghi chỉ mục

## Tiêu chí chấp nhận

- [ ] Embed lô trả đúng số vector và đúng chiều.
- [ ] Lỗi tạm thời được retry; lỗi kéo dài mở circuit breaker.
- [ ] Có thể đổi adapter bằng cấu hình.

## Kiểm thử

- Unit test với server giả; contract test chung cho các adapter.

## Tham chiếu

- [SAD.md](../../design/SAD.md) ADR-08, mục 2.2
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
