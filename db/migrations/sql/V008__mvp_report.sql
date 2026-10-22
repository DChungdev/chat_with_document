-- V008 — báo cáo đánh giá MVP (US-501): hàm tổng hợp + cấu hình mục tiêu
-- fn_mvp_report là SECURITY DEFINER: API (vai trò app_api) KHÔNG đọc được bảng telemetry_events,
-- chỉ gọi được hàm trả về số liệu tổng hợp (không có nội dung, không có dòng riêng lẻ).
SET search_path = docchat, public;

CREATE FUNCTION fn_mvp_report(p_since timestamptz DEFAULT NULL, p_until timestamptz DEFAULT NULL)
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = docchat, public
AS $$
WITH ev AS (
  SELECT name, session_id, user_hash, props
    FROM telemetry_events
   WHERE (p_since IS NULL OR ts >= p_since) AND (p_until IS NULL OR ts < p_until)
), tasks AS (
  SELECT (props->>'elapsed_ms')::bigint AS elapsed, (props->>'success')::boolean AS success
    FROM ev
   WHERE name = 'task_marked_done' AND props ? 'elapsed_ms' AND props ? 'success'
), ft AS (
  SELECT (props->>'latency_ms')::numeric AS ms
    FROM ev WHERE name = 'answer_first_token' AND props ? 'latency_ms'
), ans AS (
  SELECT props FROM ev WHERE name = 'answer_completed'
), cnt AS (
  SELECT name, props->>'stage' AS stage, count(*) AS n FROM ev GROUP BY name, props->>'stage'
)
SELECT jsonb_build_object(
  'sessions',            (SELECT count(DISTINCT session_id) FROM ev),
  'users',               (SELECT count(DISTINCT user_hash) FROM ev),
  'tasksTotal',          (SELECT count(*) FROM tasks),
  'tasksSuccess',        (SELECT count(*) FROM tasks WHERE success),
  'met001MedianMs',      (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY elapsed) FROM tasks WHERE success),
  'firstTokenN',         (SELECT count(*) FROM ft),
  'firstTokenP95Ms',     (SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY ms) FROM ft),
  'answersCompleted',    (SELECT count(*) FROM ans),
  'answersWithCitation', (SELECT count(*) FROM ans
                           WHERE coalesce((props->>'grounded')::boolean, false)
                             AND coalesce((props->>'citation_count')::int, 0) >= 1),
  'errors', jsonb_build_object(
    'upload', jsonb_build_object(
      'failed', (SELECT coalesce(sum(n), 0) FROM cnt WHERE name = 'upload_failed'),
      'total',  (SELECT coalesce(sum(n), 0) FROM cnt WHERE name IN ('upload_succeeded', 'upload_failed'))),
    'processing', jsonb_build_object(
      'failed', (SELECT coalesce(sum(n), 0) FROM cnt WHERE name = 'document_processing_failed'),
      'total',  (SELECT coalesce(sum(n), 0) FROM cnt WHERE name IN ('document_ready', 'document_processing_failed'))),
    'generation', jsonb_build_object(
      'failed', (SELECT coalesce(sum(n), 0) FROM cnt WHERE name = 'answer_failed' AND stage = 'generation'),
      'total',  (SELECT coalesce(sum(n), 0) FROM cnt WHERE name IN ('answer_completed', 'answer_failed'))),
    'streaming', jsonb_build_object(
      'failed', (SELECT coalesce(sum(n), 0) FROM cnt WHERE name = 'answer_failed' AND stage = 'streaming'),
      'total',  (SELECT coalesce(sum(n), 0) FROM cnt WHERE name IN ('answer_completed', 'answer_failed')))
  ),
  'funnel', (SELECT coalesce(jsonb_object_agg(name, n), '{}'::jsonb)
               FROM (SELECT name, count(DISTINCT session_id) AS n FROM ev
                      WHERE name IN ('session_started', 'data_notice_accepted', 'upload_succeeded',
                                     'document_ready', 'question_submitted', 'answer_completed',
                                     'citation_opened')
                      GROUP BY name) f)
);
$$;

REVOKE ALL ON FUNCTION fn_mvp_report(timestamptz, timestamptz) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION fn_mvp_report(timestamptz, timestamptz) TO app_api, app_report;

-- Mục tiêu đề xuất; CHƯA duyệt ⇒ báo cáo luôn ghi "chưa thể kết luận" cho tới khi PO đặt
-- metrics_targets_approved = true và nhập met001_baseline_ms [TBD: OQ-005].
INSERT INTO app_config (key, value) VALUES
 ('metrics_targets_approved',    'false'),
 ('met001_baseline_ms',          'null'),
 ('met001_target_reduction_pct', '50'),
 ('met002_target_pct',           '80'),
 ('first_token_target_ms',       '5000'),
 ('citation_target_pct',         '90')
ON CONFLICT (key) DO NOTHING;
