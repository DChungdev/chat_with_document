# Checklist thực thi test case

Cập nhật: 2026-11-02 · URL http://127.0.0.1:8000 · Tổng 94 case: ✅ 35 PASS · ❌ 2 FAIL · ⬜ 57 chưa chạy

> `[x]` = đã chạy và PASS; `[ ]` = FAIL hoặc chưa chạy (xem cột Kết quả). Sinh lại bằng `node tests/tools/checklist.mjs` sau mỗi lần chạy.

## API

| ✔ | ID | Tên | Ưu tiên | Kết quả | Report |
|---|---|---|---|---|---|
| [x] | [API-001](cases/API-001.md) | GET /config trả giới hạn và cờ | P0 | ✅ PASS | [report](reports/API-001/report.md) |
| [x] | [API-002](cases/API-002.md) | GET /data-notice trả thông báo hiện hành | P0 | ✅ PASS | [report](reports/API-002/report.md) |
| [x] | [API-003](cases/API-003.md) | POST /data-notice/acceptances (idempotent) | P0 | ✅ PASS | [report](reports/API-003/report.md) |
| [x] | [API-004](cases/API-004.md) | POST /documents tải PDF hợp lệ → 202 | P0 | ✅ PASS | [report](reports/API-004/report.md) |
| [x] | [API-005](cases/API-005.md) | POST /documents idempotent theo Idempotency-Key | P0 | ✅ PASS | [report](reports/API-005/report.md) |
| [x] | [API-006](cases/API-006.md) | POST /documents từ chối tệp không phải PDF | P0 | ✅ PASS | [report](reports/API-006/report.md) |
| [x] | [API-007](cases/API-007.md) | POST /documents từ chối tệp quá kích thước | P0 | ✅ PASS | [report](reports/API-007/report.md) |
| [ ] | [API-008](cases/API-008.md) | POST /documents vượt số tệp tối đa | P0 | ❌ FAIL | [report](reports/API-008/report.md) |
| [x] | [API-009](cases/API-009.md) | POST /documents bị chặn khi chưa xác nhận thông báo | P0 | ✅ PASS | [report](reports/API-009/report.md) |
| [x] | [API-010](cases/API-010.md) | Rate limit tải lên → 429 + Retry-After | P1 | ✅ PASS | [report](reports/API-010/report.md) |
| [x] | [API-011](cases/API-011.md) | GET /documents: phân trang và trạng thái | P0 | ✅ PASS | [report](reports/API-011/report.md) |
| [x] | [API-012](cases/API-012.md) | GET /documents/{id}: tồn tại và không tồn tại | P0 | ✅ PASS | [report](reports/API-012/report.md) |
| [x] | [API-013](cases/API-013.md) | DELETE /documents/{id} | P0 | ✅ PASS | [report](reports/API-013/report.md) |
| [x] | [API-014](cases/API-014.md) | POST /conversations | P0 | ✅ PASS | [report](reports/API-014/report.md) |
| [x] | [API-015](cases/API-015.md) | SSE hỏi đáp: đủ chuỗi sự kiện | P0 | ✅ PASS | [report](reports/API-015/report.md) |
| [x] | [API-016](cases/API-016.md) | Hỏi đáp: lỗi kiểm tra trước khi mở stream | P0 | ✅ PASS | [report](reports/API-016/report.md) |
| [x] | [API-017](cases/API-017.md) | Hỏi đáp với documentIds của người khác → 404 | P0 | ✅ PASS | [report](reports/API-017/report.md) |
| [x] | [API-018](cases/API-018.md) | Kill switch: 503 QA_DISABLED | P0 | ✅ PASS | [report](reports/API-018/report.md) |
| [x] | [API-019](cases/API-019.md) | Câu hỏi ngoài tài liệu: grounded=false, không citation | P0 | ✅ PASS | [report](reports/API-019/report.md) |
| [x] | [API-020](cases/API-020.md) | Hỏi đáp idempotent theo clientMessageId | P0 | ✅ PASS | [report](reports/API-020/report.md) |
| [x] | [API-023](cases/API-023.md) | Hỏi đáp trên nhiều tài liệu | P0 | ✅ PASS | [report](reports/API-023/report.md) |
| [x] | [API-025](cases/API-025.md) | GET /citations/{id} | P0 | ✅ PASS | [report](reports/API-025/report.md) |
| [x] | [API-026](cases/API-026.md) | Citation sau khi xóa tài liệu → valid=false | P0 | ✅ PASS | [report](reports/API-026/report.md) |
| [x] | [API-027](cases/API-027.md) | Citation của người khác → 404 | P0 | ✅ PASS | [report](reports/API-027/report.md) |
| [x] | [API-028](cases/API-028.md) | POST /telemetry/events (allow-list) | P0 | ✅ PASS | [report](reports/API-028/report.md) |
| [x] | [API-029](cases/API-029.md) | Telemetry từ chối sự kiện/thuộc tính ngoài allow-list | P0 | ✅ PASS | [report](reports/API-029/report.md) |
| [x] | [API-030](cases/API-030.md) | GET /reports/mvp-metrics: phân quyền | P0 | ✅ PASS | [report](reports/API-030/report.md) |
| [x] | [API-031](cases/API-031.md) | PUT /admin/flags/qa-enabled: phân quyền | P0 | ✅ PASS | [report](reports/API-031/report.md) |
| [x] | [API-032](cases/API-032.md) | Health & metrics endpoints | P0 | ✅ PASS | [report](reports/API-032/report.md) |
| [x] | [API-033](cases/API-033.md) | Mô hình lỗi RFC 7807 thống nhất | P0 | ✅ PASS | [report](reports/API-033/report.md) |
| [x] | [API-034](cases/API-034.md) | X-Request-Id trên mọi phản hồi | P1 | ✅ PASS | [report](reports/API-034/report.md) |
| [x] | [API-035](cases/API-035.md) | CORS chỉ cho phép origin của SPA | P0 | ✅ PASS | [report](reports/API-035/report.md) |
| [x] | [API-036](cases/API-036.md) | POST /messages/{id}/stop (P1) | P1 | ✅ PASS | [report](reports/API-036/report.md) |
| [x] | [API-037](cases/API-037.md) | POST /messages/{id}/regenerate (P1) | P1 | ✅ PASS | [report](reports/API-037/report.md) |
| [x] | [API-038](cases/API-038.md) | PUT /messages/{id}/feedback (P1) | P1 | ✅ PASS | [report](reports/API-038/report.md) |
| [ ] | [API-039](cases/API-039.md) | GET /conversations/{id}/messages — lịch sử (P1) | P1 | ❌ FAIL | [report](reports/API-039/report.md) |

