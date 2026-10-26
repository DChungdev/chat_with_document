# Kế hoạch kiểm thử tổng thể (Master Test Plan) — Công cụ “Chat với tài liệu”

**Chuẩn áp dụng:** IEEE 829-2008 (Software Test Documentation)
**Số tài liệu / Phiên bản:** TP-DOCCHAT-001 / v0.1 — Bản nháp
**Ngày lập:** 2026-10-23
**Nguồn đầu vào:** [PRD.md](../requirements/PRD.md) (PRD-DOCCHAT-001 v0.1), [User_Stories.html](../requirements/User_Stories.html), [SAD.md](../design/SAD.md), [API_Design.md](../design/API_Design.md) (SDD-API-DOCCHAT-001 v0.1), [UIUX_Blueprint_SDD.md](../design/UIUX_Blueprint_SDD.md) + prototype [UI_UX_design/](../design/UI_UX_design/), [Implement_Plan.md](../implement/Implement_Plan.md), báo cáo [performance.md](../implement/reports/performance.md) và [security_review.md](../implement/reports/security_review.md); prompt mẫu [testPlan_prompt.md](testPlan_prompt.md)

> **Quy ước:** **[Đề xuất]** = quyết định do kế hoạch kiểm thử này đưa ra, cần QA Lead/PO xác nhận. **[TBD: OQ-xxx]** = câu hỏi mở kế thừa từ BRD/PRD, **không phải quyết định**. Các ngưỡng số lấy từ PRD mục 5.1 và Implement Plan mục 7.2 (bản thân chúng đang là [Đề xuất]). Tài liệu này chỉ **lập kế hoạch**; không chứa kết quả thực thi.
>
> **Điều chỉnh so với prompt mẫu:** prompt mẫu là khung chung (thanh toán, đơn hàng, gRPC, MFA…). Các mục không áp dụng cho sản phẩm này đã bị loại, các mục còn lại được thay bằng nội dung thực của hệ thống (xem 5.0). Vì không có tài liệu SRS riêng, **PRD đóng vai trò SRS**; không có Figma, **prototype HTML + UI/UX Blueprint** đóng vai trò thiết kế giao diện.

---

## 1.0 Định danh kế hoạch kiểm thử (IEEE 829 §5.1)

| Thuộc tính | Giá trị |
|---|---|
| Document ID | TP-DOCCHAT-001 |
| Phiên bản | v0.1 |
| Ngày phát hành | 2026-10-23 |
| Trạng thái | Draft |
| Phân loại | Internal |
| Người lập | QA Team `[TBD: OQ-001]` |
| Người duyệt | QA Lead / PO / Tech Lead `[TBD: OQ-001]` |

---

## 2.0 Giới thiệu (§5.2)

### 2.1 Mục đích
- Xác định chiến lược kiểm thử cho MVP “Chat với tài liệu”: tải PDF → hỏi đáp RAG dạng streaming → trích dẫn kiểm chứng được → đo MET-001/MET-002.
- Xác định mức/loại kiểm thử, tiêu chí vào–ra, môi trường, công cụ, vai trò và lịch.
- Bảo đảm truy vết **yêu cầu → test**, với trọng tâm theo rủi ro (câu trả lời bịa, rò rỉ dữ liệu giữa người dùng, rò rỉ nội dung vào log).

### 2.2 Phạm vi

**Trong phạm vi (R1 — story P0; P1/P2 được lập kế hoạch ở mức khung, xem 4.3):**
- Chức năng: US-101, 102, 103, 201, 202, 203, 301, 302, 401, 402, 501.
- API `/api/v1` (REST + SSE), mô hình lỗi RFC 7807, idempotency, rate limit, CORS.
- Pipeline ingestion (hàng đợi, trích xuất, chunking, embedding, ghi chỉ mục).
- Chất lượng RAG: tỷ lệ đạt, trích dẫn hợp lệ, nhánh “không tìm thấy”.
- Giao diện SCR-01…SCR-09 trên Chrome, Edge, Safari (2 phiên bản gần nhất).
- Phi chức năng: hiệu năng, bảo mật, quyền riêng tư (log/telemetry), khả năng tiếp cận (WCAG 2.1 AA), khả năng phục hồi, vận hành (kill switch, giám sát).
- Hồi quy tự động trong CI.

**Ngoài phạm vi:**
- Nhà cung cấp LLM/Embedding/IdP (kiểm thử qua hợp đồng và giám sát, không kiểm thử nội bộ của họ).
- OCR / PDF quét (ADR-09 — chỉ kiểm thử báo lỗi rõ ràng), định dạng ngoài PDF, đồng bộ kho ngoài, workspace chia sẻ, mobile-native/offline (SAD 1.2).
- Pentest bởi bên thứ ba (kế hoạch riêng của bộ phận bảo mật; xem 6.7).
- Stress vượt 2× tải dự kiến (vài chục người dùng).

### 2.3 Mục tiêu kiểm thử

| ID | Mục tiêu | Tiêu chí thành công [Đề xuất] | Truy vết |
|---|---|---|---|
| OBJ-001 | Xác nhận toàn bộ AC của story P0 | 100% AC P0 có test tự động/thủ công và đạt | US-1xx…5xx, AC-001…004 |
| OBJ-002 | Xác nhận hợp đồng API | 100% endpoint IF-01…IF-10 + health/flags/reports có contract test; schema khớp OpenAPI | API_Design 3.3 |
| OBJ-003 | Xác nhận chất lượng câu trả lời | Bộ câu hỏi chuẩn: đạt ≥ 80% (MET-002); ≥ 90% có trích dẫn hợp lệ; 0 trích dẫn tới trang/tệp không tồn tại | PRD 5.1, OQ-009 |
| OBJ-004 | Xác nhận cô lập dữ liệu | 0 rò rỉ giữa người dùng (kể cả qua RLS, vector search, citation) | US-402, ADR-07 |
| OBJ-005 | Xác nhận quyền riêng tư | 0 nội dung tài liệu/câu hỏi trong log, telemetry, URL, header | PRD 5.1, ADR-10 |
| OBJ-006 | Xác nhận hiệu năng | Token đầu ≤ 5s p95 (≤ 10 PDF); xử lý PDF ≤ 60s; API không-AI p95 ≤ 300ms; tải trang ≤ 2s p95 | PRD 5.1, API 2.3 |
| OBJ-007 | Xác nhận UI/UX khớp thiết kế | Mọi màn/trạng thái SCR-01…09 khớp prototype | UIUX Blueprint |
| OBJ-008 | Xác nhận khả năng tiếp cận | WCAG 2.1 AA ở mức cơ bản `[Đề xuất; OQ-011]` | PRD 4.1(6) |
| OBJ-009 | Xác nhận khả năng vận hành | Kill switch diễn tập; cảnh báo hoạt động; runbook dùng được | PRD 5.1 |
| OBJ-010 | Xác nhận telemetry | 100% sự kiện PRD 5.2 phát đúng; MET-001/002 tính được | US-501 |

### 2.4 Tài liệu tham chiếu

| Tài liệu | Phiên bản | Nguồn |
|---|---|---|
| BRD-DOCCHAT-001 | v0.1 | BA |
| PRD-DOCCHAT-001 | v0.1 | Product |
| SAD-DOCCHAT-001 (IEEE 1016) | v0.1 | Architecture |
| SDD-API-DOCCHAT-001 | v0.1 | Development |
| UI/UX Blueprint + prototype HTML | v0.1 | Design |
| IMPL-DOCCHAT-001 | v0.1 | Development |
| IEEE 829-2008 | 2008 | IEEE |

---

## 3.0 Hạng mục kiểm thử (§5.3)

### 3.1 Phần mềm cần kiểm thử

| ID | Hạng mục | Công nghệ | Vị trí mã |
|---|---|---|---|
| SI-001 | Web SPA | React + TypeScript + Vite | `apps/web` |
| SI-002 | API service | FastAPI (Python 3.12) | `apps/api` |
| SI-003 | Ingestion worker | Python | `apps/worker` |
| SI-004 | Lõi miền (domain, retrieval, answering, ports) | Python | `packages/core` |
| SI-005 | Adapters (persistence, storage, llm, embedding, auth, observability) | Python | `infra` |
| SI-006 | Lược đồ CSDL, pgvector/HNSW, RLS | PostgreSQL 16 | `db/migrations` |
| SI-007 | Cấu hình triển khai, nginx (security headers), compose | YAML/nginx | `deploy` |
| SI-008 | Bộ câu hỏi chuẩn + script đánh giá | Python/JSON | D7 |

