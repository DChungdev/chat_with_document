# Báo cáo hiệu chỉnh retrieval (D8)

Ngày chạy: 2026-10-22. Nhà cung cấp: **GIẢ LẬP** (embedding túi-từ băm + LLM trích xuất). 42 cấu hình, 40 câu trong phạm vi + 12 ngoài phạm vi, 10 tài liệu × 3 trang.

Ngưỡng nghiệm thu đề xuất (VectorDB mục 10, chờ PO chốt): hit@k ≥ 90%, trích dẫn đúng ≥ 90%, câu ngoài phạm vi bị loại ≥ 90%.

## Cấu hình mặc định hiện tại

| Cấu hình | Chunk | hit@k | Trích dẫn đúng | Câu trả lời đúng | Ngoài phạm vi bị loại | “Không tìm thấy” sai | p95 truy xuất (ms) | Đạt |
|---|---|---|---|---|---|---|---|---|
| chunk 800/100, k=8, ngưỡng 0.30 | 30 | 98% | 98% | 98% | 100% | 2% | 0.5 | ✔ |

## Cấu hình tốt nhất tìm được

| Cấu hình | Chunk | hit@k | Trích dẫn đúng | Câu trả lời đúng | Ngoài phạm vi bị loại | “Không tìm thấy” sai | p95 truy xuất (ms) | Đạt |
|---|---|---|---|---|---|---|---|---|
| chunk 200/0, k=4, ngưỡng 0.30 | 30 | 98% | 98% | 98% | 100% | 2% | 0.6 | ✔ |

## 8 cấu hình đứng đầu

| Cấu hình | Chunk | hit@k | Trích dẫn đúng | Câu trả lời đúng | Ngoài phạm vi bị loại | “Không tìm thấy” sai | p95 truy xuất (ms) | Đạt |
|---|---|---|---|---|---|---|---|---|
| chunk 200/0, k=4, ngưỡng 0.30 | 30 | 98% | 98% | 98% | 100% | 2% | 0.6 | ✔ |
| chunk 200/0, k=8, ngưỡng 0.30 | 30 | 98% | 98% | 98% | 100% | 2% | 1.0 | ✔ |
| chunk 400/50, k=4, ngưỡng 0.30 | 30 | 98% | 98% | 98% | 100% | 2% | 0.5 | ✔ |
| chunk 400/50, k=8, ngưỡng 0.30 | 30 | 98% | 98% | 98% | 100% | 2% | 0.6 | ✔ |
| chunk 800/100, k=4, ngưỡng 0.30 | 30 | 98% | 98% | 98% | 100% | 2% | 0.5 | ✔ |
| chunk 800/100, k=8, ngưỡng 0.30 | 30 | 98% | 98% | 98% | 100% | 2% | 0.5 | ✔ |
| chunk 200/0, k=4, ngưỡng 0.25 | 30 | 98% | 98% | 98% | 100% | 2% | 0.6 | ✔ |
| chunk 200/0, k=8, ngưỡng 0.25 | 30 | 98% | 98% | 98% | 100% | 2% | 0.5 | ✔ |

## Số cấu hình đạt cả ba ngưỡng: 24/42


> **Cảnh báo:** kết quả dùng embedding GIẢ LẬP nên chỉ kiểm chứng *phương pháp và đường ống*, **không** dùng để chọn giá trị cho production. Điểm cosine của mô hình thật nằm ở thang khác; phải chạy lại bằng `--real` với mô hình embedding đã duyệt và bộ câu hỏi thật [TBD: OQ-009, OQ-012/013] rồi mới ghi `retrieval_min_score`, `retrieval_top_k`, `chunk_*` vào `app_config`.
