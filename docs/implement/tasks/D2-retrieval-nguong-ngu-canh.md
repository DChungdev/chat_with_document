# D2 — Retrieval: ngưỡng liên quan và dựng ngữ cảnh

| Thuộc tính | Giá trị |
|---|---|
| Workstream | D — RAG: truy xuất & trả lời |
| Sprint | S3 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | AI/BE |
| Story liên quan | US-202, US-203 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Domain service chọn đoạn đủ liên quan và đánh nhãn nguồn `[S1]…[Sn]`.

## Phạm vi

- Embed câu hỏi qua `EmbeddingPort`.
- Gọi `VectorStorePort`; loại chunk dưới ngưỡng tương đồng tối thiểu (cấu hình).
- Gán nhãn `[S1]…[Sn]` cho từng chunk, giữ ánh xạ nhãn → chunk.
- Đảm bảo đa dạng nguồn khi có nhiều tài liệu (tùy chọn: giới hạn số chunk mỗi tài liệu).
- Trả `RetrievalResult(chunks, labels)`.

## Hướng dẫn kỹ thuật

- Hàm thuần theo port, dễ giả lập.
- Ngưỡng/k đọc từ `AppConfig`, hiệu chỉnh ở D8.
- Cắt tổng độ dài ngữ cảnh theo giới hạn token của LLM.

## Đầu ra / sản phẩm bàn giao

- `packages/core/retrieval`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [D1](D1-vector-store-pgvector.md) — VectorStorePort và adapter pgvector

**Mở khóa:**
- [D3](D3-nhanh-khong-tim-thay.md) — Nhánh ‘không tìm thấy’ không qua LLM
- [D4](D4-llm-port-prompt.md) — LLMPort, adapter Claude và prompt chỉ dùng nguồn
- [G1](G1-unit-test-nghiep-vu.md) — Unit test domain, retrieval và answering

## Tiêu chí chấp nhận

- [ ] Không chunk nào đạt ngưỡng → kết quả rỗng.
- [ ] Nhãn duy nhất và ánh xạ ngược chính xác.
- [ ] Truy vấn nhiều tài liệu trả chunk từ ≥ 2 tài liệu khi liên quan.

## Kiểm thử

- Unit test với `FakeVectorStore`.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.1 (`retrieval`), 3.4B
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
