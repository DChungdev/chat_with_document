# Thiết kế CSDL vector — Công cụ “Chat với tài liệu”

**Số tài liệu / Phiên bản:** DB-VEC-DOCCHAT-001 / v0.1 — Bản nháp
**Ngày lập:** 2026-10-21
**Công nghệ:** PostgreSQL 16 + **pgvector ≥ 0.8** (bảng `chunks` của [Database_Design_SQL.md](Database_Design_SQL.md) mục 4.4)
**Nguồn đầu vào:** [PRD.md](../requirements/PRD.md), [BRD.md](../requirements/BRD.md), [SAD.md](SAD.md) (ADR-02, ADR-03, ADR-04), [API_Design.md](API_Design.md); prompt [databaseDesign_VectorDB_prompt.md](../../design/databaseDesign_VectorDB_prompt.md)

> **Quy ước:** **[Đề xuất]** = quyết định thiết kế cần xác nhận; **[TBD: OQ-xxx]** = câu hỏi mở, không phải quyết định. Mọi tham số truy xuất (k, ngưỡng, `ef_search`) phải được **hiệu chỉnh bằng bộ câu hỏi chuẩn** (`OQ-009`) trước khi khóa.

---

## 1. Yêu cầu

### 1.1 Yêu cầu nghiệp vụ → truy xuất vector
| Yêu cầu | Hệ quả cho CSDL vector |
|---|---|
| BR-002/BR-003, US-201 Hỏi đáp trên PDF | Tìm đoạn (chunk) gần nghĩa nhất với câu hỏi trong phạm vi tài liệu của người dùng |
| US-202 Báo “không tìm thấy” | Cần điểm tương đồng (score) tin cậy để đặt ngưỡng loại bỏ |
| US-203 Tổng hợp nhiều PDF | Kết quả phải đại diện nhiều tài liệu, không bị một tệp chiếm hết top-k |
| US-301, US-302 Nguồn dẫn | Mỗi vector gắn `document_id`, `page_start/page_end`, văn bản gốc của chunk |
| US-103, RSK-002 Xóa dữ liệu | Xóa tài liệu xóa luôn vector (cascade); không còn bản sao ở nơi khác |
| US-402 Cô lập | Mọi truy vấn lọc theo `user_id`; RLS bảo vệ lớp thứ hai |
| PRD 5.1 Hiệu năng | Token đầu ≤ 5s p95 ⇒ truy xuất vector ≤ 300ms p95 [Đề xuất] |

### 1.2 Đặc tính vector [Đề xuất]
| Hạng mục | Giá trị | Ghi chú |
|---|---|---|
| Mô hình embedding | Mô hình **đa ngữ, hỗ trợ tiếng Việt**, qua `EmbeddingPort` | Nhà cung cấp/vị trí xử lý `[TBD: OQ-012/013]`; ngôn ngữ tài liệu `[TBD: OQ-008]` |
| Chiều vector | **1024** (tham số; sửa trong DDL nếu đổi mô hình) | Phải khớp mô hình được chọn |
| Kiểu lưu | `vector(1024)` float32; tùy chọn `halfvec(1024)` (float16) cho chỉ mục | Xem 4.3 |
| Chuẩn hóa | Vector chuẩn hóa L2 | Cosine ≡ tích vô hướng, ổn định điểm số |
| Số vector | ≈ 300 chunk/tài liệu × ≤ 50 tài liệu × ≤ 50 người dùng ≈ **750k** (cận trên MVP) | Thực tế thấp hơn |
| Tần suất cập nhật | Theo lô khi tải tài liệu (batch); không cập nhật tại chỗ | Chunk bất biến; sửa = xóa + tạo lại |
| Đa phương thức | Không (chỉ văn bản; PDF quét/OCR ngoài MVP, `OQ-008`) | — |

