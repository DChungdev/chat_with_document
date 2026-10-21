# Kế hoạch phát triển (Implementation Plan) — Công cụ “Chat với tài liệu”

**Số tài liệu / Phiên bản:** IMPL-DOCCHAT-001 / v0.1 — Bản nháp
**Ngày lập:** 2026-10-21
**Nguồn đầu vào:** [SAD.md](../design/SAD.md) (`SAD-DOCCHAT-001` v0.1), [User_Stories.html](../requirements/User_Stories.html) (`US-DOCCHAT-001` v0.1), prototype UI trong [docs/design/UI_UX_design/](../design/UI_UX_design/)

> **Quy ước:** **[Đề xuất]** = do kế hoạch này đưa ra, cần PO/Tech Lead xác nhận. **[TBD: OQ-xxx]** = câu hỏi mở kế thừa từ BRD/PRD, **chưa phải quyết định**. Ước lượng là mức độ lớn (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) và chỉ mang tính tham khảo cho đến khi chốt đội ngũ (`OQ-006`).

---

## 1. Mục tiêu và phạm vi

### 1.1 Mục tiêu
Đưa MVP “Chat với tài liệu” vào thử nghiệm: người dùng tải PDF, hỏi bằng ngôn ngữ tự nhiên, nhận câu trả lời streaming **có trích dẫn kiểm chứng được**, và Minh có số liệu MET-001/MET-002 để quyết định đầu tư tiếp.

### 1.2 Phạm vi theo mức ưu tiên

| Mức | Story | Release |
|---|---|---|
| **P0** (bắt buộc MVP) | US-101, 102, 103, 201, 202, 203, 301, 302, 401, 402, 501 | R1 (MVP thử nghiệm) |
| **P1** (nên có) | US-104, 204, 205, 403, 502 | R2 |
| **P2** (nếu còn nguồn lực) | US-105, 206, 303 | R3 / backlog |

**Ngoài phạm vi (SAD 1.2):** định dạng ngoài PDF, OCR, đồng bộ kho ngoài, báo cáo tự động, mobile-native/offline, workspace chia sẻ.

### 1.3 Giả định lập kế hoạch [Đề xuất]
- Đội ~4 người: 1 FE, 2 BE/AI, 1 QA/DevOps (bán thời gian). Sprint 2 tuần. **[TBD: OQ-006]**
- Ngăn xếp theo SAD 2.2: React + TS + Vite; FastAPI (Python 3.12); worker Python; PostgreSQL 16 + pgvector; S3-compatible; LLM/Embedding sau Port.
- Dữ liệu thật **chỉ** dùng sau khi pháp chế duyệt (SAD 3.5); trước đó dùng tài liệu thử đã duyệt.

---

## 2. Chiến lược triển khai

1. **Walking skeleton trước:** dựng lát cắt mỏng chạy end-to-end (tải PDF → chunk → hỏi → trả lời có nguồn) với adapter giả lập, rồi mới thay bằng nhà cung cấp thật. Giúp lộ rủi ro tích hợp sớm.
2. **Hexagonal ngay từ đầu:** domain thuần + port/adapter (`LLMPort`, `EmbeddingPort`, `VectorStorePort`, `FileStoragePort`, `AuthProvider`). Nhờ vậy các `[TBD]` (OQ-012/013/014) **không chặn** phát triển; chỉ chặn việc bật dữ liệu thật.
3. **Cô lập và quyền riêng tư là “làm từ đầu”, không vá sau:** `user_id` bắt buộc trong repository + RLS, bộ lọc log allow-list có từ sprint đầu.
4. **Hiệu chỉnh bằng dữ liệu:** ngưỡng liên quan, k, chunking chỉnh dựa trên bộ câu hỏi chuẩn (`OQ-009`) trong một sprint riêng trước thử nghiệm.
5. **Cấu hình thay vì hard-code:** giới hạn PDF, độ dài câu hỏi, top-k, ngưỡng… đọc từ `app_config` (SAD mục 6).

---

## 3. Cấu trúc mã nguồn đề xuất [Đề xuất]

