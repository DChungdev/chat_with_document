# Bộ kiểm thử theo test case — Chat với tài liệu

Tách từ [docs/testing/Test_Plan.md](../docs/testing/Test_Plan.md). **Mỗi file trong [cases/](cases/README.md) là một test case**; agent thực thi theo mục “Nhiệm vụ của agent” trong file đó và để lại bằng chứng trong **thư mục riêng mang tên test case** tại `tests/reports/<ID>/`.

```
tests/
├── cases/<ID>.md            # 1 file = 1 test case (mục tiêu, tiền điều kiện, bước, kỳ vọng, nhiệm vụ agent)
├── tools/tc.mjs             # khung chạy: quay video, chụp ảnh từng bước, sinh report
├── tools/summary.mjs        # gom result.json → tests/reports/SUMMARY.md
└── reports/<ID>/            # artifact của từng test case
    ├── run.mjs              # script chạy case (agent viết)
    ├── report.md            # test report (kết quả từng bước + ảnh + video + lỗi)
    ├── result.json          # kết quả máy đọc
    ├── screenshots/NN-*.png # ảnh chụp mỗi bước (fail-*.png khi lỗi)
    └── video/<ID>.webm      # video toàn bộ quá trình test
```

## Môi trường

| Mục | Giá trị |
|---|---|
| URL kiểm thử | **http://127.0.0.1:8000** (đổi bằng biến `BASE_URL` nếu cần) |
| Máy chủ | devserver: API + worker + giao diện đã build; **adapter LLM/embedding giả, dữ liệu trong bộ nhớ** (mất khi tắt) |
| Công cụ | Node ≥ 20, Playwright (có sẵn ở `apps/web/node_modules`), Microsoft Edge hoặc Chromium; ffmpeg của Playwright để quay video |
| Dữ liệu mẫu | `apps/web/e2e/fixtures/` (`baogia.pdf`, `hopdong.pdf`, `scan.pdf`, `matkhau.pdf`, `khong-phai-pdf.pdf`); sinh lại bằng `python scripts/make_fixtures.py` |

### Khởi động máy chủ (nếu chưa chạy)

```bash
# từ thư mục gốc repo
ENVIRONMENT=dev PYTHONUTF8=1 LOG_LEVEL=WARNING FAKE_LLM_DELAY=0.12 \
  .venv/Scripts/python.exe -m docchat_api.devserver --port 8000
curl http://127.0.0.1:8000/health     # {"status":"ok"}
```

Cài một lần (nếu thiếu): `cd apps/web && pnpm install && pnpm build && npx playwright install ffmpeg` (webkit/firefox cho UI-008: `npx playwright install webkit firefox`).

## Cách chạy một test case

```bash
node tests/reports/<ID>/run.mjs      # từ thư mục gốc repo; HEADED=1 để xem trình duyệt
node tests/tools/summary.mjs         # gom kết quả vào tests/reports/SUMMARY.md
```

`run.mjs` do agent viết dựa trên bảng bước của `tests/cases/<ID>.md`:

```js
import { startCase } from "../../tools/tc.mjs";
const tc = await startCase("E2E-001", { title: "Hành trình chính của Lan" });
const { page, expect } = tc;

await tc.step("Đăng nhập", "Thấy hộp thoại thông báo dữ liệu", async () => {
  await tc.login();
  await expect(page.getByRole("dialog", { name: /Chào mừng/ })).toBeVisible();
});
// … mỗi dòng của bảng bước = một tc.step(...)
await tc.finish();     // đóng trình duyệt (chốt video), ghi report.md + result.json
```

Ví dụ hoàn chỉnh: [reports/E2E-001/run.mjs](reports/E2E-001/run.mjs) (UI) và [reports/API-006/run.mjs](reports/API-006/run.mjs) (API).

### API của khung (`tests/tools/tc.mjs`)

| Hàm | Công dụng |
|---|---|
| `startCase(id, {title, viewport, browserType, api})` | Mở trình duyệt có **quay video**; xóa artifact lần chạy trước |
| `tc.step(tên, mong_đợi, fn, {continueOnFail, screenshot})` | Chạy một bước, **tự chụp ảnh**, ghi PASS/FAIL; sau FAIL các bước còn lại là SKIP |
| `tc.http(method, url, {token, json, multipart, headers, label})` | Gọi API và **vẽ request/response lên trang để chụp ảnh + vào video**; trả `{status, headers, text, json}` (token bị che) |
| `tc.apiLogin(name, roles)` | Lấy JWT dev (`roles`: `["user"]`, `["user","ops"]`, `["user","evaluator"]`) |
| `tc.login/acceptNotice/upload/waitReady/ask/waitAnswer` | Thao tác UI dùng lại |
| `tc.axe(page)` | Quét axe-core WCAG 2.1 A/AA |
| `tc.note(t)` / `tc.defect(t)` | Ghi chú / lỗi phát hiện vào report |
| `tc.fixture(tên)`, `tc.uniqueUser()`, `tc.shot(tên)` | Tiện ích |
| `tc.finish({notes})` | Hoàn tất và sinh report |

Case API (ID bắt đầu `API-`) vẽ bằng chứng lên trang chính nên video cho thấy từng request/response; case UI chụp giao diện thật. Có thể dùng `tc.page` / `tc.context` / `tc.browser` để dùng Playwright trực tiếp. `tc.http` buffer toàn bộ phản hồi (không phù hợp để quan sát SSE đang chạy dở: dùng `fetch` stream trong trang).

## Nguyên tắc bắt buộc cho agent

1. **Trung thực:** giữ FAIL khi sản phẩm sai; không sửa mã sản phẩm, không nới kỳ vọng. Việc không kiểm chứng được phải ghi rõ “chưa kiểm chứng”.
2. **Cô lập:** mỗi case dùng tài khoản dev **tên duy nhất**; không dựa vào dữ liệu của case khác. Kill switch (`qa-enabled`) là trạng thái toàn cục: bật lại trong `finally`, không chạy song song.
3. **Giới hạn của môi trường:** devserver dùng LLM/embedding **giả** và kho trong bộ nhớ ⇒ kết quả hiệu năng, chất lượng RAG và bảo mật prompt-injection chỉ có giá trị chỉ báo, **không** chứng minh mục tiêu với Claude/pgvector thật (xem [performance.md](../docs/implement/reports/performance.md), [security_review.md](../docs/implement/reports/security_review.md)).
4. **Dữ liệu nhạy cảm:** chỉ PDF mẫu tổng hợp; không đưa token đầy đủ/secret/nội dung thật vào ảnh, report, repo. Tệp tạm của case để trong `tests/reports/<ID>/data/` (nhỏ).

## Thứ tự chạy gợi ý

`API-*` (nhanh) → `E2E-*` → `SEC-*`, `ACC-*`, `UI-*`, `RAG-*` → `PERF-*` → `OPS-001` → `SEC-010` (khởi động lại máy chủ ⇒ chạy **sau cùng**; mất dữ liệu bộ nhớ). Các case đổi kill switch (`API-018`, `API-031`, `E2E-010`, `OPS-001`) chạy **tuần tự**.
