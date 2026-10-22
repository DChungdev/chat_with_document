# Báo cáo hiệu năng ingest (C7)

Ngày chạy: 2026-10-22. 3 lượt/kích cỡ, 2500 ký tự/trang, embedding giả lập với độ trễ 150 ms/lô (64 chunk/lô, 3 lô song song).

| Số trang | PDF (MB) | Chunk | Trích xuất (s) | Chunk hóa (s) | Embed (s) | Tổng p50 (s) | Tổng p95 (s) | ≤ 60s |
|---|---|---|---|---|---|---|---|---|
| 10 | 0.10 | 9 | 0.07 | 0.00 | 0.17 | 0.25 | 0.25 | đạt |
| 50 | 0.52 | 49 | 0.36 | 0.01 | 0.24 | 0.60 | 0.60 | đạt |
| 200 | 2.06 | 199 | 1.42 | 0.06 | 0.65 | 2.12 | 2.15 | đạt |

## Cách đọc kết quả

- **Chỉ phản ánh chi phí của chính pipeline** (pypdf trích xuất, làm sạch + chunk, ghi chỉ mục trong bộ nhớ) cộng độ trễ embedding **giả định**. Embedding thật chưa được chọn [TBD: OQ-012/013] nên **chưa thể kết luận** mục tiêu "PDF ≤ 60s ở p95" (PRD 5.1) cho môi trường thật.
- Trích xuất PDF là giai đoạn tốn CPU nhất (~7 ms/trang trên PDF tổng hợp). PDF thật nhiều ảnh/bảng/font nhúng sẽ chậm hơn — cần đo lại bằng PDF mẫu thật khi có (OQ-008).
- Ngân sách còn lại cho embedding: với 200 trang ≈ 200 chunk ≈ 4 lô; để tổng ≤ 60s thì mỗi lô (3 lô chạy song song) phải trả về trong khoảng vài chục giây — dư dả nếu nhà cung cấp trả về ≤ 5s/lô.
- Hàng đợi chạy 1 job/worker; nhiều PDF cùng lúc thì tăng số bản sao worker, không ảnh hưởng thời gian của từng PDF.
- Chạy lại: `python scripts/bench_ingest.py --runs 5 --embed-latency-ms <đo thực tế> --out docs/implement/reports/ingest_benchmark.md`, tốt nhất trên staging với PDF mẫu thật.