### 1.3 Đặc tính metadata
| Hạng mục | Mô tả |
|---|---|
| Có cấu trúc | `id`, `document_id`, `user_id`, `ordinal`, `page_start`, `page_end`, `token_count`, `created_at`, `embedding_model` |
| Bán cấu trúc | Không dùng trong MVP (tránh JSONB trên đường truy vấn nóng). Dự phòng cột `meta jsonb` khi cần thêm (tiêu đề mục, ngôn ngữ) |
| Phi cấu trúc | `text` (nội dung chunk) |
| Tĩnh / động | Tất cả tĩnh (bất biến sau khi ghi). Trạng thái tài liệu (`documents.status`) nằm ở bảng khác |
| Dung lượng / chunk | text ~3 KB + vector 4 KB + metadata ~0,1 KB ≈ **7 KB** ⇒ 750k chunk ≈ 5,3 GB (chưa gồm chỉ mục) |
| Trường lọc | `user_id` (bắt buộc), `document_id IN (…)` (tùy chọn), `documents.status = 'ready'` (qua JOIN) |
| Trường sắp xếp | Khoảng cách vector; phụ: `document_id`, `ordinal` (khi dựng ngữ cảnh) |
| Trường nhóm | `document_id` (hạn mức mỗi tài liệu — US-203) |
| Truy vấn metadata | Bằng nhau (`user_id`, `document_id`), thuộc tập (`ANY`). Không cần range, geo, full-text trong MVP |

---

## 2. Lựa chọn công nghệ

| Phương án | Ưu | Nhược | Kết luận |
|---|---|---|---|
| **pgvector (PostgreSQL)** | Một kho; ACID; lọc bằng SQL/RLS; xóa cascade; ít vận hành | Quy mô giới hạn (hàng chục triệu vector), tinh chỉnh bằng tay | **Chọn cho MVP** (SAD ADR-02) |
| Qdrant / Milvus / Weaviate | Lọc metadata và mở rộng mạnh | Thêm hệ thống vận hành, đồng bộ xóa/cô lập giữa hai kho, thêm bề mặt rò rỉ | Phương án nâng cấp |
| Pinecone / dịch vụ quản lý | Không phải vận hành | Dữ liệu rời hạ tầng riêng — chưa được pháp chế duyệt (`OQ-012/013`) | Không chọn |
| Elasticsearch / Redis Stack / Chroma | Hybrid / nhanh / đơn giản | Không cần thiết cho MVP | Không chọn |

**Điều kiện kích hoạt di chuyển sang vector DB chuyên dụng** (qua `VectorStorePort`, chỉ đổi adapter): > ~5 triệu chunk, p95 truy xuất > 300ms dù đã tinh chỉnh, hoặc cần lọc metadata phức tạp/đa tenant lớn.

---

## 3. Lược đồ

Lược đồ DDL chính thức nằm ở SQL design 4.4; trích lại để tiện đối chiếu:

```sql
CREATE TABLE chunks (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     uuid         NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id         uuid         NOT NULL REFERENCES users(id)     ON DELETE CASCADE,
    ordinal         integer      NOT NULL CHECK (ordinal >= 0),
    page_start      integer      NOT NULL CHECK (page_start >= 1),
    page_end        integer      NOT NULL,
    text            text         NOT NULL CHECK (char_length(text) > 0),
    token_count     integer      NOT NULL CHECK (token_count > 0),
    embedding       vector(1024) NOT NULL,
    embedding_model text         NOT NULL,
    created_at      timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT uq_chunks_doc_ordinal UNIQUE (document_id, ordinal),
    CONSTRAINT ck_chunks_pages CHECK (page_end >= page_start)
);
```

| Cột | Vai trò trong truy xuất |
|---|---|
| `embedding` | Khóa tìm kiếm ANN (khoảng cách cosine `<=>`) |
| `user_id` | Lọc cô lập + RLS; phi chuẩn hóa để tránh JOIN |
| `document_id` | Lọc phạm vi tài liệu, nhóm theo tài liệu, cascade xóa |
| `page_start`, `page_end` | Nguồn dẫn (hiển thị `tr.N`; dùng `page_start` làm số trang chính) |
| `text` | Ngữ cảnh đưa vào prompt và snippet khi xem nguồn |
| `ordinal` | Khôi phục thứ tự đọc; ghép chunk liền kề (nếu cần) |
| `embedding_model` | Phát hiện vector khác mô hình; lập kế hoạch re-embed |

> Không lưu embedding của **câu hỏi** (PRD 5.2: không lưu nội dung câu hỏi ngoài hội thoại; embedding có thể bị đảo ngược một phần). Vector câu hỏi chỉ tồn tại trong bộ nhớ khi truy vấn.

---

## 4. Chiến lược embedding và chỉ mục

