SET search_path = docchat, public;
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['documents','chunks','conversations','messages','message_documents','citations','message_feedback','idempotency_keys']
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS p_%1$s_owner ON %1$I', t);
    EXECUTE format('ALTER TABLE %I NO FORCE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', t);
  END LOOP;
END $$;
DROP POLICY IF EXISTS p_documents_worker ON documents;
DROP POLICY IF EXISTS p_chunks_worker ON chunks;
REVOKE ALL ON ALL TABLES IN SCHEMA docchat FROM app_api, app_worker, app_report;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA docchat FROM app_api, app_worker;
REVOKE USAGE ON SCHEMA docchat FROM app_api, app_worker, app_report;
