-- CHỈ cho dev/staging với dữ liệu giả. KHÔNG chạy ở production.
SET search_path = docchat, public;

INSERT INTO users (id, external_subject, role) VALUES
 ('00000000-0000-0000-0000-0000000000a1', 'test|lan',  'user'),
 ('00000000-0000-0000-0000-0000000000b2', 'test|minh', 'evaluator'),
 ('00000000-0000-0000-0000-0000000000c3', 'test|ops',  'ops')
ON CONFLICT DO NOTHING;