### 3.2 Sản phẩm/công cụ kiểm thử cần có

| ID | Artifact | Định dạng | Chủ sở hữu |
|---|---|---|---|
| TA-001 | Test case thủ công (UAT, tiếp cận, khám phá) | Markdown/bảng tính | QA |
| TA-002 | Dữ liệu kiểm thử: PDF mẫu đã duyệt (hợp lệ, hỏng, có mật khẩu, quét, nhiều trang, đa ngôn ngữ, độc hại) | PDF + manifest | QA + PO |
| TA-003 | Bộ câu hỏi chuẩn + đáp án tham chiếu `[TBD: OQ-009]` | JSON | PO + Lan + QA |
| TA-004 | Test tự động (pytest, vitest/jest, Playwright, k6) | Python/TS/JS | Dev + QA |
| TA-005 | Adapter giả lập (FakeLLM, FakeEmbedding, dev AuthProvider) và fault injection | Python | Dev |
| TA-006 | Môi trường Docker Compose (dev/CI) và staging | Compose/manifest | DevOps |
| TA-007 | Script đo: `scripts/perf_local.py`, `scripts/bench_ingest.py`, `deploy/perf/k6-chat.js` | Python/JS | QA |

---

## 4.0 Tính năng cần kiểm thử (§5.4)

### 4.1 Ma trận ưu tiên và rủi ro

Điểm rủi ro = Khả năng (1–5) × Tác động (1–5), xem mục 15.

| Ưu tiên | Tính năng | Epic | Story | Điểm rủi ro |
|---|---|---|---|---|
| **Cao** | F-01 Cô lập dữ liệu người dùng | E4 | US-402 | 20 |
| **Cao** | F-02 Trả lời có căn cứ / “không tìm thấy” | E2 | US-202 | 20 |
| **Cao** | F-03 Trích dẫn & nguồn gốc | E3 | US-301, 302 | 20 |
| **Cao** | F-04 Tải & xử lý PDF | E1 | US-101, 102 | 16 |
| **Cao** | F-05 Hỏi đáp streaming (SSE) | E2 | US-201, 203 | 16 |
| **Cao** | F-06 Xóa tài liệu & dữ liệu liên quan | E1/E4 | US-103 | 15 |
| **Cao** | F-07 Thông báo dữ liệu & cổng tuân thủ | E4 | US-401 | 15 |
| **Trung bình** | F-08 Telemetry & báo cáo MET | E5 | US-501 | 12 |
| **Trung bình** | F-09 Kill switch, giám sát, vận hành | — | PRD 5.1 | 12 |
| **Trung bình** | F-10 Xác thực, hết phiên, giữ bản nháp | E4 | US-402 (AC2) | 12 |
| **Thấp** | F-11 Các story P1 (US-104, 204, 205, 403, 502) | — | — | 6–9 |
| **Thấp** | F-12 Các story P2 (US-105, 206, 303) | — | — | 4 |

### 4.2 Ma trận tính năng × loại kiểm thử

| Tính năng | Unit | Tích hợp | API | System/E2E | UAT | Hồi quy | Hiệu năng | Bảo mật | Tiếp cận | Chất lượng RAG |
|---|---|---|---|---|---|---|---|---|---|---|
| F-01 Cô lập | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | – |
| F-02 Có căn cứ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| F-03 Trích dẫn | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ |
| F-04 Tải & xử lý | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – |
| F-05 Hỏi đáp SSE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| F-06 Xóa | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | – |
| F-07 Thông báo dữ liệu | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | – | ✓ | – |
| F-08 Telemetry | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | – |
| F-09 Kill switch/giám sát | ✓ | ✓ | ✓ | ✓ | – | ✓ | – | – | ✓ | – |
| F-10 Xác thực/hết phiên | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | – |

### 4.3 Mô tả tính năng và tiêu chí chấp nhận

| ID | Tính năng | Mô tả | AC nguồn |
|---|---|---|---|
| F-01 | Cô lập dữ liệu | Mọi truy vấn lọc theo `user_id` từ JWT; RLS ở DB; tài nguyên người khác → `404`; vector search lọc `user_id`. | US-402 |
| F-02 | Trả lời có căn cứ | Trả lời nhất quán với nguồn; không có chunk đạt ngưỡng → “không tìm thấy”, `grounded=false`, **không gọi LLM**. | US-202 (AC-003), ADR-04 |
| F-03 | Trích dẫn | Mỗi khẳng định chính có trích dẫn (tệp, trang); chip → panel đoạn gốc; nhãn `[Sx]` không hợp lệ bị loại; tệp đã xóa → `valid=false`, “Nguồn không còn khả dụng”. | US-301, 302, ADR-03 |
| F-04 | Tải & xử lý PDF | Multipart, kiểm tra `%PDF-`, kích thước/số lượng từ `/config`, `202` ≤ 2s, `Idempotency-Key`; nhiều tệp độc lập; trạng thái `processing → ready/error`; PDF hỏng/mật khẩu/quét → lỗi rõ. | US-101, 102 (AC-001) |
| F-05 | Hỏi đáp SSE | Sự kiện `message`, `token`, `citations`, `done`, `error`, `ping`; Enter/Shift+Enter; chặn gửi khi rỗng/chưa có tệp `ready`; gộp nhiều PDF. | US-201, 203 (AC-002) |
| F-06 | Xóa | Xác nhận → tệp biến mất, chunk bị cascade, PDF gốc bị xóa, citation `valid=false`, ghi audit; hỏi sau đó không dẫn tới tệp đã xóa. | US-103 |
| F-07 | Thông báo dữ liệu | Chưa xác nhận → upload bị chặn (`403 NOTICE_NOT_ACCEPTED`); xác nhận lại khi `noticeVersion` đổi; sự kiện `data_notice_accepted`. | US-401 |
| F-08 | Telemetry | `POST /telemetry/events` allow-list; thuộc tính lạ bị loại và đếm; `userHash` do server thêm; MET-001/002 tính được; báo cáo chỉ cho vai trò `evaluator`. | US-501 (AC-004) |
| F-09 | Vận hành | `qa_enabled=false` → `503 QA_DISABLED` + banner SCR-08; health live/ready; metrics, cảnh báo. | PRD 5.1 |
| F-10 | Phiên | JWT thiếu/hết hạn → `401`; overlay SCR-07; bản nháp câu hỏi được giữ. | US-402, PRD 4.2 |
| F-11 | P1 (khung) | US-104 chọn tài liệu; US-204 hỏi nối tiếp; US-205 dừng/tạo lại (`POST /messages/{id}/stop`, `/regenerate`); US-403 nhật ký; US-502 phản hồi (`PUT …/feedback`). Test case chi tiết viết ở sprint S6. | — |
| F-12 | P2 (khung) | US-105 kéo-thả; US-206 sao chép/xuất; US-303 mở PDF tại trang. | — |

---

## 5.0 Tính năng không kiểm thử (§5.5)

| ID | Tính năng | Lý do | Rủi ro | Kế hoạch tương lai |
|---|---|---|---|---|
| NT-01 | Nội bộ nhà cung cấp LLM/Embedding/IdP | Trách nhiệm nhà cung cấp | Thấp | Kiểm thử hợp đồng + fault injection + giám sát |
| NT-02 | OCR / nội dung PDF quét | Ngoài MVP (ADR-09) | Trung bình | Chỉ kiểm thử báo lỗi rõ; kế hoạch riêng nếu thêm OCR |
| NT-03 | Định dạng ngoài PDF, đồng bộ kho ngoài, chia sẻ tài liệu, đa-tenant | Ngoài phạm vi (SAD 1.2) | Thấp | Ngoài R1 |
| NT-04 | Mobile-native / offline | Ngoài phạm vi (PRD 0) | Thấp | — |
| NT-05 | Pentest bên thứ ba, red-team với LLM thật | Do bộ phận bảo mật quyết định | Cao | Đề xuất thực hiện trước khi dùng dữ liệu thật (xem 6.7, mục 15) |
| NT-06 | Tải trên 2× dự kiến (stress cực đoan) | Quy mô MVP vài chục người dùng | Thấp | Làm lại nếu mở rộng |
| NT-07 | API đối tác, webhook, GraphQL, gRPC | Không có trong MVP | Thấp | — |

> **Không áp dụng từ prompt mẫu:** thanh toán, đơn hàng, MFA, gRPC, quản trị người dùng, báo cáo xuất/lên lịch — hệ thống này không có các tính năng đó.