```
chat_with_document/
├── apps/
│   ├── web/                 # React SPA
│   ├── api/                 # FastAPI: api.http + application.*
│   └── worker/              # ingestion worker
├── packages/
│   └── core/                # domain, retrieval, answering, ports (dùng chung api/worker)
├── infra/                   # adapters: persistence, storage, llm, embedding, auth, observability
├── db/migrations/           # schema SQL + pgvector + RLS
├── deploy/                  # docker-compose, manifests
└── docs/
```

---

## 4. Phân rã công việc (Work Breakdown)

### Workstream A — Nền tảng & hạ tầng (DevOps/BE)

| ID | Công việc | Cỡ | Phụ thuộc |
|---|---|---|---|
| A1 | Khởi tạo monorepo, lint/format, pre-commit, CI (build + test) | M | — |
| A2 | Docker Compose dev: web, api, worker, Postgres+pgvector, MinIO | M | A1 |
| A3 | Migration lược đồ SQL (users, documents, chunks, conversations, messages, citations, feedback, telemetry_events, audit_log, app_config) theo Database_Design_SQL | L | A2 |
| A4 | Bật pgvector + chỉ mục HNSW; Row-Level Security + cơ chế đặt `app.user_id` mỗi giao dịch (ADR-07) | M | A3 |
| A5 | Quản lý cấu hình/secret; `app_config` + feature flag `qa_enabled` | S | A3 |
| A6 | Logging cấu trúc JSON với **allow-list trường**; metrics Prometheus; OpenTelemetry cơ bản | M | A1 |
| A7 | Môi trường staging + pipeline triển khai | L | A2 |

### Workstream B — Backend lõi (BE)

| ID | Công việc | Cỡ | Phụ thuộc |
|---|---|---|---|
| B1 | Domain: `Document`, `Chunk`, `Conversation`, `Message`, `Citation` + quy tắc trạng thái | M | A1 |
| B2 | Định nghĩa Ports + repository PostgreSQL (luôn có `user_id`) | L | A3, B1 |
| B3 | `AuthProvider` + middleware JWT; adapter dev giả lập; trả `404` khi truy cập tài nguyên người khác | M | B2 |
| B4 | API tài liệu: `POST/GET/DELETE /api/v1/documents`, kiểm tra loại tệp (`%PDF-`), kích thước, `Idempotency-Key`, trả `202` ≤ 2s | L | B2, B3, C1 |
| B5 | Lỗi theo RFC 7807, rate limit theo người dùng | S | B4 |
| B6 | `application.compliance`: xác nhận thông báo dữ liệu; chặn upload khi chưa xác nhận | M | B3 |
| B7 | API hội thoại: tạo hội thoại, `POST …/messages` (SSE: `token`, `citations`, `done`, `error`); lưu câu hỏi **trước** khi gọi dịch vụ ngoài | L | D1–D4 |
| B8 | `GET /api/v1/citations/{id}` (trả `valid=false` nếu tài liệu đã xóa) | S | B7 |
| B9 | Kill switch: `qa_enabled=false` → `503 QA_DISABLED` | S | A5 |
| B10 | Telemetry: `POST /telemetry/events` + kiểm allow-list thuộc tính, băm `user_id` có muối | M | A3 |
| B11 | Xóa tài liệu: cascade chunk, xóa PDF gốc, đánh dấu citation `valid=false`, ghi audit | M | B4, C1 |

### Workstream C — Ingestion (BE/AI)

| ID | Công việc | Cỡ | Phụ thuộc |
|---|---|---|---|
| C1 | `FileStoragePort` + adapter S3/MinIO (mã hóa SSE, khóa `user_id/doc_id`) | M | A2 |
| C2 | Hàng đợi ingest trên PostgreSQL (`FOR UPDATE SKIP LOCKED`), retry, chạy lại idempotent | L | A3 |
| C3 | Trích xuất văn bản theo trang (`pypdf`/`pdfminer.six`); PDF quét/hỏng/mật khẩu → `status=error` + `error_code` | L | C2 |
| C4 | Chunking (~800 token, chồng 100) giữ `page_start`/`page_end` | M | C3 |
| C5 | `EmbeddingPort` + adapter (giả lập → thật), embed theo lô, retry/timeout/circuit breaker | L | B2 |
| C6 | Ghi `chunks` + embedding, chuyển `status=ready`; xử lý từng tệp độc lập (một tệp lỗi không ảnh hưởng tệp khác) | M | C4, C5 |
| C7 | Đo hiệu năng: PDF mục tiêu ≤ 60s | M | C6 |

