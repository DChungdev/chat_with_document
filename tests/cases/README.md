# Danh mục test case

Tách từ [Test_Plan.md](../../docs/testing/Test_Plan.md). Mỗi file = 1 test case; agent thực thi theo mục “Nhiệm vụ của agent” trong từng file. Môi trường: **http://127.0.0.1:8000**. Artifact: `tests/reports/<ID>/`. Hướng dẫn chung: [../README.md](../README.md).

Tổng cộng **94** test case.

## API (black-box) (36)

| ID | Tên | Ưu tiên | Truy vết |
|---|---|---|---|
| [API-001](API-001.md) | GET /config trả giới hạn và cờ | P0 | US-401, OQ-008 · API Design 3.3 IF-01 · Test Plan API-001 |
| [API-002](API-002.md) | GET /data-notice trả thông báo hiện hành | P0 | US-401 · IF-01 · API-002 |
| [API-003](API-003.md) | POST /data-notice/acceptances (idempotent) | P0 | US-401 · IF-02 · API-003 |
| [API-004](API-004.md) | POST /documents tải PDF hợp lệ → 202 | P0 | US-101 · IF-03 · API-004 |
| [API-005](API-005.md) | POST /documents idempotent theo Idempotency-Key | P0 | PRD 4.2, CN-05 · IF-03 · API-005 |
| [API-006](API-006.md) | POST /documents từ chối tệp không phải PDF | P0 | US-101 · IF-03 · API-006 |
| [API-007](API-007.md) | POST /documents từ chối tệp quá kích thước | P0 | US-101, OQ-008 · IF-03 · API-007 |
| [API-008](API-008.md) | POST /documents vượt số tệp tối đa | P0 | US-101, OQ-008 · IF-03 · API-008 |
| [API-009](API-009.md) | POST /documents bị chặn khi chưa xác nhận thông báo | P0 | US-401 · IF-03 · API-009 |
| [API-010](API-010.md) | Rate limit tải lên → 429 + Retry-After | P1 | API Design 2.3 · API-010 · SEC-013 |
| [API-011](API-011.md) | GET /documents: phân trang và trạng thái | P0 | US-102 · IF-04 · API-011 |
| [API-012](API-012.md) | GET /documents/{id}: tồn tại và không tồn tại | P0 | US-102, US-402 · IF-04 · API-012 |
| [API-013](API-013.md) | DELETE /documents/{id} | P0 | US-103 · IF-05 · API-013 |
| [API-014](API-014.md) | POST /conversations | P0 | US-201 · API-014 |
| [API-015](API-015.md) | SSE hỏi đáp: đủ chuỗi sự kiện | P0 | US-201, 203, 301 · IF-06 · API-015 |
| [API-016](API-016.md) | Hỏi đáp: lỗi kiểm tra trước khi mở stream | P0 | US-201 · IF-06 · API-016 |
| [API-017](API-017.md) | Hỏi đáp với documentIds của người khác → 404 | P0 | US-402 · SEC-001 · API-017 |
| [API-018](API-018.md) | Kill switch: 503 QA_DISABLED | P0 | PRD 5.1 · F-09 · API-018 |
| [API-019](API-019.md) | Câu hỏi ngoài tài liệu: grounded=false, không citation | P0 | US-202 · AC-003 · ADR-04 · API-019 |
| [API-020](API-020.md) | Hỏi đáp idempotent theo clientMessageId | P0 | CN-05 · IF-06 · API-020 |
| [API-023](API-023.md) | Hỏi đáp trên nhiều tài liệu | P0 | US-203 · API-023 |
| [API-025](API-025.md) | GET /citations/{id} | P0 | US-302 · IF-08 · API-025 |
| [API-026](API-026.md) | Citation sau khi xóa tài liệu → valid=false | P0 | US-302, PRD 4.2 · API-026 |
| [API-027](API-027.md) | Citation của người khác → 404 | P0 | US-402 · SEC-001 · API-027 |
| [API-028](API-028.md) | POST /telemetry/events (allow-list) | P0 | US-501 · IF-10 · API-028 |
| [API-029](API-029.md) | Telemetry từ chối sự kiện/thuộc tính ngoài allow-list | P0 | ADR-10, PRD 5.2 · API-029 · SEC-011 |
| [API-030](API-030.md) | GET /reports/mvp-metrics: phân quyền | P0 | US-501 · API-030 |
| [API-031](API-031.md) | PUT /admin/flags/qa-enabled: phân quyền | P0 | PRD 5.1 · API-031 |
| [API-032](API-032.md) | Health & metrics endpoints | P0 | PRD 5.1 · API-032 |
| [API-033](API-033.md) | Mô hình lỗi RFC 7807 thống nhất | P0 | API Design 3.4.6 · API-033 |
| [API-034](API-034.md) | X-Request-Id trên mọi phản hồi | P1 | API Design 2.3 · API-034 |
| [API-035](API-035.md) | CORS chỉ cho phép origin của SPA | P0 | API Design 2.4 · API-035 · SEC-015 |
| [API-036](API-036.md) | POST /messages/{id}/stop (P1) | P1 | US-205 · IF-07 · API-036 |
| [API-037](API-037.md) | POST /messages/{id}/regenerate (P1) | P1 | PRD 4.2, US-205 · API-037 |
| [API-038](API-038.md) | PUT /messages/{id}/feedback (P1) | P1 | US-502 · IF-09 · API-038 |
| [API-039](API-039.md) | GET /conversations/{id}/messages — lịch sử (P1) | P1 | US-204 · IF-06 · API-039 · OQ-012 |