---

## 6.0 Phương pháp tiếp cận (§5.6)

### 6.0 Nguyên tắc
1. **Rủi ro trước:** cô lập, căn cứ/trích dẫn, rò rỉ nội dung được kiểm thử sâu nhất và chạy trong **mỗi lần CI**.
2. **Port/Adapter:** kiểm thử logic nghiệp vụ bằng FakeLLM/FakeEmbedding; kiểm thử **chất lượng thật** riêng với dịch vụ thật khi được pháp chế duyệt (OQ-012/013).
3. **Phân biệt rõ phạm vi bằng chứng:** kết quả trên adapter giả/kho vector trong bộ nhớ chỉ chứng minh logic và rào cản cấu trúc, **không** chứng minh p95 hay chất lượng với Claude/pgvector thật (xem performance.md, security_review.md).
4. **Dữ liệu:** chỉ dùng PDF thử đã duyệt cho đến khi pháp chế phê duyệt dữ liệu thật.

### 6.1 Kiểm thử đơn vị (Unit)

| Thuộc tính | Mô tả |
|---|---|
| Trách nhiệm | Dev (QA rà soát) |
| Công cụ | pytest, vitest/jest, React Testing Library |
| Mục tiêu | ≥ 70% logic nghiệp vụ (PRD 5.1) |
| Vào | Mã hoàn thành, PR được review |
| Ra | Tất cả đạt, đạt ngưỡng bao phủ |
| Tập trung | Domain & trạng thái, retrieval (ngưỡng, dựng ngữ cảnh), answering (`LabelFilter`, ghép citation, escape), chunking giữ trang, validator, rate limit, bộ lọc log/telemetry, component UI |
| Mock | LLM, embedding, S3, DB (ở mức unit) |

Trường hợp chính:

| ID | Đối tượng | Kỳ vọng | Truy vết |
|---|---|---|---|
| UT-001 | Chuyển trạng thái `Document` | Chỉ cho phép `processing→ready/error`; chuyển ngược/ngoài luồng bị từ chối | SAD 3.6 |
| UT-002 | Chuyển trạng thái `Message` | `sending→streaming→complete/interrupted/failed/stopped` | API 3.6 |
| UT-003 | Chunking | ~800 token, chồng 100, giữ `page_start/page_end`, không chunk rỗng | C4 |
| UT-004 | Retrieval ngưỡng | Không chunk ≥ ngưỡng → nhánh “không tìm thấy”, không gọi LLM | ADR-04 |
| UT-005 | `LabelFilter` | Nhãn `[Sx]` không thuộc tập nguồn bị bóc; nhãn hợp lệ → citation | D5, ADR-03 |
| UT-006 | Escape ngữ cảnh | `& < >` trong chunk/tên tệp/câu hỏi bị escape, không đóng được thẻ `<nguon>` | G8 |
| UT-007 | Rate limit | 30 câu hỏi/phút, 20 tải lên/giờ; trả `Retry-After` | API 2.3 |
| UT-008 | Bộ lọc log | Chỉ trường allow-list; nội dung bị loại | A6 |
| UT-009 | Allow-list telemetry | Thuộc tính lạ/chuỗi dài bị loại và đếm | ADR-10 |
| UT-010 | Băm `user_id` | Có muối, một chiều, ổn định | B10 |
| UT-011 | Validator tệp | `%PDF-`, kích thước, số lượng, tên tệp | B4 |
| UT-012 | Trả lời không có nhãn hợp lệ | `grounded=false`, không citation | API 3.4.3 |

### 6.2 Kiểm thử tích hợp (Integration)

| Thuộc tính | Mô tả |
|---|---|
| Trách nhiệm | Dev + QA |
| Công cụ | pytest + testcontainers (Postgres+pgvector, MinIO), httpx |
| Phạm vi | API ↔ DB/RLS, API ↔ object storage, hàng đợi ingest, worker, vector store |
| Vào | Unit đạt, CI xanh |
| Ra | Tất cả đạt trên Postgres+MinIO **thật** (không chỉ in-memory) |

| ID | Kịch bản | Kỳ vọng |
|---|---|---|
| INT-001 | Upload → worker → `ready` | Chunk + embedding được ghi, `status=ready`, `pageCount` đúng |
| INT-002 | Hàng đợi `FOR UPDATE SKIP LOCKED` với 2 worker | Mỗi job chạy đúng một lần; retry idempotent |
| INT-003 | Một tệp lỗi trong lô | Tệp khác vẫn `ready` (AC-001) |
| INT-004 | RLS: truy vấn không đặt `app.user_id` | Không trả dòng nào |
| INT-005 | Tìm vector top-k | Chỉ chunk của `user_id` + `documentIds` + tài liệu `ready` |
| INT-006 | Xóa tài liệu | Cascade chunk, xóa object S3, citation `valid=false`, có audit |
| INT-007 | Lưu câu hỏi trước khi gọi dịch vụ ngoài | Khi LLM lỗi, câu hỏi vẫn còn |
| INT-008 | Migration lên/xuống | Lược đồ khớp Database_Design_SQL; HNSW tồn tại |
| INT-009 | Cấu hình `app_config` đổi nóng | `/config` phản ánh giới hạn mới |
| INT-010 | Circuit breaker/timeout adapter LLM & embedding | Hết thời gian → lỗi `retryable`, không treo |

### 6.3 Kiểm thử API

| Thuộc tính | Mô tả |
|---|---|
| Trách nhiệm | QA + Dev |
| Công cụ | pytest + httpx, schemathesis/Dredd (contract từ `/api/v1/openapi.json`), Postman/Newman (tuỳ chọn) |
| Phạm vi | Toàn bộ endpoint ở API_Design 3.3 |
| Ra | 100% endpoint có test dương + âm + xác thực + cô lập; schema khớp OpenAPI; lỗi là `application/problem+json` |

Danh mục test API (mỗi endpoint đều có thêm: không JWT → `401`; tài nguyên của người khác → `404`):

