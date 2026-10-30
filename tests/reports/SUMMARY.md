# Tổng hợp kết quả kiểm thử

Tạo lúc 2026-10-30T12:04:39.220Z · 37 test case đã chạy (PASS 35 · FAIL 2 · NOT RUN 0)

| ID | Tên | Kết quả | Bước | Ảnh | Video | Lỗi | Báo cáo |
|---|---|---|---|---|---|---|---|
| API-001 | GET /config trả giới hạn và cờ | ✅ PASS | 4 | 4 | ✔ | 0 | [report](API-001/report.md) |
| API-002 | GET /data-notice trả thông báo hiện hành | ✅ PASS | 2 | 2 | ✔ | 0 | [report](API-002/report.md) |
| API-003 | POST /data-notice/acceptances (idempotent) | ✅ PASS | 5 | 5 | ✔ | 0 | [report](API-003/report.md) |
| API-004 | POST /documents tải PDF hợp lệ → 202 | ✅ PASS | 3 | 3 | ✔ | 0 | [report](API-004/report.md) |
| API-005 | POST /documents idempotent theo Idempotency-Key | ✅ PASS | 5 | 5 | ✔ | 0 | [report](API-005/report.md) |
| API-006 | POST /documents từ chối tệp không phải PDF | ✅ PASS | 4 | 5 | ✔ | 0 | [report](API-006/report.md) |
| API-007 | POST /documents từ chối tệp quá kích thước | ✅ PASS | 3 | 3 | ✔ | 0 | [report](API-007/report.md) |
| API-008 | POST /documents vượt số tệp tối đa | ❌ FAIL | 3 | 2 | ✔ | 1 | [report](API-008/report.md) |
| API-009 | POST /documents bị chặn khi chưa xác nhận thông báo | ✅ PASS | 3 | 3 | ✔ | 0 | [report](API-009/report.md) |
| API-010 | Rate limit tải lên → 429 + Retry-After | ✅ PASS | 4 | 4 | ✔ | 0 | [report](API-010/report.md) |
| API-011 | GET /documents: phân trang và trạng thái | ✅ PASS | 5 | 7 | ✔ | 0 | [report](API-011/report.md) |
| API-012 | GET /documents/{id}: tồn tại và không tồn tại | ✅ PASS | 4 | 6 | ✔ | 0 | [report](API-012/report.md) |
| API-013 | DELETE /documents/{id} | ✅ PASS | 5 | 8 | ✔ | 0 | [report](API-013/report.md) |
| API-014 | POST /conversations | ✅ PASS | 4 | 4 | ✔ | 0 | [report](API-014/report.md) |
| API-015 | SSE hỏi đáp: đủ chuỗi sự kiện | ✅ PASS | 5 | 7 | ✔ | 0 | [report](API-015/report.md) |
| API-016 | Hỏi đáp: lỗi kiểm tra trước khi mở stream | ✅ PASS | 5 | 8 | ✔ | 0 | [report](API-016/report.md) |
| API-017 | Hỏi đáp với documentIds của người khác → 404 | ✅ PASS | 4 | 7 | ✔ | 0 | [report](API-017/report.md) |
| API-018 | Kill switch: 503 QA_DISABLED | ✅ PASS | 6 | 10 | ✔ | 0 | [report](API-018/report.md) |
| API-019 | Câu hỏi ngoài tài liệu: grounded=false, không citation | ✅ PASS | 3 | 5 | ✔ | 0 | [report](API-019/report.md) |
| API-020 | Hỏi đáp idempotent theo clientMessageId | ✅ PASS | 4 | 6 | ✔ | 0 | [report](API-020/report.md) |
| API-023 | Hỏi đáp trên nhiều tài liệu | ✅ PASS | 4 | 8 | ✔ | 0 | [report](API-023/report.md) |
| API-025 | GET /citations/{id} | ✅ PASS | 2 | 5 | ✔ | 0 | [report](API-025/report.md) |
| API-026 | Citation sau khi xóa tài liệu → valid=false | ✅ PASS | 3 | 6 | ✔ | 0 | [report](API-026/report.md) |
| API-027 | Citation của người khác → 404 | ✅ PASS | 3 | 6 | ✔ | 0 | [report](API-027/report.md) |
| API-028 | POST /telemetry/events (allow-list) | ✅ PASS | 3 | 3 | ✔ | 0 | [report](API-028/report.md) |
| API-029 | Telemetry từ chối sự kiện/thuộc tính ngoài allow-list | ✅ PASS | 4 | 4 | ✔ | 0 | [report](API-029/report.md) |
| API-030 | GET /reports/mvp-metrics: phân quyền | ✅ PASS | 3 | 3 | ✔ | 0 | [report](API-030/report.md) |
| API-031 | PUT /admin/flags/qa-enabled: phân quyền | ✅ PASS | 5 | 8 | ✔ | 0 | [report](API-031/report.md) |
| API-032 | Health & metrics endpoints | ✅ PASS | 4 | 5 | ✔ | 0 | [report](API-032/report.md) |
| API-033 | Mô hình lỗi RFC 7807 thống nhất | ✅ PASS | 4 | 10 | ✔ | 0 | [report](API-033/report.md) |
| API-034 | X-Request-Id trên mọi phản hồi | ✅ PASS | 3 | 12 | ✔ | 0 | [report](API-034/report.md) |
| API-035 | CORS chỉ cho phép origin của SPA | ✅ PASS | 3 | 3 | ✔ | 0 | [report](API-035/report.md) |
| API-036 | POST /messages/{id}/stop (P1) | ✅ PASS | 5 | 7 | ✔ | 0 | [report](API-036/report.md) |
| API-037 | POST /messages/{id}/regenerate (P1) | ✅ PASS | 4 | 6 | ✔ | 0 | [report](API-037/report.md) |
| API-038 | PUT /messages/{id}/feedback (P1) | ✅ PASS | 6 | 9 | ✔ | 0 | [report](API-038/report.md) |
| API-039 | GET /conversations/{id}/messages — lịch sử (P1) | ❌ FAIL | 2 | 6 | ✔ | 1 | [report](API-039/report.md) |
| E2E-001 | Hành trình chính của Lan | ✅ PASS | 6 | 6 | ✔ | 0 | [report](E2E-001/report.md) |