## E2E giao diện (16)

| ID | Tên | Ưu tiên | Truy vết |
|---|---|---|---|
| [E2E-001](E2E-001.md) | Hành trình chính của Lan | P0 | US-101…103, 201, 301, 302, 401 · Test Plan E2E-001 |
| [E2E-002](E2E-002.md) | Tải nhiều PDF, một số tệp lỗi | P0 | US-101 AC-001 · E2E-002 |
| [E2E-003](E2E-003.md) | Hỏi khi một tệp chưa sẵn sàng | P0 | PRD 4.2 · E2E-003 |
| [E2E-004](E2E-004.md) | Trạng thái rỗng (chưa có tài liệu) | P0 | AC-002, PRD 4.2 · E2E-004 |
| [E2E-005](E2E-005.md) | Câu hỏi ngoài phạm vi: “không tìm thấy” | P0 | US-202 AC-003 · E2E-005 |
| [E2E-006](E2E-006.md) | Tổng hợp từ nhiều PDF | P0 | US-203 · E2E-006 |
| [E2E-007](E2E-007.md) | Gián đoạn mạng khi đang trả lời | P0 | PRD 4.2 · E2E-007 |
| [E2E-008](E2E-008.md) | Mất mạng khi tải lên | P0 | PRD 4.2 · E2E-008 |
| [E2E-009](E2E-009.md) | Phiên hết hạn: overlay và giữ bản nháp | P0 | US-402 AC2, PRD 4.2 · E2E-009 |
| [E2E-010](E2E-010.md) | Kill switch trên giao diện | P0 | PRD 5.1 · E2E-010 |
| [E2E-011](E2E-011.md) | Cô lập giữa hai người dùng trên UI | P0 | US-402 · E2E-011 · SEC-001 |
| [E2E-012](E2E-012.md) | Nguồn dẫn tới tệp đã xóa | P0 | PRD 4.2, US-302 · E2E-012 |
| [E2E-013](E2E-013.md) | Báo cáo đánh giá MVP (SCR-09) | P0 | US-501 AC-004 · E2E-013 |
| [E2E-014](E2E-014.md) | Dừng sinh và Hỏi lại (P1) | P1 | US-205 · E2E-014 |
| [E2E-015](E2E-015.md) | Cổng thông báo dữ liệu | P0 | US-401 · F-07 |
| [E2E-016](E2E-016.md) | Báo cáo: người dùng thường bị từ chối | P0 | US-501 · F-08 |

## Bảo mật (16)