| ID | Endpoint | Loại | Kiểm tra | Kỳ vọng | Story |
|---|---|---|---|---|---|
| API-001 | `GET /config` | Dương | Giới hạn, `qaEnabled`, `noticeVersion`, `noticeAccepted` | `200`, đúng schema | US-401 |
| API-002 | `GET /data-notice` | Dương | Nội dung hiện hành | `200` | US-401 |
| API-003 | `POST /data-notice/acceptances` | Dương/Lặp | Xác nhận; gọi lại | `201`; idempotent | US-401 |
| API-004 | `POST /documents` | Dương | PDF hợp lệ + `Idempotency-Key` | `202`, `Location`, `status=processing`, ≤ 2s | US-101 |
| API-005 | `POST /documents` | Idempotent | Gửi lại cùng key | Cùng bản ghi, không trùng | PRD 4.2 |
| API-006 | `POST /documents` | Âm | Không phải PDF / sai chữ ký `%PDF-` | `400 INVALID_FILE_TYPE` | US-101 |
| API-007 | `POST /documents` | Âm | Quá kích thước | `413 FILE_TOO_LARGE` | US-101 |
| API-008 | `POST /documents` | Âm | Vượt số tệp | `409 LIMIT_EXCEEDED` | US-101 |
| API-009 | `POST /documents` | Âm | Chưa xác nhận thông báo | `403 NOTICE_NOT_ACCEPTED` | US-401 |
| API-010 | `POST /documents` | Âm | Vượt 20 lượt/giờ | `429` + `Retry-After` | API 2.3 |
| API-011 | `GET /documents` | Dương | Phân trang cursor (`limit`≤100, `cursor`), trạng thái | `200 {items,nextCursor}` | US-102 |
| API-012 | `GET /documents/{id}` | Dương/Âm | Poll trạng thái; id lạ/người khác | `200` / `404 NOT_FOUND` | US-102 |
| API-013 | `DELETE /documents/{id}` | Dương/Âm | Xóa; xóa lại; của người khác | `204` / `404` | US-103 |
| API-014 | `POST /conversations` | Dương | Tạo; `Idempotency-Key` | `201` | US-201 |
| API-015 | `POST /conversations/{id}/messages` | Dương | Luồng SSE đủ `message→token…→citations→done` | `text/event-stream`, header `no-cache`, `X-Accel-Buffering: no` | US-201 |
| API-016 | `…/messages` | Âm trước stream | Rỗng / quá dài / `documentIds` không `ready` / không có tệp `ready` | `422/413/409/422 NO_READY_DOCUMENTS` dạng JSON, không SSE | US-201 |
| API-017 | `…/messages` | Âm | `documentIds` của người khác | `404` | US-402 |
| API-018 | `…/messages` | Âm | `qa_enabled=false` | `503 QA_DISABLED` | PRD 5.1 |
| API-019 | `…/messages` | Không tìm thấy | Câu hỏi ngoài tài liệu | `token` + `done{grounded:false,citationCount:0}`, **LLM không bị gọi** | US-202 |
| API-020 | `…/messages` | Idempotent | Lặp `clientMessageId` | Không tạo câu hỏi trùng | CN-05 |
| API-021 | `…/messages` | Lỗi giữa chừng | LLM timeout giữa stream | Sự kiện `error{retryable}`; giữ phần đã gửi; `status=interrupted/failed` | PRD 4.2 |
| API-022 | `…/messages` | Hủy | Client đóng kết nối | Server hủy LLM, `interrupted` | API 3.4.3 |
| API-023 | `…/messages` | Nhiều tài liệu | `documentIds` ≥ 2 | `citations` chứa ≥ 2 tài liệu | US-203 |
| API-024 | `…/messages` | An toàn nhãn | LLM sinh nhãn `[S9]` không tồn tại | Nhãn bị bóc khỏi `token`, không citation giả | ADR-03 |
| API-025 | `GET /citations/{id}` | Dương | Snippet, tệp, trang, `valid=true` | `200` | US-302 |
| API-026 | `GET /citations/{id}` | Tài liệu đã xóa | — | `200 valid=false`, `snippet/documentId/documentName=null` | US-302 |
| API-027 | `GET /citations/{id}` | Cô lập | Citation của người khác | `404` | US-402 |
| API-028 | `POST /telemetry/events` | Dương | Lô sự kiện allow-list | `202 {accepted,rejected}` | US-501 |
| API-029 | `POST /telemetry/events` | Âm | Thuộc tính lạ, chuỗi dài, tên sự kiện lạ | Bị loại, `rejected>0` | ADR-10 |
| API-030 | `GET /reports/mvp-metrics` | Phân quyền | Vai trò `user` vs `evaluator` | `403` / `200` (chỉ tổng hợp) | US-501 |
| API-031 | `PUT /admin/flags/qa-enabled` | Phân quyền | Vai trò `user` vs `ops` | `403` / `204` | PRD 5.1 |
| API-032 | `GET /health/live`, `/health/ready` | Dương | Không cần JWT; ready phản ánh DB | `200`/`503` | PRD 5.1 |
| API-033 | Mọi endpoint | Lỗi chung | Định dạng RFC 7807: `type,title,status,code,detail,retryable,requestId` | Đúng schema; `detail` không chứa nội dung | API 3.4.6 |
| API-034 | Mọi endpoint | Header | `X-Request-Id` trả về | Có | API 2.3 |
| API-035 | Mọi endpoint | CORS | Origin lạ; `*` | Từ chối; không `*` | API 2.4 |
| API-036 | `POST /messages/{id}/stop` (P1) | Dương | Dừng khi đang stream | `202`; stream kết thúc `done{status:stopped}` | US-205 |
| API-037 | `POST /messages/{id}/regenerate` (P1) | Dương | Sau `interrupted` | Message AI mới, bản cũ giữ | PRD 4.2 |
| API-038 | `PUT /messages/{id}/feedback` (P1) | Idempotent | Đặt hai lần | `204`, kết quả giống nhau | US-502 |
| API-039 | `GET /conversations/{id}/messages` (P1) | Dương | Lịch sử `[TBD: OQ-012]` | `200` | US-204 |

### 6.4 Kiểm thử hệ thống / E2E

| Thuộc tính | Mô tả |
|---|---|
| Trách nhiệm | QA |
| Công cụ | Playwright (Chromium, Edge, WebKit) — `apps/web/e2e` |
| Phạm vi | Luồng người dùng xuyên SPA ↔ API ↔ worker ↔ DB |
| Vào | Tích hợp & API đạt, UI ổn định, staging sẵn sàng |
| Ra | Mọi E2E P0 đạt, không còn lỗi Blocker/Critical |

| ID | Luồng | Bước chính | Kỳ vọng | Story |
|---|---|---|---|---|
| E2E-001 | Hành trình chính của Lan | Mở → xác nhận thông báo → tải PDF → chờ `ready` → hỏi → xem chip → mở panel nguồn → xóa tệp | Mỗi bước đạt AC; sau xóa, hỏi lại không có trích dẫn tới tệp đã xóa | US-101…103, 201, 301, 302, 401 |
| E2E-002 | Tải nhiều PDF, một tệp lỗi | Chọn 3 PDF (1 hỏng) | 2 tệp `ready`, tệp lỗi hiển thị lỗi riêng | AC-001 |
| E2E-003 | Hỏi khi một phần tệp chưa sẵn sàng | 1 `ready`, 1 `processing` | Gửi được; thông báo tệp chưa sẵn sàng không được dùng | PRD 4.2 |
| E2E-004 | Chưa có tài liệu | Mở app lần đầu sau xác nhận | Ô nhập bị vô hiệu + lý do + nút “Tải PDF đầu tiên” | AC-002 |
| E2E-005 | “Không tìm thấy” | Hỏi ngoài phạm vi | Thông điệp “không tìm thấy trong tài liệu đã tải”, không chip | AC-003 |
| E2E-006 | Tổng hợp nhiều PDF | 2 PDF, câu hỏi cần cả hai | Câu trả lời có chip từ cả hai tệp | US-203 |
| E2E-007 | Gián đoạn mạng khi trả lời | Ngắt mạng giữa stream | Giữ phần đã nhận, nhãn “Bị gián đoạn”, “Tạo lại”; câu hỏi không mất | PRD 4.2 |
| E2E-008 | Mất mạng khi tải lên | Ngắt khi upload | “Tải thất bại” + “Thử lại”; thử lại không tạo trùng | PRD 4.2 |
| E2E-009 | Phiên hết hạn | JWT hết hạn khi soạn câu hỏi | Overlay SCR-07, bản nháp được giữ, tiếp tục sau đăng nhập lại | US-402 |
| E2E-010 | Kill switch | `qa_enabled=false` | Banner SCR-08, ô hỏi bị chặn, không xóa dữ liệu | PRD 5.1 |
| E2E-011 | Cô lập hai người dùng | A tải + hỏi; B truy cập bằng id của A | B không thấy tệp, citation, hội thoại | US-402 |
| E2E-012 | Trích dẫn tới tệp đã xóa | Xóa tệp rồi bấm chip cũ | “Nguồn không còn khả dụng” | PRD 4.2 |
| E2E-013 | Báo cáo MET | Tạo vài tác vụ → mở SCR-09 bằng `evaluator` | Có MET-001/002 và ghi “chưa thể kết luận” nếu mục tiêu chưa duyệt | AC-004 |
| E2E-014 | Dừng sinh (P1) | Bấm Dừng khi đang stream | Giữ phần đã nhận, trạng thái `stopped` | US-205 |

### 6.5 Kiểm thử chấp nhận (UAT)

| Thuộc tính | Mô tả |
|---|---|
| Trách nhiệm | PO, Lan (đại diện người dùng), Minh, Hà (pháp chế/bảo mật), QA điều phối |
| Phương thức | Thủ công trên staging với PDF thử đã duyệt |
| Vào | System/E2E đạt, Go/No-Go S5 đang chờ |
| Ra | Mọi AC P0 đạt; ký duyệt theo BRD 4.14 |

| ID | Story | Kịch bản | Tiêu chí |
|---|---|---|---|
| UAT-001 | US-101 | Tải 1 và nhiều PDF hợp lệ/không hợp lệ | AC-001 |
| UAT-002 | US-102 | Quan sát chuyển trạng thái tự động | Không cần tải lại trang |
| UAT-003 | US-103 | Xóa tài liệu và hỏi lại | Không còn trích dẫn tới tệp |
| UAT-004 | US-201/202 | Bộ câu hỏi thực tế của Lan | Câu trả lời nhất quán nguồn |
| UAT-005 | US-203 | Câu hỏi tổng hợp nhiều tệp | Mỗi ý có nguồn |
| UAT-006 | US-301/302 | Kiểm chứng từng chip | Đoạn gốc đúng, đúng trang |
| UAT-007 | US-401 | Lần đầu truy cập | Phải xác nhận trước khi tải |
| UAT-008 | US-402 | Phối hợp hai tài khoản | Không thấy dữ liệu nhau |
| UAT-009 | US-501 | Chạy phiên thử và xem báo cáo | MET-001/002 tính được |
| UAT-010 | Hà | Rà soát thông báo, vòng đời dữ liệu, nhà cung cấp `[TBD: OQ-012/013]` | Pháp chế phê duyệt trước dữ liệu thật |

