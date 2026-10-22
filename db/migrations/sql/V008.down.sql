SET search_path = docchat, public;
DROP FUNCTION IF EXISTS fn_mvp_report(timestamptz, timestamptz);
DELETE FROM app_config WHERE key IN ('metrics_targets_approved', 'met001_baseline_ms',
  'met001_target_reduction_pct', 'met002_target_pct', 'first_token_target_ms', 'citation_target_pct');
