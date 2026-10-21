# Danh mục task triển khai

Nguồn: [Implement_Plan.md](../Implement_Plan.md). Mỗi file là một task độc lập, đủ ngữ cảnh để nhận và phát triển.

## Workstream A — Nền tảng & hạ tầng

| ID | Task | Sprint | Cỡ | Ưu tiên | Phụ thuộc |
|---|---|---|---|---|---|
| [A1](A1-khoi-tao-monorepo-ci.md) | Khởi tạo monorepo, lint/format và CI | S0 | M | P0 | — |
| [A2](A2-docker-compose-dev.md) | Môi trường dev bằng Docker Compose | S0 | M | P0 | A1 |
| [A3](A3-migration-luoc-do-db.md) | Migration lược đồ cơ sở dữ liệu | S1 | L | P0 | A2 |
| [A4](A4-pgvector-hnsw-rls.md) | pgvector, chỉ mục HNSW và Row-Level Security | S1 | M | P0 | A3 |
| [A5](A5-cau-hinh-feature-flag.md) | Cấu hình, secret và feature flag | S1 | S | P0 | A3 |
| [A6](A6-logging-metrics-tracing.md) | Logging có allow-list, metrics và tracing | S1 | M | P0 | A1 |
| [A7](A7-staging-pipeline-trien-khai.md) | Staging và pipeline triển khai | S5 | L | P0 | A2, A6 |

## Workstream B — Backend lõi

| ID | Task | Sprint | Cỡ | Ưu tiên | Phụ thuộc |
|---|---|---|---|---|---|
| [B1](B1-domain-model.md) | Domain model và quy tắc trạng thái | S1 | M | P0 | A1 |
| [B2](B2-ports-repository.md) | Ports và repository PostgreSQL | S1 | L | P0 | A3, B1 |
| [B3](B3-xac-thuc-authprovider.md) | Xác thực JWT và AuthProvider | S1 | M | P0 | B2 |
| [B4](B4-api-tai-lieu.md) | API tài liệu: tải lên, liệt kê, chi tiết | S2 | L | P0 | B2, B3, C1 |
| [B5](B5-loi-rfc7807-rate-limit.md) | Chuẩn lỗi RFC 7807 và rate limit | S2 | S | P0 | B4 |
| [B6](B6-compliance-thong-bao-du-lieu.md) | Compliance: xác nhận thông báo dữ liệu | S2 | M | P0 | B3 |
| [B7](B7-api-hoi-dap-sse.md) | API hội thoại và hỏi đáp qua SSE | S3 | L | P0 | D4, D5, D3, B9 |
| [B8](B8-api-xem-nguon-dan.md) | API xem nguồn dẫn | S3 | S | P0 | B7 |
| [B9](B9-kill-switch-hoi-dap.md) | Kill switch hỏi đáp | S3 | S | P0 | A5 |
| [B10](B10-api-telemetry.md) | API telemetry | S4 | M | P0 | A3 |
| [B11](B11-xoa-tai-lieu.md) | Xóa tài liệu | S2 | M | P0 | B4, C1 |

## Workstream C — Ingestion

| ID | Task | Sprint | Cỡ | Ưu tiên | Phụ thuộc |
|---|---|---|---|---|---|
| [C1](C1-file-storage-s3.md) | FileStoragePort và adapter S3/MinIO | S1 | M | P0 | A2 |
| [C2](C2-hang-doi-ingest.md) | Hàng đợi ingest trên PostgreSQL | S1 | L | P0 | A3 |
| [C3](C3-trich-xuat-pdf.md) | Trích xuất văn bản PDF theo trang | S1 | L | P0 | C2 |
| [C4](C4-chunking-so-trang.md) | Chunking giữ số trang | S1 | M | P0 | C3 |
| [C5](C5-embedding-port-adapter.md) | EmbeddingPort và adapter | S2 | L | P0 | B2 |
| [C6](C6-worker-ingest-ghi-chi-muc.md) | Worker ingest end-to-end và ghi chỉ mục | S2 | M | P0 | C1, C2, C3, C4, C5 |
| [C7](C7-do-hieu-nang-ingest.md) | Đo hiệu năng xử lý PDF (≤ 60s) | S4 | M | P0 | C6 |

## Workstream D — RAG: truy xuất & trả lời