### 6.6 Kiểm thử chất lượng RAG (đặc thù sản phẩm)

| Thuộc tính | Mô tả |
|---|---|
| Trách nhiệm | PO/Lan (đáp án), AI/BE (chạy), QA (xác minh) |
| Công cụ | Script đánh giá D7 trên bộ câu hỏi chuẩn `[TBD: OQ-009]` |
| Môi trường | Staging với embedding + LLM thật và pgvector (HNSW) — **bắt buộc**; chạy trên adapter giả chỉ để kiểm tra pipeline |
| Chỉ số | Tỷ lệ đạt (MET-002 ≥ 80%); tỷ lệ trích dẫn hợp lệ ≥ 90%; 0 trích dẫn tới trang/tệp không tồn tại; tỷ lệ “không tìm thấy” đúng; tỷ lệ bịa thông tin |
| Lặp lại | Sau mỗi thay đổi prompt, chunking, ngưỡng, k, mô hình; D8 hiệu chỉnh |

| ID | Kịch bản | Kỳ vọng |
|---|---|---|
| RAG-001 | Câu hỏi có đáp án trong 1 tệp | Đúng nội dung + trích dẫn đúng trang |
| RAG-002 | Câu hỏi cần ≥ 2 tệp | Có ý từ mỗi tệp, nguồn tương ứng |
| RAG-003 | Câu hỏi ngoài tài liệu | “Không tìm thấy”, không suy đoán từ kiến thức ngoài |
| RAG-004 | Câu hỏi tiếng Việt có dấu / không dấu / Anh–Việt xen kẽ `[TBD: OQ-008]` | Đạt ngưỡng đã hiệu chỉnh |
| RAG-005 | PDF bố cục phức tạp (bảng, nhiều cột) | Ghi nhận giới hạn; không bịa số liệu |
| RAG-006 | Câu hỏi mơ hồ / quá ngắn | Không bịa; trả lời hoặc “không tìm thấy” hợp lý |
| RAG-007 | Hai tệp mâu thuẫn nhau | Nêu cả hai nguồn, không trộn thành một khẳng định |
| RAG-008 | Trang trích dẫn so với trang thực của đoạn | Trùng khớp 100% mẫu kiểm tra thủ công |

### 6.7 Kiểm thử bảo mật & quyền riêng tư

| Thuộc tính | Mô tả |
|---|---|
| Trách nhiệm | QA + Dev + Bảo mật |
| Công cụ | pytest (`test_security.py`, `test_isolation.py`, `test_no_content_leak.py` và bổ sung), OWASP ZAP (DAST), pip-audit/npm audit/Snyk (SCA), gitleaks, trivy (image) |
| Vào | Ứng dụng đã triển khai lên staging |
| Ra | Không còn lỗ hổng Cao/Nghiêm trọng (PRD 5.1) |

| ID | Hạng mục | Kịch bản | Kỳ vọng |
|---|---|---|---|
| SEC-001 | Cô lập (IDOR) | Dùng id tài liệu/hội thoại/citation/message của người khác ở **mọi** endpoint | `404`, không lộ sự tồn tại |
| SEC-002 | RLS | Bỏ lớp ứng dụng, truy vấn DB với `app.user_id` khác | Không thấy dữ liệu |
| SEC-003 | Vector search | Truy vấn chứa nội dung giống tài liệu người khác | Không chunk nào của người khác |
| SEC-004 | Xác thực | JWT thiếu/sai chữ ký/hết hạn/`alg=none`/sai `aud` | `401` |
| SEC-005 | Phân quyền vai trò | `user` gọi báo cáo/flag | `403` |
| SEC-006 | Prompt injection qua PDF | Tệp chứa “bỏ qua chỉ dẫn”, thẻ `</nguon>`, nhãn `[S1]` giả | Không phá cấu trúc, không bịa trích dẫn, không rò system prompt |
| SEC-007 | Prompt injection qua câu hỏi | Chèn thẻ `<cau_hoi>` | Bị escape |
| SEC-008 | Tệp độc hại | PDF giả (đổi đuôi), PDF có JS/nhúng, zip bomb, tên tệp `../..`, tên tệp có HTML | Từ chối hoặc vô hại; không XSS |
| SEC-009 | XSS | Nội dung trả lời/snippet/tên tệp chứa HTML/script | Hiển thị an toàn (escape) |
| SEC-010 | Rò rỉ nội dung vào log | Quét log API/worker/nginx sau bộ kịch bản | 0 nội dung tài liệu/câu hỏi |
| SEC-011 | Rò rỉ vào telemetry | Phân tích `telemetry_events` | Chỉ siêu dữ liệu |
| SEC-012 | Nội dung trong URL/header | Rà soát request/response | Không có nội dung trong URL, query, header tùy biến |
| SEC-013 | Rate limit | Vượt 30 câu hỏi/phút, 20 tải lên/giờ | `429` + `Retry-After` |
| SEC-014 | CORS / headers | CSP, HSTS, X-Content-Type-Options, frame-ancestors; nginx kế thừa `add_header` | Có đủ; origin lạ bị chặn |
| SEC-015 | Mã hóa | TLS khi truyền; SSE/at-rest bucket & DB | Có |
| SEC-016 | Secrets | Quét repo/ảnh container | 0 secret |
| SEC-017 | Phụ thuộc | SCA | Không CVE Cao/Nghiêm trọng chưa xử lý |
| SEC-018 | Xóa dữ liệu | Sau `DELETE`, kiểm tra DB, object storage, bản sao/backup theo chính sách `[TBD: OQ-012]` | Không còn dữ liệu truy cập được |
| SEC-019 | Red-team với LLM thật | Chạy bộ SEC-006/007 trên Claude thật | Rào cản cấu trúc giữ vững; ghi nhận hành vi mô hình (hiện **chưa kiểm chứng**, xem security_review.md) |

### 6.8 Kiểm thử hiệu năng

| Thuộc tính | Mô tả |
|---|---|
| Trách nhiệm | QA + DevOps |
| Công cụ | k6 (`deploy/perf/k6-chat.js`), `scripts/perf_local.py`, `scripts/bench_ingest.py`, Lighthouse |
| Môi trường | **Staging**: LLM/embedding thật, Postgres+pgvector, worker tách tiến trình |
| Vào | Build ổn định, giám sát bật |
| Ra | Đạt các ngưỡng ở bảng dưới |

> Số liệu hiện có (performance.md) đo trên máy dev, adapter giả, vector in-memory — **không** dùng để kết luận đạt/không đạt; mục này lập kế hoạch đo thật.

| ID | Loại | Tải | Thời lượng | Chỉ số mục tiêu |
|---|---|---|---|---|
| PERF-001 | Baseline | 1 người dùng, 10 PDF | 15 phút | Token đầu p95 ≤ 5s |
| PERF-002 | Load | 20 người dùng đồng thời, mỗi người ≤ 10 PDF, ≤ 30 câu/phút | 1 giờ | Token đầu p95 ≤ 5s; endpoint không-AI p95 ≤ 300ms; lỗi < 1% |
| PERF-003 | Ingest | PDF 30 và 50 trang (và PDF ở biên giới hạn cho phép `[TBD: OQ-008]`) | — | Xử lý ≤ 60s; ingest song song không làm API chậm |
| PERF-004 | Đồng thời ingest + hỏi đáp | 20 VU vừa tải vừa hỏi | 30 phút | Không treo; backlog hàng đợi hồi phục |
| PERF-005 | Spike | 0 → 40 → 0 người dùng | 10 phút | Hồi phục ≤ 1 phút; không mất message |
| PERF-006 | Endurance | 10 người dùng | 8 giờ | Không tăng bộ nhớ/kết nối bất thường (pool DB) |
| PERF-007 | SSE qua proxy | Nginx/WAF thật | — | Không buffer; `ping` mỗi 15s giữ kết nối |
| PERF-008 | UI | Lighthouse trên SCR-02/04 | — | Tải trang đầu ≤ 2s p95; LCP/INP ghi nhận |
| PERF-009 | HNSW | 10 PDF × nhiều trang | — | Độ trễ top-k và recall chấp nhận được; đề xuất `ef_search` |

