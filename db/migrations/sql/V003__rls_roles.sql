-- V003 — vai trò, quyền, Row-Level Security (mục 5)
-- Nguồn: docs/design/Database_Design_SQL.md. Biến mẫu (hai dấu ngoặc nhọn) được thay khi chạy (xem db/migrations/runner.py).
SET search_path = docchat, public;

DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_api') THEN CREATE ROLE app_api NOLOGIN; END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_worker') THEN CREATE ROLE app_worker NOLOGIN; END IF; END $$;
DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_report') THEN CREATE ROLE app_report NOLOGIN; END IF; END $$;
-- migrator là chủ sở hữu bảng, chỉ dùng khi chạy migration

GRANT USAGE ON SCHEMA docchat TO app_api, app_worker, app_report;

-- Quyền theo bảng (tối thiểu cần thiết)
GRANT SELECT, INSERT, UPDATE ON users                        TO app_api;
GRANT SELECT                  ON data_notice_versions        TO app_api;
GRANT SELECT, INSERT          ON data_notice_acceptances     TO app_api;
GRANT SELECT                  ON app_config                  TO app_api, app_worker;
GRANT UPDATE                  ON app_config                  TO app_api;           -- kill switch: chỉ vai trò ops ở tầng ứng dụng
GRANT SELECT, INSERT, DELETE  ON documents                   TO app_api;
GRANT SELECT, UPDATE          ON documents                   TO app_worker;
GRANT SELECT, INSERT          ON ingest_jobs                 TO app_api;
GRANT SELECT, UPDATE          ON ingest_jobs                 TO app_worker;
GRANT SELECT, INSERT, DELETE  ON idempotency_keys            TO app_api;
GRANT SELECT                  ON chunks                      TO app_api;
GRANT SELECT, INSERT, DELETE  ON chunks                      TO app_worker;
GRANT SELECT, INSERT, UPDATE  ON conversations, messages     TO app_api;
GRANT SELECT, INSERT          ON message_documents, citations TO app_api;
GRANT UPDATE (document_name)  ON citations                   TO app_api;           -- trigger xóa tài liệu xóa tên tệp khỏi citations
GRANT SELECT, INSERT, UPDATE  ON message_feedback            TO app_api;
GRANT INSERT                  ON telemetry_events            TO app_api;
GRANT SELECT                  ON telemetry_event_types       TO app_api;
GRANT INSERT                  ON audit_log                   TO app_api, app_worker;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA docchat       TO app_api, app_worker;

-- Bật RLS (kể cả với chủ sở hữu)
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['documents','chunks','conversations','messages','message_documents','citations','message_feedback','idempotency_keys']
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',  t);
    EXECUTE format('CREATE POLICY p_%1$s_owner ON %1$I TO app_api USING (user_id = fn_app_user_id()) WITH CHECK (user_id = fn_app_user_id())', t);
  END LOOP;
END $$;

-- Worker xử lý tài liệu của mọi người dùng, nhưng chỉ trên các bảng cần thiết
CREATE POLICY p_documents_worker ON documents TO app_worker USING (true) WITH CHECK (true);
CREATE POLICY p_chunks_worker    ON chunks    TO app_worker USING (true) WITH CHECK (true);
-- ingest_jobs, telemetry_events, audit_log không có RLS: không cấp quyền cho vai trò không liên quan
