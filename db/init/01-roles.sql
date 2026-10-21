-- Khởi tạo cụm/CSDL — chạy MỘT LẦN bởi superuser (docker-entrypoint-initdb.d hoặc fixture test).
-- Việc cần quyền superuser nằm ở đây để migration chạy được bằng vai trò `migrator` không đặc quyền.
--
-- !! Mật khẩu 'docchat_dev' CHỈ dành cho dev/test. Staging/production tạo vai trò đăng nhập bằng
-- !! secret manager (xem deploy/README.md), không dùng tệp này.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'migrator') THEN
    CREATE ROLE migrator LOGIN PASSWORD 'docchat_dev' CREATEROLE;
  END IF;
  -- Vai trò nhóm giữ quyền (V003 cấp quyền cho các vai trò này)
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_api') THEN
    CREATE ROLE app_api NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_worker') THEN
    CREATE ROLE app_worker NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_report') THEN
    CREATE ROLE app_report NOLOGIN;
  END IF;
  -- Vai trò đăng nhập của từng dịch vụ (thành viên của vai trò nhóm)
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'docchat_api') THEN
    CREATE ROLE docchat_api LOGIN PASSWORD 'docchat_dev' IN ROLE app_api;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'docchat_worker') THEN
    CREATE ROLE docchat_worker LOGIN PASSWORD 'docchat_dev' IN ROLE app_worker;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'docchat_report') THEN
    CREATE ROLE docchat_report LOGIN PASSWORD 'docchat_dev' IN ROLE app_report;
  END IF;
END
$$;

-- search_path theo vai trò: hàm fn_* và truy vấn không tiền tố schema cần `docchat`.
ALTER ROLE migrator       SET search_path = docchat, public;
ALTER ROLE docchat_api    SET search_path = docchat, public;
ALTER ROLE docchat_worker SET search_path = docchat, public;
ALTER ROLE docchat_report SET search_path = docchat, public;

-- migrator sở hữu CSDL (tạo schema, bảng) nhưng KHÔNG phải superuser nên RLS (FORCE) áp dụng với nó.
DO $$
BEGIN
  EXECUTE format('ALTER DATABASE %I OWNER TO migrator', current_database());
END
$$;

-- Cần superuser (hoặc extension "trusted"); đặt ở schema public để mọi vai trò dùng được kiểu `vector`.
CREATE EXTENSION IF NOT EXISTS vector;