### Workstream D — RAG: truy xuất & trả lời (AI/BE)

| ID | Công việc | Cỡ | Phụ thuộc |
|---|---|---|---|
| D1 | `VectorStorePort` + adapter pgvector: top-k, lọc `user_id` + `documentIds` + tài liệu `ready` | L | A4, C6 |
| D2 | `retrieval`: ngưỡng tương đồng tối thiểu, dựng ngữ cảnh có nhãn `[S1]…[Sn]` | M | D1 |
| D3 | Nhánh “không tìm thấy”: không còn chunk đạt ngưỡng → trả ngay, `grounded=false`, **không gọi LLM** (ADR-04) | S | D2 |
| D4 | `LLMPort` + adapter Claude (streaming), prompt “chỉ dùng nguồn”, nội dung PDF tách khối dữ liệu (chống prompt injection), timeout/retry/circuit breaker | L | D2 |
| D5 | Ghép trích dẫn: ánh xạ `[Sx]` → citation (documentId, tên tệp, trang, snippet); **loại nhãn không tồn tại** | M | D4 |
| D6 | Xử lý ngắt kết nối/dừng: message `interrupted`/`stopped`, giữ phần đã nhận; `POST …/stop` | M | B7 |
| D7 | Bộ câu hỏi chuẩn + script đánh giá (độ chính xác, tỷ lệ trích dẫn hợp lệ, tỷ lệ “không tìm thấy” đúng) | L | D5 |
| D8 | Hiệu chỉnh ngưỡng / k / chunking theo D7 | M | D7 |

### Workstream E — Frontend (FE)

Bám prototype SCR-01…SCR-09 trong `docs/design/UI_UX_design/`.

| ID | Công việc | Màn hình | Cỡ | Phụ thuộc |
|---|---|---|---|---|
| E1 | Khởi tạo SPA, routing, API client, design tokens, theme sáng/tối | — | M | A1 |
| E2 | Màn chào + thông báo dữ liệu, checkbox, nút “Thông báo dữ liệu” trên header | SCR-01 | M | B6 |
| E3 | Màn chính rỗng + khu vực tải lên + validate phía client | SCR-02 | M | B4 |
| E4 | Danh sách tài liệu: trạng thái (biểu tượng + chữ), polling, lỗi riêng từng tệp, menu ⋯ | SCR-03 | L | B4 |
| E5 | Hộp thoại xác nhận xóa | SCR-06 | S | B11 |
| E6 | Khung chat: gửi/Enter/Shift+Enter, SSE client qua `fetch` stream, chỉ báo đang tạo, nhãn AI cố định | SCR-04 | XL | B7 |
| E7 | Chip trích dẫn `tên tệp · tr.N` + Panel nguồn (bên phải; bottom sheet < 1024px; Esc trả focus) | SCR-04/05 | L | B8 |
| E8 | Trạng thái lỗi: Interrupted / Failed / “Không tìm thấy”; banner kill switch | SCR-04/08 | M | E6 |
| E9 | Overlay hết phiên, giữ bản nháp câu hỏi | SCR-07 | M | B3 |
| E10 | `TelemetryClient` + sự kiện (`data_notice_accepted`, `upload_*`, `citation_opened`, `task_marked_done`…) | — | M | B10 |
| E11 | Báo cáo đánh giá MVP cho Minh (MET-001/002) | SCR-09 | L | F1 |
| E12 | Tiếp cận (WCAG, bàn phím, focus), kiểm thử trình duyệt Chrome/Edge/Safari | — | M | E6 |

### Workstream F — Đo lường (BE/FE)

| ID | Công việc | Cỡ | Phụ thuộc |
|---|---|---|---|
| F1 | Truy vấn SQL tính MET-001/MET-002 từ `telemetry_events` + endpoint báo cáo (vai trò `evaluator`, chỉ số tổng hợp, không nội dung) | L | B10 |
| F2 | Dashboard cảnh báo vận hành: p95 token đầu > 5s, `answer_failed` cao, tồn đọng hàng đợi, lỗi LLM | M | A6 |

### Workstream G — Chất lượng & bảo mật (QA)

