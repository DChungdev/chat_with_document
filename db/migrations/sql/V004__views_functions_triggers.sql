-- V004 — view, hàm, trigger (mục 8)
-- Nguồn: docs/design/Database_Design_SQL.md. Biến mẫu (hai dấu ngoặc nhọn) được thay khi chạy (xem db/migrations/runner.py).
SET search_path = docchat, public;

-- Danh sách tài liệu cho UI (RLS tự áp dụng khi truy vấn qua app_api)
CREATE VIEW vw_document_overview WITH (security_invoker = true) AS
SELECT d.id, d.user_id, d.name, d.size_bytes, d.uploaded_at, d.status, d.page_count, d.error_code
FROM documents d;

-- Tác vụ thử nghiệm để tính MET-001 / MET-002 (PRD 5.2: task_marked_done)
CREATE VIEW vw_met_tasks AS
SELECT props->>'task_id'                AS task_id,
       user_hash,
       (props->>'elapsed_ms')::bigint   AS elapsed_ms,
       (props->>'success')::boolean     AS success,
       ts
FROM telemetry_events
WHERE name = 'task_marked_done';

-- Báo cáo MVP: trung vị thời gian tác vụ thành công (MET-001) và tỷ lệ thành công (MET-002)
CREATE VIEW vw_mvp_metrics AS
SELECT count(*)                                                             AS tasks_total,
       count(*) FILTER (WHERE success)                                      AS tasks_success,
       round(100.0 * count(*) FILTER (WHERE success) / NULLIF(count(*), 0), 1) AS met002_success_pct,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY elapsed_ms) FILTER (WHERE success) AS met001_median_ms
FROM vw_met_tasks;

-- Phễu chính theo PRD 5.2
CREATE VIEW vw_funnel AS
SELECT name, count(DISTINCT session_id) AS sessions
FROM telemetry_events
WHERE name IN ('session_started','data_notice_accepted','upload_succeeded','document_ready','question_submitted','answer_completed','citation_opened')
GROUP BY name;

GRANT SELECT ON vw_met_tasks, vw_mvp_metrics, vw_funnel TO app_report;
GRANT SELECT ON vw_document_overview TO app_api;

-- Nhận một việc trong hàng đợi (worker); an toàn khi nhiều worker chạy song song
CREATE FUNCTION fn_claim_ingest_job(p_worker text) RETURNS SETOF ingest_jobs
LANGUAGE sql AS $$
  WITH c AS (
    SELECT id FROM ingest_jobs
    WHERE status = 'queued' AND run_after <= now()
    ORDER BY id
    FOR UPDATE SKIP LOCKED
    LIMIT 1
  )
  UPDATE ingest_jobs j
     SET status = 'running', locked_at = now(), locked_by = p_worker, attempts = j.attempts + 1
    FROM c
   WHERE j.id = c.id
  RETURNING j.*;
$$;

-- Tìm top-k chunk gần nhất trong phạm vi người dùng/tài liệu; loại kết quả dưới ngưỡng
-- SECURITY INVOKER: RLS của app_api vẫn áp dụng; p_user_id chỉ để lọc tường minh và dùng chỉ mục
CREATE FUNCTION fn_search_chunks(
    p_user_id   uuid,
    p_query     vector({{EMBEDDING_DIM}}),
    p_doc_ids   uuid[],
    p_k         integer DEFAULT 8,
    p_min_score double precision DEFAULT 0.0
) RETURNS TABLE (chunk_id uuid, document_id uuid, document_name text, page_start integer, page_end integer, text text, score double precision)
LANGUAGE sql STABLE AS $$
  SELECT * FROM (
    SELECT c.id, c.document_id, d.name, c.page_start, c.page_end, c.text,
           1 - (c.embedding <=> p_query) AS score
      FROM chunks c
      JOIN documents d ON d.id = c.document_id AND d.status = 'ready'
     WHERE c.user_id = p_user_id
       AND (p_doc_ids IS NULL OR c.document_id = ANY (p_doc_ids))
     ORDER BY c.embedding <=> p_query
     LIMIT p_k
  ) r
  WHERE r.score >= p_min_score;
