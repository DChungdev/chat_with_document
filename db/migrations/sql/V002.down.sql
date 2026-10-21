SET search_path = docchat, public;
DROP TABLE IF EXISTS audit_log, telemetry_events, telemetry_event_types, message_feedback, citations,
  message_documents, messages, conversations, chunks, idempotency_keys, ingest_jobs, documents,
  app_config, data_notice_acceptances, data_notice_versions, users CASCADE;
DROP TYPE IF EXISTS audit_action;