| ID | Công việc | Cỡ |
|---|---|---|
| G1 | Unit test domain/retrieval/answering (mục tiêu ≥ 70% logic nghiệp vụ) | L |
| G2 | Test tích hợp với Postgres+MinIO (testcontainers) | L |
| G3 | **Test cô lập:** user A không thấy/truy vấn/nhận trích dẫn từ tài liệu của B (US-402) | M |
| G4 | Test không rò nội dung vào log/telemetry (quét log tự động) | M |
| G5 | Test trích dẫn: 0 trích dẫn tới trang không tồn tại; test xóa tài liệu → citation `valid=false` | M |
| G6 | E2E (Playwright) các luồng P0: Lan tải → hỏi → xem nguồn → xóa | L |
| G7 | Test hiệu năng: token đầu ≤ 5s p95 (≤ 10 PDF), xử lý PDF ≤ 60s | M |
| G8 | Rà soát bảo mật: prompt injection, tệp độc hại, rate limit, secret | M |

---

> **Chi tiết từng task:** mỗi mã công việc ở trên có file riêng trong [tasks/](tasks/README.md).

## 5. Lộ trình theo sprint [Đề xuất]

Mốc thời gian tính theo tuần kể từ ngày khởi động (S0 = tuần 0). Mọi sprint kết thúc bằng bản chạy được và demo.

| Sprint | Mục tiêu | Nội dung chính | Story đạt được | Kết quả demo / Exit |
|---|---|---|---|---|
| **S0** (1 tuần) | Chuẩn bị | Chốt đội, môi trường, ADR còn mở; A1, A2; thống nhất hợp đồng API; **bắt đầu thu thập bộ câu hỏi chuẩn (OQ-009)** | — | Repo + CI xanh, `docker compose up` chạy |
| **S1** | Walking skeleton | A3–A6, B1–B3, C1–C4, E1; adapter embedding/LLM **giả lập** | — | Tải PDF → có chunk trong DB (qua API) |
| **S2** | Tải & quản lý tài liệu | B4–B6, B11, C5–C6, E2–E5, E9; dùng embedding thật nếu được duyệt | US-101, 102, 103, 401, 402 (phần BE/UI) | Lan tải nhiều PDF, thấy trạng thái, xóa được; thông báo dữ liệu hoạt động |
| **S3** | Hỏi đáp có nguồn | D1–D5, B7–B9, E6–E8 | US-201, 202, 203, 301, 302 | Hỏi → stream → chip trích dẫn → panel nguồn; “không tìm thấy” đúng |
| **S4** | Đo lường & hiệu chỉnh | B10, E10, F1, E11, D7–D8, G1–G5, C7 | US-501 + cô lập/độ tin cậy | Báo cáo MET-001/002 chạy trên dữ liệu thử; ngưỡng đã hiệu chỉnh |
| **S5** | Cứng hóa & UAT | G6–G8, E12, A7, F2, runbook, kill switch drill; sửa lỗi | Hoàn tất **R1 (P0)** | Đạt Exit Criteria R1 (mục 7); sẵn sàng thử nghiệm nội bộ |
| **S6** | P1 | US-104, 204, 205, 502, 403 (BE + UI nhật ký) | P1 | Release **R2** |
| **S7+** | P2 / backlog | US-105, 206, 303 | P2 | Release **R3** theo nguồn lực |

> Tổng R1 ≈ 5–6 sprint (10–12 tuần) với giả định ở 1.3. Cần xác nhận lại sau S1 dựa trên tốc độ thực tế (velocity).

### 5.1 Đường găng (critical path)
`A3 → B2 → C2/C3/C4 → C5 → C6 → D1 → D2 → D4 → D5 → B7 → E6 → E7`
Rủi ro lớn nhất trên đường găng: **chất lượng truy xuất** (D7/D8) và **tích hợp streaming FE/BE** (E6).

---

## 6. Truy vết Story → Công việc