### 4.1 Chia đoạn (chunking) — quyết định chất lượng trích dẫn
| Tham số | Giá trị [Đề xuất] | Lý do |
|---|---|---|
| Kích thước chunk | ~800 token | Đủ ngữ cảnh cho điều khoản/đoạn văn; không quá dài làm loãng điểm số |
| Chồng lấn | 100 token | Tránh cắt đôi câu/điều khoản ở ranh giới |
| Ranh giới | Ưu tiên theo đoạn/câu; không cắt giữa câu | Chất lượng ngữ nghĩa |
| Theo trang | Mỗi chunk lưu `page_start`, `page_end`; chunk không vượt quá 2 trang (cấu hình `chunk_max_page_span`, mặc định **1**: trích dẫn chỉ ghi một số trang nên chunk vắt qua 2 trang sẽ trích sai trang) | Nguồn dẫn kiểm chứng được (US-301) |
| Làm sạch | Bỏ header/footer lặp lại, chuẩn hóa khoảng trắng, giữ dấu tiếng Việt (NFC) | Giảm nhiễu |
| Chunk quá ngắn | Bỏ chunk < 5 token (nhãn trang lạc, dòng đơn lẻ). Ngưỡng 20 ban đầu làm mất trang chỉ có một câu ngắn — xem docs/implement/reports/retrieval_tuning.md | Tránh khớp rác nhưng không mất nội dung thật |
| Bảng/biểu | Trích văn bản thô; chất lượng bảng phức tạp là hạn chế đã biết | `OQ-008` |

### 4.2 Sinh embedding
- Gọi `EmbeddingPort.embed()` theo **lô** (ví dụ 64 chunk/lần), retry có backoff, timeout; lỗi một lô ⇒ công việc ingest thất bại có thể chạy lại (xóa chunk cũ của tài liệu rồi ghi lại — idempotent).
- Chuẩn hóa L2 ở worker nếu mô hình chưa chuẩn hóa.
- Với câu hỏi: dùng cùng mô hình; nếu mô hình phân biệt tiền tố “query/passage” thì áp dụng đúng.
- Ghi `embedding_model` cho mọi chunk. Truy xuất chỉ so sánh vector có cùng `embedding_model` (kiểm tra ở `VectorStorePort`).

### 4.3 Chỉ mục — hai chế độ, chọn theo quy mô thực đo

**Quan sát then chốt:** mọi truy vấn đều lọc theo `user_id` (≈ 1/50 tập) và thường theo ≤ 10 tài liệu — tập ứng viên chỉ khoảng **vài nghìn vector**. Với tập này, quét **chính xác** (exact) bằng chỉ mục B-tree `(user_id, document_id)` + sắp xếp theo khoảng cách cho recall 100% và nhanh (vài ms – chục ms). HNSW giúp khi phạm vi lọc lớn.

| Chế độ | Khi nào | Cấu hình |
|---|---|---|
| **A. Exact trong phạm vi lọc** (mặc định MVP) | Số chunk trong phạm vi lọc ≲ 20k | Dựa vào `idx_chunks_user_document`; planner tự chọn; không đặt `enable_indexscan` ép HNSW |
| **B. HNSW + lọc lặp** | Phạm vi lọc lớn (người dùng có rất nhiều tài liệu) hoặc tổng chunk lớn | Chỉ mục HNSW + `hnsw.iterative_scan` |

```sql
-- Chỉ mục HNSW (đã có trong SQL design 4.4)
CREATE INDEX idx_chunks_embedding_hnsw ON chunks
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Biến thể tiết kiệm bộ nhớ (~50% kích thước chỉ mục): lập chỉ mục trên halfvec, truy vấn ép kiểu tương ứng
-- CREATE INDEX idx_chunks_embedding_hnsw_half ON chunks
--   USING hnsw ((embedding::halfvec(1024)) halfvec_cosine_ops) WITH (m = 16, ef_construction = 64);
-- Truy vấn: ORDER BY (embedding::halfvec(1024)) <=> $1::halfvec(1024)
```

| Tham số | Giá trị khởi điểm | Tác động |
|---|---|---|
| `m` | 16 | Tăng ⇒ recall cao hơn, chỉ mục lớn hơn |
| `ef_construction` | 64 (tăng 128 nếu recall thấp) | Chất lượng đồ thị, thời gian dựng |
| `hnsw.ef_search` | 100 (mặc định 40) | Tăng ⇒ recall cao hơn, chậm hơn; đặt bằng `SET LOCAL` |
| `hnsw.iterative_scan` | `relaxed_order` | Tiếp tục quét khi lọc loại bớt kết quả ⇒ trả đủ k dòng sau lọc |
| `hnsw.max_scan_tuples` | 20000 | Giới hạn chi phí quét lặp |

