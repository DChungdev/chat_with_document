SET search_path = docchat, public;
DROP VIEW IF EXISTS vw_funnel, vw_mvp_metrics, vw_met_tasks, vw_document_overview;
DROP TRIGGER IF EXISTS trg_telemetry_events_insert_before ON telemetry_events;
DROP TRIGGER IF EXISTS trg_messages_insert_after ON messages;
DROP TRIGGER IF EXISTS trg_audit_log_mutate_before ON audit_log;
DROP TRIGGER IF EXISTS trg_notice_acceptances_insert_after ON data_notice_acceptances;
DROP TRIGGER IF EXISTS trg_documents_insert_after ON documents;
DROP TRIGGER IF EXISTS trg_documents_delete_before ON documents;
DROP FUNCTION IF EXISTS fn_telemetry_props_check(), fn_messages_insert_after(), fn_audit_immutable(),
  fn_notice_accept_after(), fn_documents_insert_after(), fn_documents_delete_before(),
  fn_purge_idempotency_keys(), fn_purge_expired_documents(interval), fn_claim_ingest_job(text);
DROP FUNCTION IF EXISTS fn_search_chunks(uuid, vector, uuid[], integer, double precision);
