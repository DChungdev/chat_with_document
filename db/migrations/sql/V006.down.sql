SET search_path = docchat, public;
DELETE FROM app_config
 WHERE key IN ('max_pdf_pages', 'chunk_tokens', 'chunk_overlap_tokens', 'chunk_min_tokens', 'chunk_max_page_span',
               'embed_batch_size', 'ingest_max_attempts');