**Ước lượng dung lượng (cận trên 750k vector, 1024 chiều):** bảng ≈ 750k × (4 KB vector + 3 KB text) ≈ 5,3 GB; chỉ mục HNSW float32 ≈ 3,5–4 GB; halfvec ≈ 1,8–2 GB. Với máy 8 GB RAM [Đề xuất SAD 3.6] nên dùng chế độ A hoặc halfvec; kiểm tra lại sau khi đo số vector thực tế.

**Quy trình chọn chế độ:** chạy bộ truy vấn đại diện bằng `EXPLAIN (ANALYZE, BUFFERS)` ở cả hai chế độ; chọn B chỉ khi chế độ A vượt 300ms p95 hoặc khi phạm vi lọc thường > 20k vector. Ghi kết quả vào `V006__vector_index_tuning.sql` (SQL design mục 11).

---

## 5. Truy vấn tương đồng

### 5.1 Truy vấn cơ bản (top-k có lọc)
```sql
BEGIN;
SET LOCAL app.user_id = :user_id;
SET LOCAL hnsw.ef_search = 100;
SET LOCAL hnsw.iterative_scan = relaxed_order;

SELECT c.id, c.document_id, d.name, c.page_start, c.page_end, c.text,
       1 - (c.embedding <=> :q) AS score
  FROM chunks c
  JOIN documents d ON d.id = c.document_id AND d.status = 'ready'
 WHERE c.user_id = :user_id
   AND (:doc_ids IS NULL OR c.document_id = ANY (:doc_ids))
 ORDER BY c.embedding <=> :q
 LIMIT :k;
COMMIT;
```
(Hàm đóng gói: `fn_search_chunks`, SQL design 8.2.)

### 5.2 Đa dạng theo tài liệu (US-203)
Một tệp dài không được chiếm toàn bộ top-k. Lấy tối đa `n` chunk tốt nhất **mỗi tài liệu**, rồi cắt top-k tổng:

```sql
WITH ranked AS (
  SELECT c.id, c.document_id, d.name, c.page_start, c.page_end, c.text,
         1 - (c.embedding <=> :q) AS score,
         row_number() OVER (PARTITION BY c.document_id ORDER BY c.embedding <=> :q) AS rn
    FROM chunks c
    JOIN documents d ON d.id = c.document_id AND d.status = 'ready'
   WHERE c.user_id = :user_id AND c.document_id = ANY (:doc_ids)
)
SELECT * FROM ranked
 WHERE rn <= :per_doc_cap            -- ví dụ 3
   AND score >= :min_score           -- ngưỡng “không tìm thấy” (ADR-04)
 ORDER BY score DESC
 LIMIT :k;                           -- ví dụ 8
```
Cửa sổ `row_number()` yêu cầu tính khoảng cách cho toàn bộ phạm vi lọc ⇒ chỉ dùng ở chế độ A (phạm vi nhỏ) hoặc sau bước ANN lấy dư (`LIMIT :k * 4`) ở chế độ B.

### 5.3 Ngưỡng liên quan và “không tìm thấy”
- Điểm `score = 1 − khoảng cách cosine` ∈ [−1, 1]. Nếu **không còn chunk nào ≥ `retrieval_min_score`** ⇒ trả lời “không tìm thấy trong tài liệu đã tải”, **không gọi LLM** (SAD ADR-04, US-202).
- Giá trị `0.30` trong seed chỉ là điểm xuất phát; ngưỡng phụ thuộc mô hình embedding và ngôn ngữ ⇒ **bắt buộc hiệu chỉnh** bằng bộ câu hỏi chuẩn gồm cả câu *có* và *không có* đáp án trong tài liệu (`OQ-009`), mục tiêu: ≥ 90% câu có đáp án vượt ngưỡng, ≥ 90% câu ngoài phạm vi bị loại [Đề xuất].

### 5.4 Dựng ngữ cảnh
- Đánh nhãn `[S1]…[Sn]` theo thứ tự điểm giảm dần; mỗi nhãn ánh xạ 1–1 tới `chunk_id` (nguồn của bảng `citations`).
- Tổng token ngữ cảnh ≤ ngân sách (ví dụ 6 000 token [Đề xuất]); cắt từ chunk điểm thấp nhất.
- Chunk liền kề cùng tài liệu có thể gộp khi `ordinal` liên tiếp (giữ nhãn của chunk có điểm cao nhất).

