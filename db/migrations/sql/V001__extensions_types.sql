-- V001 — extension, schema, kiểu, hàm tiện ích (mục 4.1)
-- Nguồn: docs/design/Database_Design_SQL.md. Biến mẫu (hai dấu ngoặc nhọn) được thay khi chạy (xem db/migrations/runner.py).
CREATE EXTENSION IF NOT EXISTS vector;          -- pgvector (>= 0.7)
CREATE SCHEMA IF NOT EXISTS docchat;
SET search_path = docchat, public;

CREATE TYPE document_status AS ENUM ('processing', 'ready', 'error');   -- 'uploading'/'upload_failed' chỉ tồn tại ở client
CREATE TYPE message_role    AS ENUM ('user', 'ai');
CREATE TYPE message_status  AS ENUM ('sending', 'streaming', 'complete', 'interrupted', 'failed', 'stopped');
CREATE TYPE job_status      AS ENUM ('queued', 'running', 'done', 'failed');
CREATE TYPE feedback_rating AS ENUM ('up', 'down');
CREATE TYPE user_role       AS ENUM ('user', 'evaluator', 'ops');

-- ID người dùng của giao dịch hiện tại (API/worker đặt bằng SET LOCAL app.user_id = '<uuid>')
CREATE FUNCTION fn_app_user_id() RETURNS uuid
LANGUAGE sql STABLE AS $$ SELECT NULLIF(current_setting('app.user_id', true), '')::uuid $$;

CREATE FUNCTION fn_touch_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$ BEGIN NEW.updated_at := now(); RETURN NEW; END $$;