| ID | Task | Sprint | Cỡ | Ưu tiên | Phụ thuộc |
|---|---|---|---|---|---|
| [D1](D1-vector-store-pgvector.md) | VectorStorePort và adapter pgvector | S3 | L | P0 | A4, C6 |
| [D2](D2-retrieval-nguong-ngu-canh.md) | Retrieval: ngưỡng liên quan và dựng ngữ cảnh | S3 | M | P0 | D1 |
| [D3](D3-nhanh-khong-tim-thay.md) | Nhánh ‘không tìm thấy’ không qua LLM | S3 | S | P0 | D2 |
| [D4](D4-llm-port-prompt.md) | LLMPort, adapter Claude và prompt chỉ dùng nguồn | S3 | L | P0 | D2 |
| [D5](D5-ghep-trich-dan.md) | Ghép trích dẫn và kiểm tra hậu xử lý | S3 | M | P0 | D4 |
| [D6](D6-dung-sinh-gian-doan.md) | Dừng sinh và xử lý gián đoạn | S6 | M | P1 | B7 |
| [D7](D7-bo-cau-hoi-chuan-danh-gia.md) | Bộ câu hỏi chuẩn và script đánh giá | S4 | L | P0 | D5 |
| [D8](D8-hieu-chinh-nguong-k.md) | Hiệu chỉnh ngưỡng, k và chunking | S4 | M | P0 | D7 |

## Workstream E — Frontend

| ID | Task | Sprint | Cỡ | Ưu tiên | Phụ thuộc |
|---|---|---|---|---|---|
| [E1](E1-khoi-tao-spa.md) | Khởi tạo SPA, routing, API client và design tokens | S1 | M | P0 | A1 |
| [E2](E2-scr01-thong-bao-du-lieu.md) | SCR-01 Màn chào và thông báo dữ liệu | S2 | M | P0 | B6, E1 |
| [E3](E3-scr02-man-chinh-rong-tai-len.md) | SCR-02 Màn chính trạng thái rỗng và tải lên | S2 | M | P0 | B4, E1 |
| [E4](E4-scr03-danh-sach-tai-lieu.md) | SCR-03 Danh sách tài liệu và trạng thái | S2 | L | P0 | B4, E3 |
| [E5](E5-scr06-xac-nhan-xoa.md) | SCR-06 Hộp thoại xác nhận xóa tài liệu | S2 | S | P0 | B11, E4 |
| [E6](E6-scr04-khung-chat-sse.md) | SCR-04 Khung chat và streaming SSE | S3 | XL | P0 | B7, E1 |
| [E7](E7-scr05-chip-trich-dan-panel-nguon.md) | Chip trích dẫn và panel nguồn | S3 | L | P0 | B8, E6 |
| [E8](E8-scr08-trang-thai-loi-kill-switch.md) | Trạng thái lỗi và banner kill switch | S3 | M | P0 | E6 |
| [E9](E9-scr07-het-phien.md) | SCR-07 Overlay hết phiên và giữ bản nháp | S2 | M | P0 | B3, E1 |
| [E10](E10-telemetry-client.md) | TelemetryClient và sự kiện | S4 | M | P0 | B10, E6 |
| [E11](E11-scr09-bao-cao-danh-gia.md) | SCR-09 Báo cáo đánh giá MVP | S4 | L | P0 | F1, E1 |
| [E12](E12-a11y-da-trinh-duyet.md) | Tiếp cận (a11y) và kiểm thử đa trình duyệt | S5 | M | P0 | E6, E7, E8 |

## Workstream F — Đo lường

| ID | Task | Sprint | Cỡ | Ưu tiên | Phụ thuộc |
|---|---|---|---|---|---|
| [F1](F1-truy-van-met-bao-cao.md) | Truy vấn MET-001/MET-002 và endpoint báo cáo | S4 | L | P0 | B10 |
| [F2](F2-dashboard-canh-bao.md) | Dashboard và cảnh báo vận hành | S5 | M | P0 | A6 |

## Workstream G — Chất lượng & bảo mật

| ID | Task | Sprint | Cỡ | Ưu tiên | Phụ thuộc |
|---|---|---|---|---|---|
| [G1](G1-unit-test-nghiep-vu.md) | Unit test domain, retrieval và answering | S4 | L | P0 | B1, D2, D5 |
| [G2](G2-test-tich-hop.md) | Test tích hợp với Postgres và MinIO | S4 | L | P0 | B4, C6, D1 |
| [G3](G3-test-co-lap-nguoi-dung.md) | Test cô lập người dùng (US-402) | S4 | M | P0 | B3, D1, B8 |
| [G4](G4-test-khong-ro-noi-dung.md) | Test không rò nội dung vào log và telemetry | S4 | M | P0 | A6, B10, G2 |
| [G5](G5-test-trich-dan-xoa.md) | Test độ tin cậy trích dẫn và xóa dữ liệu | S4 | M | P0 | D5, B11 |
| [G6](G6-e2e-luong-p0.md) | E2E các luồng P0 (Playwright) | S5 | L | P0 | E6, E7, E5 |
| [G7](G7-test-hieu-nang.md) | Test hiệu năng (token đầu, xử lý PDF) | S5 | M | P0 | B7, C7 |
| [G8](G8-ra-soat-bao-mat.md) | Rà soát bảo mật | S5 | M | P0 | D4, B5, B4 |

Tổng: 55 task.