## E2E giao diện

| ✔ | ID | Tên | Ưu tiên | Kết quả | Report |
|---|---|---|---|---|---|
| [x] | [E2E-001](cases/E2E-001.md) | Hành trình chính của Lan | P0 | ✅ PASS | [report](reports/E2E-001/report.md) |
| [ ] | [E2E-002](cases/E2E-002.md) | Tải nhiều PDF, một số tệp lỗi | P0 | Chưa chạy |  |
| [ ] | [E2E-003](cases/E2E-003.md) | Hỏi khi một tệp chưa sẵn sàng | P0 | Chưa chạy |  |
| [ ] | [E2E-004](cases/E2E-004.md) | Trạng thái rỗng (chưa có tài liệu) | P0 | Chưa chạy |  |
| [ ] | [E2E-005](cases/E2E-005.md) | Câu hỏi ngoài phạm vi: “không tìm thấy” | P0 | Chưa chạy |  |
| [ ] | [E2E-006](cases/E2E-006.md) | Tổng hợp từ nhiều PDF | P0 | Chưa chạy |  |
| [ ] | [E2E-007](cases/E2E-007.md) | Gián đoạn mạng khi đang trả lời | P0 | Chưa chạy |  |
| [ ] | [E2E-008](cases/E2E-008.md) | Mất mạng khi tải lên | P0 | Chưa chạy |  |
| [ ] | [E2E-009](cases/E2E-009.md) | Phiên hết hạn: overlay và giữ bản nháp | P0 | Chưa chạy |  |
| [ ] | [E2E-010](cases/E2E-010.md) | Kill switch trên giao diện | P0 | Chưa chạy |  |
| [ ] | [E2E-011](cases/E2E-011.md) | Cô lập giữa hai người dùng trên UI | P0 | Chưa chạy |  |
| [ ] | [E2E-012](cases/E2E-012.md) | Nguồn dẫn tới tệp đã xóa | P0 | Chưa chạy |  |
| [ ] | [E2E-013](cases/E2E-013.md) | Báo cáo đánh giá MVP (SCR-09) | P0 | Chưa chạy |  |
| [ ] | [E2E-014](cases/E2E-014.md) | Dừng sinh và Hỏi lại (P1) | P1 | Chưa chạy |  |
| [ ] | [E2E-015](cases/E2E-015.md) | Cổng thông báo dữ liệu | P0 | Chưa chạy |  |
| [ ] | [E2E-016](cases/E2E-016.md) | Báo cáo: người dùng thường bị từ chối | P0 | Chưa chạy |  |