| ID | Tên | Ưu tiên | Truy vết |
|---|---|---|---|
| [SEC-001](SEC-001.md) | IDOR: mọi endpoint với id của người khác | P0 | US-402 · SEC-001 · RISK-01 |
| [SEC-003](SEC-003.md) | Tìm kiếm vector không rò sang người dùng khác | P0 | US-402, ADR-07 · SEC-003 |
| [SEC-004](SEC-004.md) | Xác thực JWT: thiếu, sai, hết hạn, alg=none | P0 | PRD 5.1 · SEC-004 · API Design 2.4 |
| [SEC-005](SEC-005.md) | Phân quyền vai trò | P0 | SEC-005 · API-030/031 |
| [SEC-006](SEC-006.md) | Prompt injection qua nội dung PDF | P0 | RSK-I6, ADR-03 · SEC-006 |
| [SEC-007](SEC-007.md) | Prompt injection qua câu hỏi | P0 | SEC-007 |
| [SEC-008](SEC-008.md) | Tệp độc hại / tên tệp nguy hiểm | P0 | SEC-008 · RSK-I8 |
| [SEC-009](SEC-009.md) | XSS: nội dung hiển thị được escape | P0 | SEC-009 |
| [SEC-010](SEC-010.md) | Không rò nội dung vào log máy chủ | P0 | PRD 5.1, OBJ-005 · SEC-010 · RISK-01 |
| [SEC-011](SEC-011.md) | Telemetry chỉ chứa siêu dữ liệu | P0 | ADR-10 · SEC-011 · API-029 |
| [SEC-012](SEC-012.md) | Không có nội dung trong URL / header | P0 | API Design 1.3 · SEC-012 |
| [SEC-013](SEC-013.md) | Rate limit hỏi đáp: 429 | P0 | API Design 2.3 · SEC-013 |
| [SEC-014](SEC-014.md) | Security headers | P0 | PRD 5.1 · SEC-014 |
| [SEC-015](SEC-015.md) | CORS và Origin lạ | P0 | SEC-014 · API-035 |
| [SEC-016](SEC-016.md) | Không lộ secret trong bundle và phản hồi | P0 | PRD 5.1 · SEC-016 |
| [SEC-018](SEC-018.md) | Xóa dữ liệu: không còn truy cập được | P0 | US-103, PRD 5.1 · SEC-018 |

## Khả năng tiếp cận (8)

| ID | Tên | Ưu tiên | Truy vết |
|---|---|---|---|
| [ACC-001](ACC-001.md) | Điều hướng bàn phím toàn luồng P0 | P0 | PRD 4.1(6), OBJ-008 · ACC-001 |
| [ACC-002](ACC-002.md) | Cây trợ năng cho trình đọc màn hình | P0 | ACC-002 |
| [ACC-003](ACC-003.md) | Tương phản màu (sáng và tối) | P0 | ACC-003 |
| [ACC-004](ACC-004.md) | Không chỉ dựa vào màu | P0 | PRD 4.1, UIUX Blueprint · ACC-004 |
| [ACC-005](ACC-005.md) | Quản lý focus: hộp thoại và panel | P0 | ACC-005 |
| [ACC-006](ACC-006.md) | Vùng live: streaming và lỗi | P1 | ACC-006 |
| [ACC-007](ACC-007.md) | Thu phóng 200% / reflow | P1 | ACC-007 · WCAG 1.4.4/1.4.10 |
| [ACC-008](ACC-008.md) | Quét axe-core toàn bộ màn hình | P0 | OBJ-008 · PRD 5.1 |

## UI/UX (8)

| ID | Tên | Ưu tiên | Truy vết |
|---|---|---|---|
| [UI-001](UI-001.md) | So khớp màn hình SCR-01…SCR-09 với prototype | P0 | OBJ-007 · UIUX Blueprint · UI-001 |
| [UI-002](UI-002.md) | Responsive 320–2560px | P0 | UI-002 · UIUX Blueprint |
| [UI-003](UI-003.md) | Trạng thái thành phần | P0 | UI-003 |
| [UI-004](UI-004.md) | Nhãn “do AI tạo” luôn hiển thị | P0 | BRU-002, PRD 4.1(4) · UI-004 |
| [UI-005](UI-005.md) | Hành vi ô nhập và nút Gửi | P0 | PRD 4.1, 4.2 · UI-005 |
| [UI-006](UI-006.md) | Giao diện sáng/tối | P1 | UI-006 |
| [UI-007](UI-007.md) | Hiển thị streaming | P0 | UI-007 · CN-02 |
| [UI-008](UI-008.md) | Tương thích trình duyệt: Chromium, WebKit, Firefox | P0 | PRD 5.1 (QA) · UI-008 |