### 6.9 Kiểm thử khả năng tiếp cận (WCAG 2.1 AA — mức cơ bản)

| Thuộc tính | Mô tả |
|---|---|
| Trách nhiệm | QA (+ thiết kế) |
| Công cụ | axe-core (trong Playwright), Lighthouse, NVDA/VoiceOver (thủ công) |
| Ra | Không còn vi phạm Serious/Critical của axe; luồng P0 dùng được hoàn toàn bằng bàn phím |

| ID | Kiểm tra | Kỳ vọng |
|---|---|---|
| ACC-001 | Điều hướng bàn phím toàn luồng P0 | Mọi điều khiển dùng được, thứ tự hợp lý |
| ACC-002 | Trình đọc màn hình | Trạng thái tài liệu, “đang tạo câu trả lời”, lỗi được đọc |
| ACC-003 | Tương phản (sáng/tối) | ≥ 4.5:1 chữ thường |
| ACC-004 | Không chỉ dùng màu | Trạng thái dùng biểu tượng + chữ |
| ACC-005 | Quản lý focus | Panel nguồn/hộp thoại xóa: bẫy focus; **Esc** trả focus về chip |
| ACC-006 | Vùng live | Token streaming/lỗi được thông báo hợp lý, không spam |
| ACC-007 | Thu phóng 200% / reflow | Không mất nội dung/chức năng |

### 6.10 Kiểm thử UI/UX & tương thích trình duyệt

| Thuộc tính | Mô tả |
|---|---|
| Trách nhiệm | QA + Thiết kế |
| Công cụ | Playwright (ảnh chụp so sánh), kiểm thử thủ công |
| Ra | Khớp prototype; chạy được trên Chrome, Edge, Safari (2 phiên bản gần nhất) |

| ID | Kiểm tra | Kỳ vọng |
|---|---|---|
| UI-001 | So khớp SCR-01…SCR-09 với prototype | Bố cục, nhãn tiếng Việt, token thiết kế khớp |
| UI-002 | Responsive | Desktop ≥ 1280; Panel nguồn thành bottom sheet < 1024px; không cuộn ngang |
| UI-003 | Trạng thái thành phần | Mặc định/hover/active/disabled/loading/error/empty đều có |
| UI-004 | Nhãn AI cố định | “Câu trả lời do AI tạo, hãy kiểm tra nguồn trước khi sử dụng” luôn hiển thị |
| UI-005 | Chat | Enter gửi, Shift+Enter xuống dòng, Gửi bị vô hiệu khi rỗng/quá dài |
| UI-006 | Theme sáng/tối | Cả hai đạt UI-001 |
| UI-007 | Streaming | Hiển thị tăng dần, không nhấp nháy, cuộn hợp lý |
| UI-008 | Tương thích | SSE `fetch` stream hoạt động trên cả 3 trình duyệt |

### 6.11 Kiểm thử hồi quy

| Thuộc tính | Mô tả |
|---|---|
| Kích hoạt | Mỗi PR/merge (smoke + unit + API), mỗi build staging (đầy đủ), sau mỗi sửa lỗi, mỗi thay đổi prompt/ngưỡng/mô hình |
| Cách làm | 100% AC P0 có test hồi quy tự động (PRD 5.1) |

| Bộ | Phạm vi | Tần suất |
|---|---|---|
| REG-001 Smoke | Health, đăng nhập dev, upload→ready→hỏi→citation | Mỗi PR |
| REG-002 Unit + API contract | 6.1 + 6.3 | Mỗi PR |
| REG-003 Cô lập & rò rỉ | SEC-001…003, SEC-010…012 | **Mỗi PR** (rủi ro cao nhất) |
| REG-004 Tích hợp Postgres/MinIO | 6.2 | Mỗi merge vào main |
| REG-005 E2E P0 | E2E-001…013 | Mỗi build staging |
| REG-006 Chất lượng RAG | Bộ câu hỏi chuẩn | Khi đổi prompt/k/ngưỡng/chunking/mô hình; trước mỗi release |

### 6.12 Kiểm thử vận hành & phục hồi

| ID | Kịch bản | Kỳ vọng |
|---|---|---|
| OPS-001 | Diễn tập kill switch | `503 QA_DISABLED` ≤ vài giây; bật lại khôi phục; upload/xóa không ảnh hưởng |
| OPS-002 | LLM lỗi/chậm (fault injection) | Thông báo thân thiện, giữ câu hỏi, circuit breaker mở/đóng đúng |
| OPS-003 | Embedding lỗi khi ingest | Retry; sau đó `error` có `errorCode`; không ảnh hưởng tệp khác |
| OPS-004 | Worker chết giữa job | Job được nhận lại, không trùng chunk |
| OPS-005 | DB/S3 tạm mất | `ready` trả `503`; API hồi phục khi dịch vụ lên lại |
| OPS-006 | Cảnh báo | p95 token đầu > 5s, `answer_failed` cao, tồn đọng hàng đợi, lỗi LLM → cảnh báo kích hoạt |
| OPS-007 | Runbook | Một người ngoài đội làm theo được để xử lý sự cố mẫu |
| OPS-008 | Telemetry funnel | Toàn bộ sự kiện PRD 5.2 phát đúng và theo đúng thứ tự phễu |
| OPS-009 | Nhiều bản sao API + `stop` | Yêu cầu dừng tới đúng bản sao giữ stream (hoặc cơ chế thông báo) — xem API 3.4.3 |

---

## 7.0 Tiêu chí đạt/không đạt hạng mục (§5.7)

**Mức nghiêm trọng lỗi:** Blocker (chặn luồng P0 hoặc rò rỉ dữ liệu) · Critical (sai chức năng P0 không có cách khắc phục) · Major (sai chức năng, có cách khắc phục) · Minor · Trivial.

| Hạng mục | Đạt khi |
|---|---|
| Test case | Kết quả thực tế = kỳ vọng ở mọi bước |
| Story P0 | Mọi AC đạt (11/11) |
| Cổng chức năng | Không Blocker/Critical; ≤ 3 Major có phương án khắc phục |
| Chất lượng trả lời | MET-002 ≥ 80%; ≥ 90% có trích dẫn hợp lệ; **0** trích dẫn tới tệp/trang không tồn tại |
| Cô lập | **0** rò rỉ giữa người dùng |
| Quyền riêng tư | **0** nội dung trong log/telemetry/URL |
| Hiệu năng (staging thật) | Token đầu ≤ 5s p95 (≤ 10 PDF); PDF ≤ 60s; tải trang ≤ 2s p95 |
| Bảo mật | Không lỗ hổng Cao/Nghiêm trọng còn mở |
| Bao phủ tự động | ≥ 70% logic nghiệp vụ; 100% AC P0 có test hồi quy |
| Tương thích | Chrome, Edge, Safari (2 phiên bản gần nhất) đạt E2E P0 |
| Tiếp cận | Không vi phạm Serious/Critical; luồng P0 dùng được bằng bàn phím |
| Vận hành | Kill switch đã diễn tập; cảnh báo & runbook kiểm chứng |

---

## 8.0 Tiêu chí tạm dừng và tiếp tục (§5.8)

| Loại | Điều kiện |
|---|---|
| **Tạm dừng** | (1) Build không khởi động hoặc smoke thất bại; (2) phát hiện **rò rỉ liên người dùng hoặc nội dung vào log** (dừng ngay mọi thử nghiệm dùng dữ liệu thật, escalate); (3) ≥ 30% test P0 thất bại; (4) môi trường staging/LLM/Embedding không khả dụng > 4 giờ làm việc; (5) tỷ lệ lỗi chặn > 20% trong cùng một bản build; (6) dùng PDF chưa được duyệt. |
| **Tiếp tục** | Lỗi nguyên nhân đã sửa và có bản build mới; smoke + REG-003 đạt; môi trường ổn định ≥ 1 giờ; QA Lead và Tech Lead đồng ý. |

---

## 9.0 Sản phẩm bàn giao (§5.9)