| Story | Ưu tiên | Công việc chính | Sprint |
|---|---|---|---|
| US-101 Tải PDF | P0 | B4, B5, C1–C6, E3, E4 | S2 |
| US-102 Danh sách + trạng thái | P0 | B4, C6, E4 | S2 |
| US-103 Xóa PDF | P0 | B11, E5 | S2 |
| US-201 Đặt câu hỏi | P0 | B7, B9, E6, E8 | S3 |
| US-202 Trả lời có căn cứ / “không tìm thấy” | P0 | D2, D3, D4, D8 | S3–S4 |
| US-203 Tổng hợp nhiều PDF | P0 | D1 (đa tài liệu), D5, E7 | S3 |
| US-301 Trích dẫn | P0 | D5, E7 | S3 |
| US-302 Xem đoạn gốc | P0 | B8, E7 | S3 |
| US-401 Thông báo dữ liệu | P0 | B6, E2 | S2 |
| US-402 Cô lập người dùng | P0 | A4, B2, B3, E9, G3 | S1–S2, kiểm S4 |
| US-501 MET-001/002 | P0 | B10, E10, F1, E11 | S4 |
| US-104 Chọn tài liệu cho câu hỏi | P1 | D1 (lọc `documentIds`), E4/E6 | S6 |
| US-204 Hỏi nối tiếp | P1 | B7 (ngữ cảnh hội thoại), D4, E6 | S6 |
| US-205 Dừng / tạo lại | P1 | D6, E6/E8 | S6 *(nền tảng `interrupted` làm ở S3)* |
| US-403 Nhật ký tải/xóa | P1 | Audit (B11), API + UI nhật ký (mới) | S6 |
| US-502 Đánh giá câu trả lời | P1 | `feedback` API, E6 | S6 |
| US-105 Kéo-thả | P2 | E3 | S7+ |
| US-206 Sao chép / xuất | P2 | E6 | S7+ |
| US-303 Mở PDF tại trang | P2 | E7 + endpoint tệp | S7+ |

---

## 7. Định nghĩa Hoàn thành (DoD) và Tiêu chí thoát

### 7.1 DoD cho mỗi story
- Mã đã review, CI xanh (lint, unit, integration).
- Đáp ứng mọi Given/When/Then của story; có test tự động cho nhánh chính và nhánh lỗi.
- Không có nội dung tài liệu/câu hỏi trong log/telemetry (G4 qua).
- Mọi truy vấn có `user_id`; test cô lập liên quan qua.
- UI khớp prototype tương ứng; dùng bàn phím và trạng thái không chỉ dựa vào màu.
- Cập nhật tài liệu (API/DB) nếu thay đổi.

### 7.2 Tiêu chí thoát R1 (MVP thử nghiệm)
| Hạng mục | Ngưỡng [Đề xuất] |
|---|---|
| Story P0 | 11/11 đạt DoD |
| Token đầu (≤ 10 PDF) | ≤ 5s ở p95 |
| Xử lý PDF | ≤ 60s |
| Câu trả lời có trích dẫn hợp lệ | ≥ 90%; **0** trích dẫn tới trang không tồn tại |
| Rò rỉ liên người dùng | **0** (G3) |
| Nội dung trong log/telemetry | **0** (G4) |
| Bao phủ logic nghiệp vụ | ≥ 70% |
| Vận hành | Có giám sát, cảnh báo, kill switch đã diễn tập, runbook |
| Pháp lý | Pháp chế duyệt thông báo dữ liệu + nhà cung cấp LLM/Embedding (OQ-012/013) trước khi dùng dữ liệu thật |

---

## 8. Câu hỏi mở chặn và cách xử lý

| ID | Nội dung | Ảnh hưởng | Cần chốt trước | Cách giảm thiểu trong lúc chờ |
|---|---|---|---|---|
| OQ-012 / OQ-013 | Vị trí xử lý dữ liệu, thời hạn lưu/xóa, nhà cung cấp LLM/Embedding | Chọn adapter thật; nội dung SCR-01; vòng đời dữ liệu | Bật dữ liệu thật; chọn embedding ở S2 | Adapter giả lập/khóa thử; chỉ dùng tài liệu thử đã duyệt; thời hạn lưu cấu hình được |
| OQ-014 | Cơ chế xác thực | `AuthProvider`, SCR-07 | S2 | Adapter JWT dev; giao diện trung lập |
| OQ-008 | Giới hạn PDF, OCR, ngôn ngữ | Giới hạn upload, chọn mô hình embedding đa ngữ (tiếng Việt) | S1 (chọn embedding) | Giới hạn trong `app_config`; PDF quét báo lỗi rõ (ADR-09) |
| OQ-009 | Bộ câu hỏi chuẩn & ngưỡng chất lượng | D7/D8, US-202 | Bắt đầu S0, xong trước S4 | Thu thập sớm cùng Lan/PO |
| OQ-010 | Nguồn dẫn có thuộc P0 không | Phạm vi US-301/302 | S2 | **Giữ ở P0** (cốt lõi độ tin cậy, ADR-03) cho đến khi PO xác nhận khác |
| OQ-005 | Vị trí `task_marked_done`, hình thức báo cáo | E10, E11, F1 | S3 | Dựng báo cáo web đơn giản (SCR-09) |
| OQ-006 | Quy mô & nhân sự đội | Toàn bộ lộ trình | S0 | Lộ trình tính lại sau S1 |
| OQ-011 | Yêu cầu hiệu năng/sẵn sàng chính thức | G7, A7 | S4 | Dùng ngưỡng đề xuất ở 7.2 |

