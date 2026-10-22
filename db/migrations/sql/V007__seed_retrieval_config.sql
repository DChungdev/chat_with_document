-- V007 — cấu hình mặc định cho retrieval / trả lời (workstream D)
-- Chỉ thêm khóa còn thiếu. Ngưỡng liên quan `retrieval_min_score` và `retrieval_top_k` đã có ở V005;
-- giá trị chốt cho production phải hiệu chỉnh bằng bộ câu hỏi chuẩn thật [TBD: OQ-009].
SET search_path = docchat, public;

INSERT INTO app_config (key, value) VALUES
 ('retrieval_per_doc_cap', '3'),     -- tối đa chunk mỗi tài liệu trong top-k (US-203)
 ('context_token_budget',  '6000'),  -- ngân sách token ngữ cảnh đưa vào prompt
 ('llm_max_tokens',        '1500')   -- giới hạn độ dài câu trả lời
ON CONFLICT (key) DO NOTHING;
