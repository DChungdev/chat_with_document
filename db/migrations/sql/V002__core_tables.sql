-- V002 — bảng lõi (mục 4.2–4.6)
-- Nguồn: docs/design/Database_Design_SQL.md. Biến mẫu (hai dấu ngoặc nhọn) được thay khi chạy (xem db/migrations/runner.py).
SET search_path = docchat, public;

CREATE TABLE users (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    external_subject text        NOT NULL,                    -- `sub` của IdP [TBD: OQ-014]
    role             user_role   NOT NULL DEFAULT 'user',
    created_at       timestamptz NOT NULL DEFAULT now(),
    last_seen_at     timestamptz,
    CONSTRAINT uq_users_external_subject UNIQUE (external_subject)
);

CREATE TABLE data_notice_versions (
    version      text        PRIMARY KEY,                     -- ví dụ '2026-10-v1'
    content      text        NOT NULL,                        -- nội dung [TBD: OQ-012/013]
    published_at timestamptz NOT NULL DEFAULT now(),
    is_current   boolean     NOT NULL DEFAULT false
);
CREATE UNIQUE INDEX uq_data_notice_current ON data_notice_versions (is_current) WHERE is_current;

CREATE TABLE data_notice_acceptances (
    user_id    uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version    text        NOT NULL REFERENCES data_notice_versions(version),
    accepted_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, version)
);

CREATE TABLE app_config (
    key        text        PRIMARY KEY,
    value      jsonb       NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    updated_by uuid
);
CREATE TRIGGER trg_app_config_touch_before BEFORE UPDATE ON app_config
    FOR EACH ROW EXECUTE FUNCTION fn_touch_updated_at();

CREATE TABLE documents (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          uuid            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name             text            NOT NULL CHECK (char_length(name) BETWEEN 1 AND 255),
    size_bytes       bigint          NOT NULL CHECK (size_bytes > 0),
    page_count       integer         CHECK (page_count > 0),
    status           document_status NOT NULL DEFAULT 'processing',
    error_code       text,                                   -- PDF_PASSWORD | PDF_CORRUPT | NO_TEXT | ...
    storage_key      text            NOT NULL,               -- khóa trong object storage
    content_sha256   char(64),
    uploaded_at      timestamptz     NOT NULL DEFAULT now(),
    processed_at     timestamptz,
    CONSTRAINT uq_documents_storage_key UNIQUE (storage_key),
    CONSTRAINT ck_documents_error CHECK ((status = 'error') = (error_code IS NOT NULL)),
    CONSTRAINT ck_documents_ready CHECK (status <> 'ready' OR (page_count IS NOT NULL AND processed_at IS NOT NULL))
);
CREATE INDEX idx_documents_user_uploaded ON documents (user_id, uploaded_at DESC);
CREATE INDEX idx_documents_user_status   ON documents (user_id, status);

CREATE TABLE ingest_jobs (
    id            bigserial PRIMARY KEY,
    document_id   uuid        NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    status        job_status  NOT NULL DEFAULT 'queued',
    attempts      integer     NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    run_after     timestamptz NOT NULL DEFAULT now(),
    locked_at     timestamptz,
    locked_by     text,
    last_error    text,                                      -- chỉ mã lỗi, KHÔNG nội dung tài liệu
    trace_context jsonb,                                     -- carrier W3C traceparent để nối trace api → worker (A6)
    created_at    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_ingest_jobs_document UNIQUE (document_id)
);
CREATE INDEX idx_ingest_jobs_queue ON ingest_jobs (run_after, id) WHERE status = 'queued';

CREATE TABLE idempotency_keys (
    user_id     uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scope       text        NOT NULL,                        -- 'document_upload' | 'conversation_create' | 'message_create'
    key         uuid        NOT NULL,
    resource_id uuid        NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, scope, key)
);
CREATE INDEX idx_idempotency_created ON idempotency_keys (created_at);

-- Chiều vector (1024) là tham số theo mô hình embedding [TBD: OQ-008, OQ-012]; đổi mô hình ⇒ migration + re-embed.
CREATE TABLE chunks (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id uuid         NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id     uuid         NOT NULL REFERENCES users(id) ON DELETE CASCADE,   -- phi chuẩn hóa để lọc/RLS nhanh
    ordinal     integer      NOT NULL CHECK (ordinal >= 0),
    page_start  integer      NOT NULL CHECK (page_start >= 1),
    page_end    integer      NOT NULL,
    text        text         NOT NULL CHECK (char_length(text) > 0),
    token_count integer      NOT NULL CHECK (token_count > 0),
    embedding   vector({{EMBEDDING_DIM}}) NOT NULL,
    embedding_model text     NOT NULL,                      -- tên + phiên bản mô hình đã tạo vector (phục vụ re-embed)
    created_at  timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT uq_chunks_doc_ordinal UNIQUE (document_id, ordinal),
    CONSTRAINT ck_chunks_pages CHECK (page_end >= page_start)
);
CREATE INDEX idx_chunks_user_document ON chunks (user_id, document_id);
CREATE INDEX idx_chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = {{HNSW_M}}, ef_construction = {{HNSW_EF_CONSTRUCTION}});
-- Chi tiết điều chỉnh (ef_search, iterative scan, lọc theo user/document): xem Database_Design_VectorDB.md

