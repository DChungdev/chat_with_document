SET search_path = docchat, public;
DELETE FROM app_config WHERE key IN ('retrieval_per_doc_cap', 'context_token_budget', 'llm_max_tokens');