## Chất lượng RAG (5)

| ID | Tên | Ưu tiên | Truy vết |
|---|---|---|---|
| [RAG-001](RAG-001.md) | Câu hỏi có đáp án trong 1 tệp | P0 | US-202, OBJ-003 · RAG-001 |
| [RAG-002](RAG-002.md) | Câu hỏi cần ≥ 2 tệp | P0 | US-203 · RAG-002 |
| [RAG-003](RAG-003.md) | Câu hỏi ngoài tài liệu | P0 | US-202 AC-003 · RAG-003 |
| [RAG-004](RAG-004.md) | Tiếng Việt có dấu / không dấu | P1 | OQ-008 · RAG-004 |
| [RAG-008](RAG-008.md) | Trang trích dẫn so với trang thực của đoạn | P0 | RSK-I3, OBJ-003 · RAG-008 |

## Vận hành (2)

| ID | Tên | Ưu tiên | Truy vết |
|---|---|---|---|
| [OPS-001](OPS-001.md) | Diễn tập kill switch | P0 | PRD 5.1, OBJ-009 · OPS-001 |
| [OPS-008](OPS-008.md) | Phễu telemetry theo đúng thứ tự | P0 | PRD 5.2, OBJ-010 · OPS-008 |

## Hiệu năng (chỉ báo) (3)

| ID | Tên | Ưu tiên | Truy vết |
|---|---|---|---|
| [PERF-001](PERF-001.md) | Baseline: độ trễ token đầu, 1 người dùng | P1 | OBJ-006, PRD 5.1 · PERF-001 |
| [PERF-003](PERF-003.md) | Thời gian xử lý (ingest) PDF | P1 | OBJ-006, PRD 5.1 · PERF-003 |
| [PERF-008](PERF-008.md) | Thời gian tải trang đầu | P1 | PRD 5.1, OBJ-006 · PERF-008 |

## Không đưa vào bộ test case này (và lý do)

| Mã trong Test Plan | Lý do |
|---|---|
| UT-001…012 (unit), INT-001…010 (tích hợp) | Test mức mã nguồn; chạy bằng `pytest`/`vitest` trong repo (và CI với Postgres+MinIO thật), không phải kiểm thử qua URL |
| API-021, API-022, API-024 | Cần chèn lỗi/đầu ra vào LLM hoặc ngắt kết nối từ phía server, devserver không cho phép; phần hành vi phía UI được phủ bởi E2E-007; logic lọc nhãn bởi UT-005 |
| SEC-002 (RLS), SEC-015 (TLS), SEC-017 (SCA), SEC-019 (red-team Claude thật) | Cần PostgreSQL/hạ tầng/LLM thật hoặc công cụ ngoài; devserver dùng bộ nhớ |
| RAG-005, RAG-006, RAG-007 | Cần PDF bố cục phức tạp/mơ hồ/mâu thuẫn và LLM thật mới có ý nghĩa |
| PERF-002, 004, 005, 006, 007, 009 | Cần staging (k6, LLM/embedding thật, pgvector HNSW, nginx/WAF) |
| OPS-002…007, OPS-009 | Cần fault injection, nhiều worker/bản sao API, hệ thống giám sát |
| UAT-001…010 | Chấp nhận do con người ký duyệt (Lan, Minh, Hà); phần tự động hóa được đã nằm ở E2E |
| UI-001 (so sánh Figma) | Không có Figma; dùng prototype HTML (đã có ở UI-001) |

Mọi hạng mục trên vẫn là phạm vi của Test Plan; chúng chưa có file case vì không thực thi được qua http://127.0.0.1:8000 với devserver.