## Bảo mật

| ✔ | ID | Tên | Ưu tiên | Kết quả | Report |
|---|---|---|---|---|---|
| [ ] | [SEC-001](cases/SEC-001.md) | IDOR: mọi endpoint với id của người khác | P0 | Chưa chạy |  |
| [ ] | [SEC-003](cases/SEC-003.md) | Tìm kiếm vector không rò sang người dùng khác | P0 | Chưa chạy |  |
| [ ] | [SEC-004](cases/SEC-004.md) | Xác thực JWT: thiếu, sai, hết hạn, alg=none | P0 | Chưa chạy |  |
| [ ] | [SEC-005](cases/SEC-005.md) | Phân quyền vai trò | P0 | Chưa chạy |  |
| [ ] | [SEC-006](cases/SEC-006.md) | Prompt injection qua nội dung PDF | P0 | Chưa chạy |  |
| [ ] | [SEC-007](cases/SEC-007.md) | Prompt injection qua câu hỏi | P0 | Chưa chạy |  |
| [ ] | [SEC-008](cases/SEC-008.md) | Tệp độc hại / tên tệp nguy hiểm | P0 | Chưa chạy |  |
| [ ] | [SEC-009](cases/SEC-009.md) | XSS: nội dung hiển thị được escape | P0 | Chưa chạy |  |
| [ ] | [SEC-010](cases/SEC-010.md) | Không rò nội dung vào log máy chủ | P0 | Chưa chạy |  |
| [ ] | [SEC-011](cases/SEC-011.md) | Telemetry chỉ chứa siêu dữ liệu | P0 | Chưa chạy |  |
| [ ] | [SEC-012](cases/SEC-012.md) | Không có nội dung trong URL / header | P0 | Chưa chạy |  |
| [ ] | [SEC-013](cases/SEC-013.md) | Rate limit hỏi đáp: 429 | P0 | Chưa chạy |  |
| [ ] | [SEC-014](cases/SEC-014.md) | Security headers | P0 | Chưa chạy |  |
| [ ] | [SEC-015](cases/SEC-015.md) | CORS và Origin lạ | P0 | Chưa chạy |  |
| [ ] | [SEC-016](cases/SEC-016.md) | Không lộ secret trong bundle và phản hồi | P0 | Chưa chạy |  |
| [ ] | [SEC-018](cases/SEC-018.md) | Xóa dữ liệu: không còn truy cập được | P0 | Chưa chạy |  |

## Khả năng tiếp cận

