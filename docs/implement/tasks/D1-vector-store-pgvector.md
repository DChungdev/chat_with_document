# D1 — VectorStorePort và adapter pgvector

| Thuộc tính | Giá trị |
|---|---|
| Workstream | D — RAG: truy xuất & trả lời |
| Sprint | S3 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | AI/BE |
| Story liên quan | US-201, US-203, US-402 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Tìm top-k chunk liên quan trong phạm vi người dùng và tài liệu được chọn.

## Phạm vi

- Port `VectorStorePort.search(user_id, document_ids, query_vector, k)` → danh sách (chunk, độ tương đồng).
- Adapter pgvector: toán tử cosine, `ORDER BY embedding <=> :q LIMIT k`.
- Lọc bắt buộc: `user_id`, `document_id IN (...)`, tài liệu `status=ready`.
- Đặt `ef_search` theo cấu hình.
- Trả kèm `document_id`, tên tệp, `page_start`, `page_end`, `content`.

## Hướng dẫn kỹ thuật

- Phụ thuộc RLS làm lớp bảo vệ thứ hai; vẫn lọc `user_id` tường minh.
- Giới hạn số tài liệu mỗi truy vấn (10).
- Tránh lọc sau khi ANN (post-filter) làm mất kết quả: cân nhắc `iterative scan`/tăng `ef_search`.

## Đầu ra / sản phẩm bàn giao

- `infra/persistence/vector_store`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A4](A4-pgvector-hnsw-rls.md) — pgvector, chỉ mục HNSW và Row-Level Security
- [C6](C6-worker-ingest-ghi-chi-muc.md) — Worker ingest end-to-end và ghi chỉ mục

**Mở khóa:**
- [D2](D2-retrieval-nguong-ngu-canh.md) — Retrieval: ngưỡng liên quan và dựng ngữ cảnh
- [G2](G2-test-tich-hop.md) — Test tích hợp với Postgres và MinIO
- [G3](G3-test-co-lap-nguoi-dung.md) — Test cô lập người dùng (US-402)

## Tiêu chí chấp nhận

- [ ] Kết quả chỉ chứa chunk thuộc user và tài liệu được chọn.
- [ ] Tài liệu `processing`/`error` không xuất hiện.
- [ ] Truy vấn ≤ 200 ms trên tập thử ~10 PDF [Đề xuất].

## Kiểm thử

- Integration test hai user; test lọc theo `document_ids`; đo độ trễ.

## Tham chiếu

- [SAD.md](../../design/SAD.md) ADR-02
- Database_Design_VectorDB.md
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
