# Bộ nhớ dự án — Chat với tài liệu

Tài liệu gốc: `docs/` (requirements → design → implement → testing). Tiếng Việt cho tài liệu và giao diện.

## Chạy và kiểm thử
- Chạy local không Docker: `make local` hoặc `.venv/Scripts/python.exe -m docchat_api.devserver --port 8000` (cần `ENVIRONMENT=dev`). Dùng **LLM/embedding giả**, dữ liệu trong bộ nhớ.
- Unit test: `make test`. Lint/kiến trúc: `make lint`.
- Test theo case: `tests/cases/<ID>.md` (1 file = 1 test case) → `node tests/reports/<ID>/run.mjs` → bằng chứng ở `tests/reports/<ID>/`. Hướng dẫn: `tests/README.md`; checklist: `node tests/tools/checklist.mjs`.
- URL kiểm thử: **http://127.0.0.1:8000**.

## Quy tắc bắt buộc
- Kết quả test **trung thực**: sản phẩm sai thì giữ FAIL + ghi lỗi; không sửa mã sản phẩm hay nới kỳ vọng để cho đạt; không kiểm chứng được thì ghi “chưa kiểm chứng”.
- Môi trường dev dùng adapter giả ⇒ kết quả hiệu năng/chất lượng RAG/prompt-injection chỉ là **chỉ báo**, không kết luận đạt mục tiêu thật.
- Không đưa nội dung tài liệu/câu hỏi/token/secret vào log, ảnh, report, repo.
- Mỗi case dùng tài khoản dev tên duy nhất. Kill switch (`qa-enabled`) là trạng thái toàn cục: bật lại trong `finally`, không chạy song song.
- `[Đề xuất]` / `[TBD: OQ-xxx]` trong tài liệu chưa phải quyết định — không coi là đã chốt.

## Phát hiện còn mở (cập nhật 2026-11-02)
- API-008: rate limit tải lên (20/giờ) chặn trước giới hạn 50 tệp ⇒ không kiểm chứng được `409 LIMIT_EXCEEDED`; cần PO quyết định.
- API-039: `GET /conversations/{id}/messages` trả 404 (P1, US-204 chưa làm).
- `health/ready` trả 503 ở devserver (không có CSDL) — bình thường ở môi trường này.
