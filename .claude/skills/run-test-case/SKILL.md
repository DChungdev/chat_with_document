---
name: run-test-case
description: Thực thi một test case của dự án Chat với tài liệu (tests/cases/<ID>.md) trên http://127.0.0.1:8000 và tạo đủ bằng chứng (report.md, ảnh từng bước, video, result.json) trong tests/reports/<ID>/. Dùng khi người dùng yêu cầu chạy/kiểm tra một test case (vd "chạy API-004", "chạy test E2E-001") hoặc cả một nhóm (API, E2E, SEC…).
---

# Chạy một test case

Đầu vào: mã test case `<ID>` (vd `API-004`, `E2E-010`). Nếu người dùng nêu một nhóm, lặp tuần tự từng case (không song song với các case đổi kill switch).

## Quy trình
1. **Đọc** `tests/cases/<ID>.md` (mục tiêu, tiền điều kiện, bảng bước/kết quả mong đợi, lưu ý) và `tests/README.md` nếu chưa nắm khung `tests/tools/tc.mjs` (`startCase`, `tc.step`, `tc.http`, `tc.login`…) và `tests/tools/api.mjs` (helper cho case API).
2. **Máy chủ:** `curl http://127.0.0.1:8000/health` phải trả `{"status":"ok"}`. Nếu không, khởi động devserver (xem `.claude/CLAUDE.md`) — chỉ khởi động, không sửa mã sản phẩm.
3. **Script:** nếu chưa có `tests/reports/<ID>/run.mjs`, viết mới. Mỗi dòng của bảng bước = một `tc.step(tên, mong_đợi, fn)`; case API dùng `tc.http()`/helper trong `api.mjs`, case UI dùng thao tác Playwright. Tham khảo mẫu: `tests/reports/E2E-001/run.mjs` (UI) và `tests/reports/API-004/run.mjs` (API).
4. **Chạy:** `node tests/reports/<ID>/run.mjs` từ thư mục gốc repo. Mở vài ảnh chính để chắc chắn chúng là bằng chứng đúng của bước đó.
5. **Phân loại kết quả (trung thực):**
   - Sản phẩm lệch kỳ vọng → giữ **FAIL** + `tc.defect("mô tả, cách tái hiện, mức độ")`. Không sửa mã sản phẩm, không nới kỳ vọng.
   - Lỗi do script/selector hoặc kỳ vọng ghi sai so với tài liệu thiết kế → sửa script (và file case nếu kỳ vọng sai, nói rõ lý do) rồi chạy lại.
   - Không kiểm chứng được (thiếu môi trường) → `tc.note(...)` và kết luận “chưa kiểm chứng”, không ghi PASS.
6. **Dọn dẹp** trạng thái dùng chung (vd bật lại `qa-enabled`) trong `finally`.
7. **Cập nhật tổng hợp:** `node tests/tools/summary.mjs` và `node tests/tools/checklist.mjs`.
8. **Trả lời ngắn:** `ID · PASS/FAIL/chưa kiểm chứng · đường dẫn report.md · lỗi phát hiện (nếu có)`.

## Tiêu chí hoàn thành
`tests/reports/<ID>/` có `report.md`, ≥ 1 ảnh mỗi bước (`screenshots/`), video `video/<ID>.webm` không rỗng, `result.json`, `run.mjs`. Không có token/secret/nội dung nhạy cảm trong report.

## Lưu ý môi trường
Devserver dùng LLM/embedding giả và kho trong bộ nhớ: kết quả về hiệu năng, chất lượng RAG, prompt injection chỉ là chỉ báo — nêu rõ điều này trong report.
