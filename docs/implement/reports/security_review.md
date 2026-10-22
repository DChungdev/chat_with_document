# Báo cáo rà soát bảo mật (G8)

Ngày: 2026-10-23 · Phạm vi: mã trong repo (API, worker, core, infra, web, deploy). Phương pháp: đọc mã + test tự động
(`apps/api/tests/test_security.py`, `test_isolation.py`, `test_no_content_leak.py`) + SCA. **Chưa có pentest ngoài,
chưa red-team với Claude thật, chưa kiểm trên hạ tầng container/k8s** (máy này không có Docker/Postgres).

## Tóm tắt

| Mức | Số lượng | Ghi chú |
|---|---|---|
| Nghiêm trọng / Cao chưa xử lý | 0 phát hiện trong phạm vi đã kiểm | Xem mục "Chưa kiểm chứng" — không đồng nghĩa là không có |
| Trung bình đã sửa trong lần rà soát này | 3 | Thiếu security headers/CSP; nginx không kế thừa `add_header`; devserver lỗi mã hóa console |
| Rủi ro chấp nhận / còn mở | 5 | Bảng cuối |

## Kết quả theo hạng mục

### 1. Prompt injection qua nội dung PDF
- **Biện pháp có kiểm chứng (test):** nội dung chunk, tên tệp và câu hỏi được escape (`& < >`) nên không thể đóng thẻ `<nguon>`/`<cau_hoi>` hay chèn thẻ giả (`test_answering.py`, `test_security.py::test_injected_document_cannot_forge_citations_or_break_out`, `::test_question_cannot_inject_tags`).
- Trích dẫn **chỉ** được dựng từ ID chunk đã truy xuất; nhãn `[Sx]` không thuộc tập nguồn bị `LabelFilter` bóc trước khi tới người dùng ⇒ tài liệu độc hại không thể bịa trích dẫn hay trỏ sang tài liệu người khác.
- Câu trả lời không có nhãn hợp lệ ⇒ `grounded=false` (không tuyên bố có căn cứ).
- System prompt coi nội dung `<nguon>` là dữ liệu, bỏ qua mọi chỉ thị bên trong.
- **Chưa kiểm chứng:** việc *mô hình Claude thật* có tuân thủ quy tắc 4 của system prompt hay không. Test dùng FakeLLM nên chỉ chứng minh các rào cản **cấu trúc** (escape, lọc nhãn, trích dẫn từ ID). Cần bộ tấn công với Claude thật trước khi đưa production (mở: R-1).

### 2. Tệp tải lên độc hại
- Kiểm tra magic bytes `%PDF-`, kích thước tối đa, số tệp tối đa/người dùng, giới hạn số trang và độ phức tạp, PDF mật khẩu/hỏng/quét → lỗi có mã, không crash (`test_security.py`, `test_documents_api.py`, `test_pdf_extractor`).
- Tên tệp không dùng làm khóa lưu trữ (khóa là `user_id/uuid`); tên chứa `../`, CRLF được vô hiệu hóa/bác bỏ; không phản chiếu vào header.
- Không có giải nén/ thực thi nội dung ⇒ zip bomb không áp dụng; PDF "bom" bị chặn bởi giới hạn trang/độ phức tạp.
- Không quét mã độc (đề xuất, chưa làm): mở R-2.

### 3. Rate limit / lạm dụng
- Hỏi: 30/phút/người dùng, tải lên có hạn mức riêng, theo người dùng chứ không toàn cục (`test_rate_limit_applies_per_user_not_globally`). Bộ đếm hiện **trong bộ nhớ từng replica** ⇒ giới hạn thực tế = hạn mức × số replica (R-3).

### 4. CORS, CSP, header, XSS
- CORS: danh sách origin tường minh, không `*`; origin lạ không được echo (`test_cors_is_not_wildcard...`).
- **Đã sửa:** API trả `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` và CSP `default-src 'none'` cho `/api`; SPA có CSP không `unsafe-inline`/`unsafe-eval`, `frame-ancestors 'none'`.
- **Đã sửa:** nginx `add_header` ở `server` bị mất ở `location` có `add_header` riêng; chuyển sang `web.security.conf` được include ở mọi location, có test đối chiếu CSP nginx ↔ API.
- XSS: SPA không dùng `dangerouslySetInnerHTML`/`innerHTML`; câu trả lời và tên tệp luôn là text node (`Workspace.test.tsx` — "XSS"). Chưa render Markdown (nếu thêm, phải dùng bộ lọc HTML an toàn).
- CSP được kiểm bằng Playwright + axe trên devserver sau thay đổi (xem kết quả chạy cuối trong báo cáo tổng).