---

## 9. Rủi ro triển khai

| ID | Rủi ro | Khả năng | Tác động | Giảm thiểu |
|---|---|---|---|---|
| RSK-I1 | Chất lượng truy xuất kém với tiếng Việt / PDF bố cục phức tạp | Trung bình | Cao | Chọn embedding đa ngữ; D7/D8 sớm; điều chỉnh chunking; ghi nhận giới hạn |
| RSK-I2 | Token đầu > 5s do embedding + LLM từ xa | Trung bình | Trung bình | Đo từ S3; embed câu hỏi song song; giảm k; chọn model nhanh hơn |
| RSK-I3 | LLM “bịa” nguồn hoặc nhãn sai | Trung bình | Cao | Trích dẫn sinh từ ID chunk, loại nhãn không hợp lệ (D5), ngưỡng không tìm thấy (D3) |
| RSK-I4 | Pháp chế chậm duyệt → không bật được dữ liệu thật | Cao | Cao | Làm việc với dữ liệu thử; trao đổi với Hà từ S0; adapter có thể đổi nhanh |
| RSK-I5 | Rò rỉ chéo người dùng / nội dung vào log | Thấp | Rất cao | RLS + test G3/G4 chạy trong CI; allow-list log |
| RSK-I6 | Prompt injection từ nội dung PDF | Trung bình | Trung bình | Khối dữ liệu phân định; LLM không có công cụ ghi; G8 |
| RSK-I7 | Phạm vi trượt (P1/P2 chen vào R1) | Trung bình | Trung bình | Khóa phạm vi P0 sau S0; thay đổi qua PO |
| RSK-I8 | Đội nhỏ, phụ thuộc người chủ chốt | Trung bình | Trung bình | Review chéo; tài liệu ADR; ranh giới module rõ |

---

## 10. Quản trị dự án

- **Nhịp làm việc:** daily stand-up 15’; sprint planning/review/retro mỗi 2 tuần.
- **Nhánh & phát hành:** trunk-based với nhánh ngắn hạn + PR bắt buộc review; tag theo release (R1, R2…); feature flag cho tính năng chưa hoàn thiện.
- **Môi trường:** Dev (Compose) → Staging (bộ câu hỏi chuẩn, dữ liệu thử đã duyệt) → Production thử nghiệm.
- **Theo dõi:** backlog theo Epic E1–E5; burn-down theo sprint; báo cáo rủi ro/OQ mỗi sprint review.
- **Cổng quyết định:** (1) Cuối S0: chốt đội + phạm vi P0. (2) Cuối S2: chốt nhà cung cấp embedding/LLM + xác thực. (3) Cuối S4: duyệt ngưỡng chất lượng. (4) Cuối S5: Go/No-Go thử nghiệm với dữ liệu thật (cần pháp chế duyệt).

---

## 11. Bước tiếp theo

1. PO/Tech Lead xác nhận giả định 1.3, phạm vi P0 và OQ-010.
2. Khởi động S0: tạo repo/CI, chốt hợp đồng API ([API_Design.md](../design/API_Design.md)) và lược đồ DB.
3. Bắt đầu thu thập bộ câu hỏi chuẩn (OQ-009) với Lan.
4. Gửi Hà (pháp chế) danh sách dịch vụ ngoài dự kiến (LLM, Embedding, IdP) để khởi động rà soát sớm.
5. Tách backlog thành ticket theo bảng mục 4 và gắn nhãn Story/Sprint theo mục 6.
