# PERF-001 — Baseline: độ trễ token đầu, 1 người dùng

| Thuộc tính | Giá trị |
|---|---|
| **ID** | PERF-001 |
| **Loại** | Hiệu năng (chỉ báo) |
| **Ưu tiên** | P1 |
| **Truy vết** | OBJ-006, PRD 5.1 · PERF-001 |
| **URL kiểm thử** | http://127.0.0.1:8000 |
| **Thư mục artifact** | `tests/reports/PERF-001/` |
| **Nguồn** | [docs/testing/Test_Plan.md](../../docs/testing/Test_Plan.md) |

## Mục tiêu

Đo độ trễ từ lúc gửi câu hỏi đến token đầu và tổng thời gian trên adapter giả.

## Điều kiện tiên quyết

- Máy chủ đang chạy tại http://127.0.0.1:8000 (`GET /health` → 200; devserver: adapter LLM/embedding giả, dữ liệu trong bộ nhớ).
- Tài khoản dev **mới, tên duy nhất** cho case này (vd `tc<mã-thời-gian>`), tạo bằng `tc.apiLogin()` hoặc form đăng nhập.
- Tài khoản đã xác nhận thông báo dữ liệu (`GET /api/v1/data-notice` → lấy `version` → `POST /api/v1/data-notice/acceptances`) — với UI dùng `tc.acceptNotice()`.
- `baogia.pdf` (và `hopdong.pdf`) `ready`.

## Các bước và kết quả mong đợi

| # | Hành động | Kết quả mong đợi |
|---|---|---|
| 1 | Trong trang: `fetch` stream tới `POST …/messages`; đo `t_first_token` và `t_total` cho 20 câu hỏi liên tiếp | Có 20 mẫu |
| 2 | Tính p50/p95 của token đầu và tổng thời gian | Bảng trong report |
| 3 | Đối chiếu mục tiêu (token đầu ≤ 5 s p95) | Ghi đạt/không đạt **kèm nêu rõ giới hạn** |
| 4 | Vẽ/ghi histogram đơn giản | Có ảnh |

## Tiêu chí đạt

Tất cả các bước đều đạt kết quả mong đợi. Bất kỳ bước nào lệch → case **FAIL**.

## Lưu ý

- **Quan trọng:** Môi trường hiện dùng **FakeLLM/FakeEmbedding** và kho vector trong bộ nhớ: kết quả chỉ chứng minh logic + rào cản cấu trúc, **không** chứng minh chất lượng/hiệu năng với Claude/pgvector thật (Test Plan 6.0, RISK-04). Ghi rõ điều này trong report. Kết quả không được dùng để kết luận đạt/không đạt mục tiêu 5 s; chỉ là chỉ báo chi phí cố hữu của API/SSE (xem `docs/implement/reports/performance.md`). Đo thật ở staging bằng `deploy/perf/k6-chat.js` (chưa thực hiện).

## Nhiệm vụ của agent

Bạn là agent thực thi test case này. **Phải** tạo đủ các artifact sau trong thư mục riêng `tests/reports/PERF-001/`:

| Artifact | Đường dẫn | Yêu cầu |
|---|---|---|
| Test report | `tests/reports/PERF-001/report.md` | Kết quả tổng, từng bước (mong đợi vs thực tế), lỗi phát hiện, ghi chú |
| Ảnh chụp màn hình | `tests/reports/PERF-001/screenshots/*.png` | Ít nhất **một ảnh cho mỗi bước** (khung tự chụp); ảnh bước lỗi có tiền tố `fail-` |
| Video | `tests/reports/PERF-001/video/PERF-001.webm` | Quay toàn bộ quá trình chạy (khung tự quay) |
| Kết quả máy đọc | `tests/reports/PERF-001/result.json` | Tự sinh |
| Mã chạy | `tests/reports/PERF-001/run.mjs` | Script bạn viết để thực thi case này (giữ lại để chạy lại) |

**Quy trình:**
1. Đọc [tests/README.md](../README.md) (cách dùng khung `tests/tools/tc.mjs`: `startCase`, `tc.step`, `tc.http`, `tc.login`, `tc.axe`…).
2. Xác nhận máy chủ `http://127.0.0.1:8000/health` trả `200`. Nếu chưa chạy, khởi động theo README (không đổi mã sản phẩm).
3. Viết `tests/reports/PERF-001/run.mjs` dùng `startCase("PERF-001", { title: "…" })`. **Mỗi dòng ở bảng “Các bước” là một `tc.step(tên, mong_đợi, fn)`**; dùng `expect` để kiểm tra, trả về chuỗi mô tả kết quả thực tế. Case API dùng `tc.http()` để mỗi request/response có ảnh bằng chứng; case UI dùng ảnh chụp giao diện.
4. Chạy `node tests/reports/PERF-001/run.mjs` từ thư mục gốc repo; mở vài ảnh chính để chắc chắn chúng thật sự là bằng chứng của bước đó.
5. Phân loại kết quả trung thực:
   - Sản phẩm sai so với “Kết quả mong đợi” → giữ **FAIL**, ghi `tc.defect("mô tả + cách tái hiện + mức độ")`. **Không** sửa mã sản phẩm, **không** nới kỳ vọng để “cho đạt”.
   - Lỗi do script/selector của bạn → sửa script và chạy lại.
   - Không thể kiểm chứng (thiếu môi trường, ngoài khả năng của devserver) → ghi rõ trong `tc.note(...)` và trong kết luận là **chưa kiểm chứng** (không ghi PASS).
6. Dọn dẹp trạng thái dùng chung (ví dụ bật lại kill switch) trong `finally`.
7. Kết thúc bằng một câu trả lời ngắn: **ID · PASS/FAIL/chưa kiểm chứng · đường dẫn `report.md` · lỗi phát hiện (nếu có)**.

**Tiêu chí hoàn thành artifact:** `report.md`, ≥ 1 ảnh mỗi bước, 1 video `.webm` không rỗng và `result.json` đều tồn tại; report không chứa token/secret/nội dung nhạy cảm.