---

## 6. Cô lập, bảo mật và vòng đời dữ liệu vector

| Chủ đề | Thiết kế |
|---|---|
| Cô lập | Lọc `user_id` trong mọi truy vấn + RLS `FORCE` trên `chunks` (SQL design mục 5); kiểm thử US-402 bao gồm truy vấn ANN |
| Quyền | `app_api` chỉ `SELECT` trên `chunks`; chỉ `app_worker` được `INSERT/DELETE` |
| Tính nhạy cảm | Embedding và `text` được coi là **dữ liệu nhạy cảm như PDF gốc** (có thể suy ra nội dung) — cùng mã hóa at-rest, cùng chính sách xóa |
| Xóa | `DELETE documents` ⇒ cascade `chunks` ⇒ `citations.chunk_id` về `NULL`. Vector biến mất khỏi chỉ mục HNSW sau khi VACUUM; thời hạn xóa vật lý kể cả sao lưu `[TBD: OQ-012]` |
| Dịch vụ embedding ngoài | Văn bản chunk được gửi tới nhà cung cấp ⇒ cần hợp đồng không-huấn-luyện/không-lưu và vị trí xử lý đã duyệt trước khi dùng dữ liệu thật (PRD 5.1) |
| Log | Không ghi vector, `text` hay câu hỏi vào log truy vấn |
| Kiểm toán | Tải/xóa tài liệu ghi `audit_log` (không chứa nội dung) |

---

## 7. Hiệu năng và mở rộng

| Chỉ tiêu [Đề xuất] | Mục tiêu | Cách đạt / đo |
|---|---|---|
| Độ trễ truy xuất | p95 ≤ 300ms (k=8, ≤ 10 tài liệu) | Chế độ A/B; đo bằng `EXPLAIN ANALYZE` + metric ứng dụng |
| Embedding câu hỏi | p95 ≤ 500ms | Gọi trong cùng vùng mạng; timeout 3s |
| Thông lượng ghi | 1 tài liệu 100 trang ≤ 60s (PRD 5.1) | Embed theo lô song song 2–4, `INSERT` nhiều dòng (`COPY`/`executemany`) |
| Recall | ≥ 0.95 so với quét chính xác (chế độ B) | So sánh top-k ANN vs exact trên mẫu truy vấn |
| Dựng chỉ mục | Tạo/ tái tạo HNSW ngoài giờ | `CREATE INDEX CONCURRENTLY`; tăng `maintenance_work_mem` |

**Đường mở rộng:** (1) tăng RAM + `halfvec`; (2) replica đọc cho truy xuất; (3) phân vùng `chunks` theo `HASH(user_id)` để mỗi phân vùng có chỉ mục HNSW nhỏ; (4) chuyển sang vector DB chuyên dụng qua `VectorStorePort` (mục 2).

---

## 8. Vận hành và quan sát

| Metric | Nguồn | Cảnh báo [Đề xuất] |
|---|---|---|
| Độ trễ truy xuất vector (p50/p95) | Ứng dụng | p95 > 300ms trong 10 phút |
| Tỷ lệ `grounded=false` | `messages.grounded` / `answer_completed` | Tăng đột biến (>2× baseline) ⇒ nghi ngờ lỗi embedding/ngưỡng |
| Số chunk / kích thước chỉ mục | `pg_total_relation_size` | > 70% RAM khả dụng |
| Công việc ingest tồn đọng, thời gian xử lý | `ingest_jobs`, `document_ready.processing_ms` | Tồn đọng > 10 phút |
| Chunk khác `embedding_model` hiện hành | `SELECT embedding_model, count(*) FROM chunks GROUP BY 1` | Có chunk “cũ” sau khi đổi mô hình |

Bảo trì: `VACUUM (ANALYZE)` sau đợt xóa lớn; `REINDEX INDEX CONCURRENTLY idx_chunks_embedding_hnsw` khi phân mảnh/chất lượng giảm; `ANALYZE chunks` sau ingest lớn.