| Sản phẩm | Khi nào | Người giao |
|---|---|---|
| Test Plan này (cập nhật theo phiên bản) | Cuối S0, rà soát cuối S2/S4 | QA |
| Test Design Specification & Test Case (tự động trong repo + thủ công) | Theo sprint | QA/Dev |
| Test Data (PDF thử + manifest, bộ câu hỏi chuẩn) | S0–S4 | QA/PO |
| Ma trận truy vết (mục 16) cập nhật | Mỗi sprint | QA |
| Test Log / báo cáo CI | Mỗi lần chạy | CI |
| Incident/Defect Report | Liên tục | QA/Dev |
| Báo cáo chất lượng RAG | Mỗi lần hiệu chỉnh; trước release | AI/BE + QA |
| Báo cáo hiệu năng staging (`performance.md` cập nhật) | S4–S5 | QA/DevOps |
| Báo cáo bảo mật (`security_review.md` cập nhật) | S5 | QA/Bảo mật |
| Báo cáo tiếp cận | S5 | QA |
| Test Summary Report + đề xuất Go/No-Go | Cuối S5 | QA Lead |

---

## 10.0 Các tác vụ kiểm thử (§5.10)

Ánh xạ tới workstream G của [Implement_Plan.md](../implement/Implement_Plan.md) và task chi tiết trong [tasks/](../implement/tasks/README.md).

| ID | Tác vụ | Tương ứng | Phụ thuộc | Sprint |
|---|---|---|---|---|
| TT-01 | Chốt phạm vi, mục tiêu, tiêu chí; thu thập PDF thử và bắt đầu bộ câu hỏi chuẩn | OQ-009 | — | S0 |
| TT-02 | Dựng CI: lint, unit, API contract, quét secret/SCA | A1, G1 | TT-01 | S0–S1 |
| TT-03 | Unit test nghiệp vụ (≥ 70%) | G1 | B1, D2…D5 | S1–S4 |
| TT-04 | Test tích hợp Postgres+MinIO | G2 | A3, A4, C1 | S2–S4 |
| TT-05 | Test cô lập người dùng | G3 | A4, B2, B3 | S2 + kiểm S4 |
| TT-06 | Test không rò nội dung | G4 | A6, B10 | S4 |
| TT-07 | Test trích dẫn & xóa | G5 | D5, B11 | S4 |
| TT-08 | Contract test OpenAPI (API-001…039) | API | B3…B10 | S2–S4 |
| TT-09 | Đánh giá chất lượng RAG & hiệu chỉnh | D7, D8 | OQ-009 | S4 |
| TT-10 | E2E Playwright luồng P0 | G6 | E2…E8 | S4–S5 |
| TT-11 | Hiệu năng trên staging | G7, C7 | A7 | S5 |
| TT-12 | Rà soát bảo mật + red-team LLM thật | G8 | A7 | S5 |
| TT-13 | Tiếp cận & trình duyệt | E12 | E6 | S5 |
| TT-14 | Diễn tập kill switch, cảnh báo, runbook | F2, A7 | B9 | S5 |
| TT-15 | UAT với Lan, Minh, Hà | — | TT-10 | S5 |
| TT-16 | Test Summary Report, Go/No-Go | — | tất cả | Cuối S5 |
| TT-17 | Test P1 (US-104, 204, 205, 403, 502) | — | — | S6 |

---

## 11.0 Nhu cầu môi trường (§5.11)

| Môi trường | Mục đích | Cấu hình |
|---|---|---|
| **CI** | Unit, API, tích hợp (testcontainers), quét SCA/secret | Container Postgres 16 + pgvector, MinIO; adapter giả |
| **Dev (Compose)** | Phát triển & smoke | web, api, worker, Postgres, MinIO; FakeLLM/FakeEmbedding; AuthProvider dev |
| **Staging** | E2E, hiệu năng, RAG, bảo mật, UAT | Giống production: tiến trình worker riêng, nginx/WAF thật, LLM + embedding thật (khi được duyệt), IdP thật hoặc mô phỏng `[TBD: OQ-014]` |
| **Production thử nghiệm** | Chỉ smoke sau triển khai, giám sát | Sau Go/No-Go và phê duyệt pháp chế |

**Dữ liệu:** PDF thử đã duyệt (hợp lệ nhiều kích cỡ/trang, tiếng Việt/Anh, bảng biểu, hỏng, mật khẩu, quét, độc hại, vượt giới hạn); ≥ 2 tài khoản thử + vai trò `evaluator`, `ops`; bộ câu hỏi chuẩn.

**Trình duyệt/thiết bị:** Chrome, Edge, Safari (2 phiên bản gần nhất); viewport 320–2560px.

**Ràng buộc đã biết:** môi trường dev hiện tại không có Docker/Postgres (xem security_review.md) → tích hợp thật phải chạy ở CI/staging.

---

## 12.0 Trách nhiệm (§5.12)

| Vai trò | Trách nhiệm |
|---|---|
| QA Lead `[TBD: OQ-001]` | Sở hữu Test Plan, báo cáo tổng kết, đề xuất Go/No-Go |
| QA/Automation | API/E2E/hồi quy, dữ liệu thử, báo cáo lỗi, hiệu năng |
| Dev FE/BE/AI | Unit/tích hợp, sửa lỗi, fault injection, cung cấp adapter giả |
| DevOps | CI, staging, giám sát, đo hiệu năng |
| PO | Phạm vi P0, phê duyệt AC, bộ câu hỏi chuẩn (OQ-009/010) |
| Lan (đại diện người dùng) | Viết đáp án tham chiếu, UAT |
| Minh | UAT báo cáo MET, ngưỡng KPI (OQ-005) |
| Hà (pháp chế/bảo mật) | Duyệt dữ liệu thử, nhà cung cấp, thông báo, vòng đời dữ liệu; pentest |

---

## 13.0 Nhân sự và đào tạo (§5.13)

- Đội ~4 người theo giả định Implement Plan 1.3 (1 FE, 2 BE/AI, 1 QA/DevOps bán thời gian) `[TBD: OQ-006]` → **khuyến nghị** có thêm năng lực QA/automation hoặc xác nhận QA bán thời gian đủ cho workstream G.
- Đào tạo: Playwright & axe-core; k6; cách chấm bộ câu hỏi chuẩn (thang điểm thống nhất giữa người chấm); xử lý dữ liệu nhạy cảm; vận hành kill switch.

---

## 14.0 Lịch kiểm thử (§5.14)

Bám lộ trình sprint của Implement Plan (mỗi sprint 2 tuần; S0 = 1 tuần) [Đề xuất]:

| Sprint | Hoạt động kiểm thử | Cổng |
|---|---|---|
| S0 | TT-01, TT-02; chốt hợp đồng API; bắt đầu bộ câu hỏi chuẩn | CI xanh |
| S1 | Unit nền tảng; smoke walking skeleton | Tải PDF → có chunk |
| S2 | Test tài liệu/thông báo/cô lập (API-001…014, SEC-001…005); tích hợp; E2E-001/002/004/008 | **Cổng 2:** chốt nhà cung cấp & xác thực |
| S3 | Test hỏi đáp SSE (API-015…027); E2E-003/005…007/012 | Hỏi→stream→chip→nguồn |
| S4 | G1…G5, RAG, telemetry, báo cáo MET, hiệu chỉnh ngưỡng | **Cổng 3:** duyệt ngưỡng chất lượng |
| S5 | Hiệu năng/bảo mật staging, tiếp cận, trình duyệt, kill switch, UAT, đóng lỗi | **Cổng 4:** Go/No-Go |
| S6 | Test P1; hồi quy đầy đủ | Release R2 |

**Chu kỳ chạy:** Smoke + Unit + API mỗi PR; E2E mỗi build staging; RAG mỗi lần đổi prompt/ngưỡng; hiệu năng & bảo mật đầy đủ ở S5 và trước mỗi release.

---

## 15.0 Rủi ro và dự phòng (§5.15)

### 15.1 Rủi ro kiểm thử

Điểm = Khả năng × Tác động (1–5).