| ✔ | ID | Tên | Ưu tiên | Kết quả | Report |
|---|---|---|---|---|---|
| [ ] | [ACC-001](cases/ACC-001.md) | Điều hướng bàn phím toàn luồng P0 | P0 | Chưa chạy |  |
| [ ] | [ACC-002](cases/ACC-002.md) | Cây trợ năng cho trình đọc màn hình | P0 | Chưa chạy |  |
| [ ] | [ACC-003](cases/ACC-003.md) | Tương phản màu (sáng và tối) | P0 | Chưa chạy |  |
| [ ] | [ACC-004](cases/ACC-004.md) | Không chỉ dựa vào màu | P0 | Chưa chạy |  |
| [ ] | [ACC-005](cases/ACC-005.md) | Quản lý focus: hộp thoại và panel | P0 | Chưa chạy |  |
| [ ] | [ACC-006](cases/ACC-006.md) | Vùng live: streaming và lỗi | P1 | Chưa chạy |  |
| [ ] | [ACC-007](cases/ACC-007.md) | Thu phóng 200% / reflow | P1 | Chưa chạy |  |
| [ ] | [ACC-008](cases/ACC-008.md) | Quét axe-core toàn bộ màn hình | P0 | Chưa chạy |  |

## UI/UX

| ✔ | ID | Tên | Ưu tiên | Kết quả | Report |
|---|---|---|---|---|---|
| [ ] | [UI-001](cases/UI-001.md) | So khớp màn hình SCR-01…SCR-09 với prototype | P0 | Chưa chạy |  |
| [ ] | [UI-002](cases/UI-002.md) | Responsive 320–2560px | P0 | Chưa chạy |  |
| [ ] | [UI-003](cases/UI-003.md) | Trạng thái thành phần | P0 | Chưa chạy |  |
| [ ] | [UI-004](cases/UI-004.md) | Nhãn “do AI tạo” luôn hiển thị | P0 | Chưa chạy |  |
| [ ] | [UI-005](cases/UI-005.md) | Hành vi ô nhập và nút Gửi | P0 | Chưa chạy |  |
| [ ] | [UI-006](cases/UI-006.md) | Giao diện sáng/tối | P1 | Chưa chạy |  |
| [ ] | [UI-007](cases/UI-007.md) | Hiển thị streaming | P0 | Chưa chạy |  |
| [ ] | [UI-008](cases/UI-008.md) | Tương thích trình duyệt: Chromium, WebKit, Firefox | P0 | Chưa chạy |  |

## Chất lượng RAG

| ✔ | ID | Tên | Ưu tiên | Kết quả | Report |
|---|---|---|---|---|---|
| [ ] | [RAG-001](cases/RAG-001.md) | Câu hỏi có đáp án trong 1 tệp | P0 | Chưa chạy |  |
| [ ] | [RAG-002](cases/RAG-002.md) | Câu hỏi cần ≥ 2 tệp | P0 | Chưa chạy |  |
| [ ] | [RAG-003](cases/RAG-003.md) | Câu hỏi ngoài tài liệu | P0 | Chưa chạy |  |
| [ ] | [RAG-004](cases/RAG-004.md) | Tiếng Việt có dấu / không dấu | P1 | Chưa chạy |  |
| [ ] | [RAG-008](cases/RAG-008.md) | Trang trích dẫn so với trang thực của đoạn | P0 | Chưa chạy |  |

## Vận hành

| ✔ | ID | Tên | Ưu tiên | Kết quả | Report |
|---|---|---|---|---|---|
| [ ] | [OPS-001](cases/OPS-001.md) | Diễn tập kill switch | P0 | Chưa chạy |  |
| [ ] | [OPS-008](cases/OPS-008.md) | Phễu telemetry theo đúng thứ tự | P0 | Chưa chạy |  |

## Hiệu năng (chỉ báo)

| ✔ | ID | Tên | Ưu tiên | Kết quả | Report |
|---|---|---|---|---|---|
| [ ] | [PERF-001](cases/PERF-001.md) | Baseline: độ trễ token đầu, 1 người dùng | P1 | Chưa chạy |  |
| [ ] | [PERF-003](cases/PERF-003.md) | Thời gian xử lý (ingest) PDF | P1 | Chưa chạy |  |
| [ ] | [PERF-008](cases/PERF-008.md) | Thời gian tải trang đầu | P1 | Chưa chạy |  |