CREATE TABLE conversations (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at       timestamptz NOT NULL DEFAULT now(),
    last_activity_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_conversations_user_activity ON conversations (user_id, last_activity_at DESC);

CREATE TABLE messages (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id   uuid           NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id           uuid           NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role              message_role   NOT NULL,
    text              text           NOT NULL DEFAULT '',
    status            message_status NOT NULL,
    grounded          boolean,                                   -- chỉ có nghĩa với role='ai'
    parent_message_id uuid           REFERENCES messages(id) ON DELETE SET NULL,  -- câu hỏi mà câu trả lời này đáp
    client_message_id uuid,
    error_code        text,
    created_at        timestamptz    NOT NULL DEFAULT now(),
    completed_at      timestamptz,
    CONSTRAINT uq_messages_client UNIQUE (conversation_id, client_message_id),
    CONSTRAINT ck_messages_grounded CHECK (role = 'ai' OR grounded IS NULL),
    CONSTRAINT ck_messages_text_len CHECK (char_length(text) <= 20000)
);
CREATE INDEX idx_messages_conversation_created ON messages (conversation_id, created_at);
CREATE INDEX idx_messages_user ON messages (user_id);

CREATE TABLE message_documents (                                  -- tài liệu được chọn cho câu hỏi (selected_for)
    message_id  uuid NOT NULL REFERENCES messages(id)  ON DELETE CASCADE,
    document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id     uuid NOT NULL REFERENCES users(id)     ON DELETE CASCADE,
    PRIMARY KEY (message_id, document_id)
);
CREATE INDEX idx_message_documents_document ON message_documents (document_id);

CREATE TABLE citations (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id    uuid    NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id       uuid    NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
    ordinal       integer NOT NULL CHECK (ordinal >= 1),        -- nhãn [S1], [S2]…
    document_id   uuid    REFERENCES documents(id) ON DELETE SET NULL,
    chunk_id      uuid    REFERENCES chunks(id)    ON DELETE SET NULL,
    document_name text,                                          -- bản chụp để hiển thị; bị xóa (NULL) khi tài liệu bị xóa
    page          integer NOT NULL CHECK (page >= 1),
    valid         boolean GENERATED ALWAYS AS (chunk_id IS NOT NULL) STORED,
    CONSTRAINT uq_citations_message_ordinal UNIQUE (message_id, ordinal)
);
CREATE INDEX idx_citations_message  ON citations (message_id);
CREATE INDEX idx_citations_document ON citations (document_id) WHERE document_id IS NOT NULL;
CREATE INDEX idx_citations_chunk    ON citations (chunk_id)    WHERE chunk_id    IS NOT NULL;

CREATE TABLE message_feedback (
    message_id  uuid PRIMARY KEY REFERENCES messages(id) ON DELETE CASCADE,
    user_id     uuid            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating      feedback_rating NOT NULL,
    reason_code text,
    created_at  timestamptz     NOT NULL DEFAULT now()
);

CREATE TABLE telemetry_event_types (                              -- allow-list (PRD 5.2, Blueprint 3.6)
    name          text PRIMARY KEY,
    allowed_props text[] NOT NULL                                  -- thuộc tính được phép
);

CREATE TABLE telemetry_events (
    id          bigserial PRIMARY KEY,
    ts          timestamptz NOT NULL,
    received_at timestamptz NOT NULL DEFAULT now(),
    name        text        NOT NULL REFERENCES telemetry_event_types(name),
    user_hash   char(64)    NOT NULL,                              -- băm một chiều có muối, không phải user_id
    session_id  uuid        NOT NULL,
    app_version text        NOT NULL,
    props       jsonb       NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT ck_telemetry_props_size CHECK (pg_column_size(props) <= 2048)
);
CREATE INDEX idx_telemetry_name_ts ON telemetry_events (name, ts);
CREATE INDEX idx_telemetry_session ON telemetry_events (session_id, ts);

CREATE TYPE audit_action AS ENUM ('notice_accepted', 'document_uploaded', 'document_deleted');

CREATE TABLE audit_log (
    id        bigserial PRIMARY KEY,
    ts        timestamptz  NOT NULL DEFAULT now(),
    user_id   uuid         NOT NULL,                               -- cố ý KHÔNG có FK: giữ vết sau khi người dùng bị xóa
    action    audit_action NOT NULL,
    entity_id uuid,
    metadata  jsonb        NOT NULL DEFAULT '{}'::jsonb            -- chỉ kích thước/thời điểm; KHÔNG tên tệp hay nội dung
);
CREATE INDEX idx_audit_user_ts ON audit_log (user_id, ts);