| ID | Rủi ro | KN | TĐ | Điểm | Giảm thiểu / Dự phòng | Truy vết |
|---|---|---|---|---|---|---|
| RISK-01 | Rò rỉ chéo người dùng / vào log | 2 | 5 | 10 | RLS + G3/G4 chạy mỗi PR; dừng ngay theo mục 8.0 | RSK-I5 |
| RISK-02 | Câu trả lời bịa / trích dẫn giả | 3 | 5 | 15 | Bộ RAG, loại nhãn không hợp lệ, ngưỡng “không tìm thấy”, đánh giá thủ công mẫu | RSK-001, RSK-I3 |
| RISK-03 | Chất lượng truy xuất kém với tiếng Việt / bố cục phức tạp | 3 | 4 | 12 | Embedding đa ngữ; D7/D8 sớm; ghi nhận giới hạn | RSK-I1 |
| RISK-04 | Kết quả trên adapter giả bị hiểu nhầm là kết quả thật | 4 | 4 | 16 | Ghi rõ phạm vi bằng chứng trong mọi báo cáo; **bắt buộc** chạy staging thật trước Go/No-Go | performance.md |
| RISK-05 | Chưa có đáp án/bộ câu hỏi chuẩn (OQ-009) | 3 | 5 | 15 | Thu thập từ S0 với Lan; không công bố “đạt” khi chưa có bộ được duyệt | OQ-009 |
| RISK-06 | Pháp chế chậm duyệt → không thể dùng dữ liệu thật/LLM thật | 4 | 4 | 16 | Dùng PDF thử; phối hợp Hà từ S0; ghi “chưa thể kết luận” | RSK-I4 |
| RISK-07 | Tốc độ trả lời > 5s với LLM thật | 3 | 3 | 9 | Đo từ S3; embed song song; giảm k | RSK-I2 |
| RISK-08 | Prompt injection qua PDF với mô hình thật | 3 | 3 | 9 | SEC-006/007/019; rào cản cấu trúc | RSK-I6 |
| RISK-09 | Môi trường staging chậm/thiếu (không Docker/Postgres ở dev) | 3 | 4 | 12 | Ưu tiên A7 sớm; dùng CI + testcontainers | A7 |
| RISK-10 | Phạm vi trượt (P1/P2 chen vào R1) | 3 | 3 | 9 | Khóa phạm vi P0 sau S0 | RSK-I7 |
| RISK-11 | Mơ hồ phạm vi do OQ-008/010/014 chưa chốt | 3 | 3 | 9 | Test đọc giới hạn từ `/config`, không hard-code; giữ US-301/302 ở P0 | OQ-008/010/014 |
| RISK-12 | Test E2E/SSE không ổn định (flaky) | 3 | 3 | 9 | Fake LLM tất định cho E2E; retry có kiểm soát; theo dõi tỷ lệ flaky | — |
| RISK-13 | Đội nhỏ, QA bán thời gian | 3 | 3 | 9 | Tự động hóa tối đa phần rủi ro cao; review chéo | RSK-I8 |
| RISK-14 | Dừng sinh không hoạt động với nhiều bản sao API | 2 | 3 | 6 | OPS-009; định tuyến dính | API 3.4.3 |

### 15.2 Kế hoạch dự phòng
- Trễ môi trường staging → ưu tiên CI + testcontainers; hoãn PERF/RAG thật nhưng **không** tuyên bố đạt.
- Trễ bộ câu hỏi chuẩn → dùng bộ tạm do QA + Lan, đánh dấu “chưa duyệt”.
- Lỗi chặn muộn → cắt giảm test P1/P2 trước; **không** cắt REG-003 và SEC-001…003.

---

## 16.0 Truy vết yêu cầu → kiểm thử

| Story / Yêu cầu | AC | Unit | API | Tích hợp | E2E | UAT | Khác |
|---|---|---|---|---|---|---|---|
| US-101 Tải PDF | AC-001 | UT-011 | API-004…010 | INT-001, 003 | E2E-001, 002, 008 | UAT-001 | SEC-008, PERF-003 |
| US-102 Danh sách/trạng thái | — | UT-001 | API-011, 012 | INT-001 | E2E-001, 003 | UAT-002 | UI-003 |
| US-103 Xóa | — | — | API-013 | INT-006 | E2E-001, 012 | UAT-003 | SEC-018 |
| US-201 Đặt câu hỏi | AC-002 | UT-002 | API-014…016, 018, 020…022 | INT-007 | E2E-001, 004, 007, 010 | UAT-004 | PERF-001/002, UI-005 |
| US-202 Có căn cứ/“không tìm thấy” | AC-003 | UT-004, 012 | API-019 | — | E2E-005 | UAT-004 | RAG-001, 003, 006 |
| US-203 Nhiều PDF | — | — | API-023 | INT-005 | E2E-006 | UAT-005 | RAG-002, 007 |
| US-301 Trích dẫn | — | UT-005 | API-015, 024 | — | E2E-001 | UAT-006 | RAG-008 |
| US-302 Xem đoạn gốc | — | — | API-025…027 | INT-006 | E2E-001, 012 | UAT-006 | ACC-005 |
| US-401 Thông báo dữ liệu | — | — | API-001…003, 009 | — | E2E-001 | UAT-007, 010 | — |
| US-402 Cô lập | — | — | mọi endpoint (404) | INT-004, 005 | E2E-009, 011 | UAT-008 | SEC-001…005 |
| US-501 MET-001/002 | AC-004 | UT-009, 010 | API-028…030 | — | E2E-013 | UAT-009 | OPS-008 |
| PRD 4.2 Trạng thái lỗi | — | — | API-021, 033 | INT-010 | E2E-003, 004, 007…010 | — | OPS-002…005 |
| PRD 5.1 Hiệu năng | — | — | — | — | — | — | PERF-001…009 |
| PRD 5.1 Bảo mật/dữ liệu | — | UT-006, 008 | API-035 | INT-004 | — | UAT-010 | SEC-001…019 |
| PRD 5.1 Vận hành | — | — | API-031, 032 | — | E2E-010 | — | OPS-001…009 |
| WCAG 2.1 AA (PRD 4.1) | — | — | — | — | — | — | ACC-001…007 |
| US-104/204/205/403/502 (P1) | — | — | API-036…039 | — | E2E-014 | — | S6 |

> Mọi AC của story P0 đều có ít nhất một test tự động; ngoại lệ phải ghi lý do trong ma trận khi triển khai.

---

## 17.0 Câu hỏi mở ảnh hưởng kế hoạch kiểm thử

| ID | Nội dung | Ảnh hưởng | Cách xử lý tạm |
|---|---|---|---|
| OQ-005 | KPI, baseline MET-001, vị trí `task_marked_done` | E2E-013, UAT-009 | Báo cáo ghi “chưa thể kết luận” |
| OQ-008 | Giới hạn PDF, OCR, ngôn ngữ | API-007/008, PERF-003, RAG-004, SEC-008 | Đọc giới hạn từ `/config` |
| OQ-009 | Bộ câu hỏi chuẩn & ngưỡng đạt | Mục 6.6, OBJ-003 | Bộ tạm do QA + Lan |
| OQ-010 | Nguồn dẫn có thuộc P0 | US-301/302 | Giữ ở P0 |
| OQ-011 | Hiệu năng/sẵn sàng chính thức; mức WCAG | 6.8, 6.9 | Dùng ngưỡng đề xuất |
| OQ-012/013 | Vị trí xử lý, thời hạn lưu/xóa, nhà cung cấp | SEC-018, UAT-010, môi trường staging | Chỉ PDF thử đã duyệt |
| OQ-014 | Cơ chế xác thực | SEC-004/005, E2E-009 | AuthProvider dev (JWT) |
| OQ-001/006 | Chủ sở hữu, quy mô đội | Mục 12–13 | Giả định Implement Plan 1.3 |

---

## 18.0 Phê duyệt (§5.16)

| Vai trò | Họ tên | Chữ ký | Ngày |
|---|---|---|---|
| QA Lead | `[TBD]` | | |
| Product Owner | `[TBD]` | | |
| Tech Lead | `[TBD]` | | |
| Pháp chế / Bảo mật (Hà) | `[TBD]` | | |
| Nhà bảo trợ / Chủ nghiệp vụ | `[TBD]` | | |

---

## Phụ lục A — Ánh xạ mục lục IEEE 829 ↔ tài liệu này

| IEEE 829 | Tài liệu này |
|---|---|
| 5.1 Định danh | 1.0 |
| 5.2 Giới thiệu | 2.0 |
| 5.3 Hạng mục kiểm thử | 3.0 |
| 5.4 Tính năng cần kiểm thử | 4.0 |
| 5.5 Tính năng không kiểm thử | 5.0 |
| 5.6 Phương pháp | 6.0 |
| 5.7 Tiêu chí đạt/không đạt | 7.0 |
| 5.8 Tạm dừng/tiếp tục | 8.0 |
| 5.9 Sản phẩm bàn giao | 9.0 |
| 5.10 Tác vụ kiểm thử | 10.0 |
| 5.11 Môi trường | 11.0 |
| 5.12 Trách nhiệm | 12.0 |
| 5.13 Nhân sự & đào tạo | 13.0 |
| 5.14 Lịch | 14.0 |
| 5.15 Rủi ro & dự phòng | 15.0 |
| 5.16 Phê duyệt | 18.0 |
| (Bổ sung) Truy vết, câu hỏi mở | 16.0, 17.0 |
