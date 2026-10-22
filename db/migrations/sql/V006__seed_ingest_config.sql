-- V006 — cấu hình mặc định cho pipeline ingest (workstream C)
-- Chỉ thêm khóa còn thiếu (ON CONFLICT DO NOTHING) nên không ghi đè giá trị đã chỉnh tay.
SET search_path = docchat, public;

INSERT INTO app_config (key, value) VALUES
 ('max_pdf_pages',       '500'),   -- [TBD: OQ-008] giới hạn số trang mỗi PDF
 ('chunk_tokens',        '800'),   -- đổi chunking ⇒ phải ingest lại tài liệu đã có
 ('chunk_overlap_tokens','100'),
 ('chunk_min_tokens',    '5'),     -- 20 làm mất trang chỉ có một câu ngắn (đánh giá D7)
 ('chunk_max_page_span',  '1'),     -- 1 = chunk không vắt qua trang (trích dẫn đúng trang)
 ('embed_batch_size',    '64'),
 ('ingest_max_attempts', '3')
ON CONFLICT (key) DO NOTHING;
