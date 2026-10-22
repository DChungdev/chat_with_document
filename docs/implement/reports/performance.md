# Báo cáo hiệu năng (G7)

> **Phạm vi trung thực:** số liệu dưới đây đo **phần mềm của chúng ta** trên một máy phát triển Windows, một tiến trình
> (API + worker ingest chung event loop), **adapter giả** (FakeLLM trễ 30 ms/từ, FakeEmbedding), kho vector **trong bộ nhớ**,
> không Postgres/pgvector, không nhà cung cấp LLM/embedding thật. Vì vậy **không dùng để kết luận đạt/không đạt**
> mục tiêu SAD 5.1 (p95 token đầu ≤ 5s, PDF ≤ 60s). Chúng chỉ cho biết chi phí cố hữu của API/SSE/retrieval/ingest và phát hiện nghẽn.
> Đo thật phải chạy trên staging bằng `deploy/perf/k6-chat.js` — **chưa thực hiện**.

## Cách đo

```bash
python scripts/perf_local.py --users 5  --questions 5 --out perf5.json
python scripts/perf_local.py --users 20 --questions 5 --out perf20.json
```

Mỗi "người dùng" đăng nhập dev, xác nhận thông báo, tải một PDF 30 trang, chờ `ready`, rồi hỏi liên tiếp 5 câu qua SSE thật (HTTP, `httpx` stream).

## Kết quả (2026-10-23, máy dev, Python 3.14)

| Kịch bản | Ingest PDF 30 trang p50 / p95 | Token đầu p50 / p95 | Tổng thời gian trả lời p50 / p95 | Lỗi |
|---|---|---|---|---|
| 5 người dùng đồng thời | 433 / 603 ms | 193 / 225 ms | 925 / 968 ms | 0 |
| 20 người dùng đồng thời (tải đồng thời cả ingest và hỏi) | 3 857 / 9 654 ms | 857 / 2 930 ms | 4 291 / 9 091 ms | 0 |

## Nhận xét

- Ở 20 người dùng, độ trễ tăng gấp ~13 lần so với 5 người dùng: nguyên nhân **nhiều khả năng** là trích xuất PDF (pypdf) và nhúng bằng FakeEmbedding là CPU-bound, chạy chung event loop với API trong cấu hình dev một tiến trình (**giả thuyết, chưa profile để xác nhận**). Ở triển khai thật, worker là tiến trình riêng (đã tách trong `deploy/`), nên API không bị ingest chặn; con số này **không** áp dụng cho production.
- Không có lỗi, không rò rỉ, không treo ở 20 người dùng × 5 câu hỏi.
- Việc cần đo trên staging: (1) p95 token đầu với Claude thật + pgvector (HNSW) ở 20 VU; (2) thời gian ingest thực với embedding thật cho PDF ≤ 50 trang (`scripts/bench_ingest.py` và `docs/implement/reports/ingest_benchmark.md` có số liệu ingest từng giai đoạn trên adapter giả); (3) kích thước pool kết nối DB (`DB_POOL_SIZE`) và số worker.
- Hạn chế của k6: không đọc SSE theo sự kiện; script chỉ đo được **tổng thời gian trả lời** (chặn trên của token đầu; TTFB là sự kiện `message` gửi ngay nên không dùng được). Cần `xk6-sse` để đo chính xác sự kiện `token` đầu tiên, khi đó siết ngưỡng về p95 < 5 s.