**Đổi mô hình embedding (re-embed):**
1. Thêm cột `embedding_v2 vector(N')` + `embedding_model_v2` (hoặc bảng `chunks_v2`).
2. Worker nền embed lại theo tài liệu, ghi vào cột mới; truy xuất song song so sánh trên bộ câu hỏi chuẩn.
3. Chuyển truy vấn sang cột mới (cờ cấu hình), dựng chỉ mục mới, bỏ cột cũ khi ổn định.
Không bao giờ trộn vector từ hai mô hình trong cùng một phép so sánh.

---

## 9. Mở rộng tương lai (ngoài MVP)

| Tính năng | Thiết kế dự kiến |
|---|---|
| Tìm kiếm lai (hybrid) từ khóa + vector | Thêm cột `tsv tsvector` (cấu hình `simple`, kèm `unaccent` tùy chọn cho tiếng Việt) + GIN; kết hợp thứ hạng bằng Reciprocal Rank Fusion (RRF). Hữu ích với mã/số hiệu/tên riêng mà embedding khớp kém |
| Reranking | Reranker nhỏ (cross-encoder) trên top 20 ⇒ top 8; cân nhắc độ trễ/chi phí |
| OCR cho PDF quét | Thêm bước ingest; không đổi lược đồ vector |
| Định dạng khác PDF | Thêm cột `source_type`; chunking theo cấu trúc |
| Chia sẻ tài liệu / workspace | Thay `user_id` bằng `owner_id` + bảng quyền; thiết kế lại RLS (hiện ngoài phạm vi, `OQ-007`) |

---

## 10. Kiểm thử và nghiệm thu

| Kiểm thử | Phương pháp | Tiêu chí |
|---|---|---|
| Cô lập ANN | Hai người dùng A/B; truy vấn của B bằng vector gần chunk của A | 0 kết quả của A (US-402) |
| Xóa | Xóa tài liệu rồi truy vấn | 0 chunk; citation `valid=false`; không còn dòng `chunks` của tài liệu |
| Chất lượng truy xuất | Bộ câu hỏi chuẩn (`OQ-009`): hit@k (đáp án nằm trong top-k) | ≥ 90% [Đề xuất]; ≥ 90% citation đúng vị trí trang (KR2.2) |
| Ngưỡng | Câu ngoài phạm vi | ≥ 90% bị loại → “không tìm thấy” [Đề xuất] |
| Hiệu năng | 750k vector tổng hợp, 50 truy vấn đồng thời | p95 ≤ 300ms |
| Recall ANN | So với exact | ≥ 0.95 |
| Idempotent ingest | Chạy lại công việc 2 lần | Không trùng chunk (`uq_chunks_doc_ordinal`) |
| Đa dạng | Hai PDF, câu hỏi cần cả hai | Kết quả có chunk từ cả hai tài liệu (US-203) |

---

## 11. Truy vết

| Story / quyết định | Phần tử thiết kế vector |
|---|---|
| US-201, US-203 | Mục 5.1–5.2 (top-k, đa dạng theo tài liệu) |
| US-202 | Mục 5.3 (ngưỡng), SAD ADR-04 |
| US-301, US-302 | `page_start/page_end`, `text`, nhãn `[Sx]` ⇒ `citations` (5.4) |
| US-103, RSK-002 | `ON DELETE CASCADE`, mục 6 |
| US-402 | `user_id` + RLS, mục 6 & 10 |
| PRD 5.1 hiệu năng | Mục 4.3, 7 |
| KR2.2 trích dẫn đúng | Mục 4.1 (chunk theo trang), 10 |

## 12. Rủi ro và câu hỏi mở
| ID | Nội dung | Tác động | Liên kết |
|---|---|---|---|
| R-VEC-01 | Mô hình embedding, chiều vector, vị trí xử lý chưa chọn/duyệt | Kích thước cột/chỉ mục, nhà cung cấp, re-embed | OQ-008, OQ-012, OQ-013 |
| R-VEC-02 | Ngưỡng liên quan & k chưa hiệu chỉnh | Tỷ lệ “không tìm thấy” sai / bịa đặt | OQ-009 |
| R-VEC-03 | Chất lượng với PDF bảng biểu / quét / nhiều cột | Chunk kém ⇒ trích dẫn kém | OQ-008 |
| R-VEC-04 | Quy mô thực tế chưa biết | Chọn chế độ A hay B, RAM | OQ-006, OQ-011 |
| R-VEC-05 | Lọc + HNSW có thể trả ít hơn k kết quả nếu không bật quét lặp | Thiếu ngữ cảnh | Cấu hình `iterative_scan` (4.3) |