### 5. Secret và cấu hình
- Môi trường staging/prod từ chối khởi động với `AUTH_PROVIDER=dev`, `STORAGE_BACKEND=memory`, LLM/embedding giả. Endpoint `/dev/login` chỉ mount khi `environment=dev` **và** `auth_provider=dev` (test xác nhận vắng mặt ở môi trường test).
- Secret mặc định chỉ để dev (`dev-only-change-me-...`); production phải đặt qua secret manager (runbook `deploy/README.md` 4.5). JWT: kiểm tra chữ ký/`exp`, từ chối `alg=none` và token ký sai (`test_isolation.py`).
- **Đã sửa:** devserver lỗi `UnicodeEncodeError` khi stdout bị chuyển hướng trên Windows.

### 6. Cô lập dữ liệu và riêng tư
- 404 (không phải 403) cho mọi truy cập chéo người dùng: tài liệu, trích dẫn, hội thoại, tin nhắn, feedback, stop/regenerate; evaluator/ops không đọc được nội dung; báo cáo chỉ chứa số liệu tổng hợp (`test_isolation.py`, 11 test). RLS PostgreSQL được kiểm bởi `db/tests/*_integration.py` — **chưa chạy được ở máy này (cần Docker)**.
- Canary (nội dung PDF, câu hỏi, tên tệp) không xuất hiện trong log, `/metrics`, telemetry, audit, kể cả khi nhà cung cấp LLM ném lỗi dội lại prompt (`test_no_content_leak.py`).

### 7. Phụ thuộc (SCA)
- `pnpm audit --prod`: không có lỗ hổng đã biết.
- `pip-audit` (2026-10-23): chỉ `pip 26.1.1` (công cụ build, không đóng gói vào image runtime). Khuyến nghị nâng pip trong image build. Đã thêm bước SCA vào CI.
- Quét image (Trivy/Grype): **chưa chạy** (không có Docker); thêm vào CI là việc còn mở (R-4).

## Phát hiện đã sửa
| # | Mức | Phát hiện | Sửa |
|---|---|---|---|
| S-1 | Trung bình | API/SPA không có security headers, không CSP | Middleware `_security_headers`, CSP chặt, test |
| S-2 | Trung bình | nginx: header ở `server` biến mất ở `location` có `add_header` | `web.security.conf` include ở mọi location + test |
| S-3 | Thấp | devserver crash khi stdout không phải UTF-8 (Windows) | `reconfigure(encoding="utf-8")` |
| S-4 | Thấp (độ tin cậy dữ liệu) | Làm sạch header/footer có thể xóa sạch nội dung một trang gồm toàn dòng "lặp" ⇒ tài liệu bị `NO_TEXT` oan | Không bao giờ xóa hết nội dung trang + test |

## Rủi ro còn mở / chấp nhận
| ID | Rủi ro | Mức | Đề xuất |
|---|---|---|---|
| R-1 | Chưa red-team prompt injection với Claude thật | Cao (chưa biết) | Chạy bộ tấn công trên staging trước go-live; ghi tỉ lệ bị vượt rào |
| R-2 | Không quét mã độc cho PDF | Thấp–TB | Tích hợp ClamAV nếu chính sách yêu cầu |
| R-3 | Rate limit theo từng replica, Stop theo từng replica | Thấp | Chuyển bộ đếm sang Redis/PG khi scale > 1 replica |
| R-4 | Chưa quét image container, chưa kiểm NetworkPolicy thực tế | TB | Trivy trong CI; kiểm thử trên cụm staging |
| R-5 | Token lưu trong `sessionStorage` (XSS có thể đọc) | Thấp–TB | Giảm bằng CSP chặt (đã làm); cân nhắc cookie HttpOnly khi chọn IdP thật `[TBD: OQ-001]` |