$$;

-- Xóa tài liệu hết hạn theo chính sách lưu giữ [TBD: OQ-012]
CREATE FUNCTION fn_purge_expired_documents(p_retention interval) RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE n integer;
BEGIN
  WITH del AS (DELETE FROM documents WHERE uploaded_at < now() - p_retention RETURNING id)
  SELECT count(*) INTO n FROM del;      -- trigger trg_documents_delete_before tự ghi audit 'document_deleted'
  RETURN n;   -- API/worker xóa tiếp các PDF gốc tương ứng ở object storage
END $$;

CREATE FUNCTION fn_purge_idempotency_keys() RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE n integer;
BEGIN
  DELETE FROM idempotency_keys WHERE created_at < now() - interval '24 hours';
  GET DIAGNOSTICS n = ROW_COUNT;
  RETURN n;
END $$;

-- (1) Xóa tài liệu: xóa tên tệp khỏi citations (chunk_id/document_id tự về NULL nhờ FK) và ghi audit
CREATE FUNCTION fn_documents_delete_before() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  UPDATE citations SET document_name = NULL WHERE document_id = OLD.id;
  INSERT INTO audit_log (user_id, action, entity_id, metadata)
  VALUES (OLD.user_id, 'document_deleted', OLD.id, jsonb_build_object('size_bytes', OLD.size_bytes, 'status', OLD.status));
  RETURN OLD;
END $$;
CREATE TRIGGER trg_documents_delete_before BEFORE DELETE ON documents
    FOR EACH ROW EXECUTE FUNCTION fn_documents_delete_before();

-- (2) Ghi audit khi tải lên
CREATE FUNCTION fn_documents_insert_after() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO audit_log (user_id, action, entity_id, metadata)
  VALUES (NEW.user_id, 'document_uploaded', NEW.id, jsonb_build_object('size_bytes', NEW.size_bytes));
  RETURN NEW;
END $$;
CREATE TRIGGER trg_documents_insert_after AFTER INSERT ON documents
    FOR EACH ROW EXECUTE FUNCTION fn_documents_insert_after();

-- (3) Ghi audit khi xác nhận thông báo
CREATE FUNCTION fn_notice_accept_after() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO audit_log (user_id, action, metadata) VALUES (NEW.user_id, 'notice_accepted', jsonb_build_object('version', NEW.version));
  RETURN NEW;
END $$;
CREATE TRIGGER trg_notice_acceptances_insert_after AFTER INSERT ON data_notice_acceptances
    FOR EACH ROW EXECUTE FUNCTION fn_notice_accept_after();

-- (4) Audit chỉ thêm
CREATE FUNCTION fn_audit_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'audit_log is append-only'; END $$;
CREATE TRIGGER trg_audit_log_mutate_before BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION fn_audit_immutable();

-- (5) Cập nhật hoạt động hội thoại
CREATE FUNCTION fn_messages_insert_after() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  UPDATE conversations SET last_activity_at = now() WHERE id = NEW.conversation_id;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_messages_insert_after AFTER INSERT ON messages
    FOR EACH ROW EXECUTE FUNCTION fn_messages_insert_after();

-- (6) Kiểm tra allow-list thuộc tính telemetry (phòng thủ nhiều lớp; ứng dụng đã lọc trước)
CREATE FUNCTION fn_telemetry_props_check() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE allowed text[]; bad text;
BEGIN
  SELECT allowed_props INTO allowed FROM telemetry_event_types WHERE name = NEW.name;
  SELECT k INTO bad FROM jsonb_object_keys(NEW.props) AS k WHERE k <> ALL (allowed) LIMIT 1;
  IF bad IS NOT NULL THEN
    RAISE EXCEPTION 'telemetry property % not allowed for event %', bad, NEW.name USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_telemetry_events_insert_before BEFORE INSERT ON telemetry_events
    FOR EACH ROW EXECUTE FUNCTION fn_telemetry_props_check();
