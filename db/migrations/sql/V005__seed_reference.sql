-- V005 — dữ liệu tham chiếu và cấu hình mặc định (mục 10)
-- Nguồn: docs/design/Database_Design_SQL.md. Biến mẫu (hai dấu ngoặc nhọn) được thay khi chạy (xem db/migrations/runner.py).
SET search_path = docchat, public;

INSERT INTO telemetry_event_types (name, allowed_props) VALUES
 ('session_started',            ARRAY['entry_source']),
 ('data_notice_accepted',       ARRAY['notice_version']),
 ('upload_started',             ARRAY['file_size','file_index']),
 ('upload_succeeded',           ARRAY['file_size','duration_ms']),
 ('upload_failed',              ARRAY['error_code','file_size']),
 ('document_ready',             ARRAY['page_count','processing_ms']),
 ('document_processing_failed', ARRAY['error_code']),
 ('document_deleted',           ARRAY['document_age_days']),
 ('question_submitted',         ARRAY['question_length','docs_selected_count']),
 ('answer_first_token',         ARRAY['latency_ms']),
 ('answer_completed',           ARRAY['total_ms','citation_count','grounded']),
 ('answer_failed',              ARRAY['error_code','stage']),
 ('answer_stopped',             ARRAY['elapsed_ms']),
 ('citation_opened',            ARRAY['citation_index']),
 ('answer_feedback',            ARRAY['rating','reason_code']),
 ('task_marked_done',           ARRAY['task_id','elapsed_ms','success']),
 ('copy_answer',                ARRAY['answer_id']);

-- Giá trị mặc định; con số thật phụ thuộc OQ-008/OQ-011/OQ-012
INSERT INTO app_config (key, value) VALUES
 ('qa_enabled',          'true'),
 ('max_file_size_bytes', '20971520'),      -- 20 MB   [TBD: OQ-008]
 ('max_files_per_user',  '50'),            --          [TBD: OQ-008]
 ('max_question_length', '2000'),          --          [TBD]
 ('accepted_types',      '["application/pdf"]'),
 ('retrieval_top_k',     '8'),
 ('retrieval_min_score', '0.30'),          -- hiệu chỉnh bằng bộ câu hỏi chuẩn [TBD: OQ-009]
 ('retention_days',      'null');          -- [TBD: OQ-012]

INSERT INTO data_notice_versions (version, content, is_current)
VALUES ('draft-0', 'Nội dung thông báo dữ liệu chờ phê duyệt của pháp chế/bảo mật [TBD: OQ-012, OQ-013].', true);
