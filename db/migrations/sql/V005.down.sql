SET search_path = docchat, public;
DELETE FROM data_notice_versions WHERE version = 'draft-0';
DELETE FROM app_config;
DELETE FROM telemetry_event_types;
