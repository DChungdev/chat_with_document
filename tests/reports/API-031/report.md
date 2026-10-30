# Test report — API-031: PUT /admin/flags/qa-enabled: phân quyền

| Mục | Giá trị |
|---|---|
| **Kết quả** | **PASS** |
| Test case | [API-031](../../cases/API-031.md) |
| URL kiểm thử | http://127.0.0.1:8000 |
| Trình duyệt | Microsoft Edge (Chromium) (1280×720) |
| Bắt đầu / kết thúc | 2026-10-30T12:04:31.412Z → 2026-10-30T12:04:38.089Z (6.7s) |
| Số bước | PASS: 5 · FAIL: 0 · SKIP: 0 |
| Video | [video/API-031.webm](video/API-031.webm) |

<video src="video/API-031.webm" controls width="720"></video>

## Kết quả từng bước

### Bước 1. User: PUT {enabled:false} — ✅ PASS

- **Mong đợi:** 403; /config vẫn qaEnabled=true
- **Thực tế:** Đúng như mong đợi

![Bước 1](screenshots/01-user-put-qa-enabled-false.png)

![Bước 1](screenshots/02-get-config.png)

### Bước 2. Evaluator: PUT {enabled:false} — ✅ PASS

- **Mong đợi:** 403
- **Thực tế:** Đúng như mong đợi

![Bước 2](screenshots/03-evaluator-put-qa-enabled-false.png)

### Bước 3. Ops: false rồi true — ✅ PASS

- **Mong đợi:** Cả hai 204; /config phản ánh
- **Thực tế:** Đúng như mong đợi

![Bước 3](screenshots/04-ops-put-qa-enabled-false.png)

![Bước 3](screenshots/05-ops-put-qa-enabled-true.png)

![Bước 3](screenshots/06-get-config-da-bat-lai.png)

### Bước 4. Body sai {enabled:"abc"} — ✅ PASS

- **Mong đợi:** 400 VALIDATION_ERROR
- **Thực tế:** Đúng như mong đợi

![Bước 4](screenshots/07-ops-put-body-sai.png)

### Bước 5. Dọn dẹp: bảo đảm qaEnabled=true — ✅ PASS

- **Mong đợi:** 204
- **Thực tế:** Đúng như mong đợi

![Bước 5](screenshots/08-ops-put-qa-enabled-true-don-dep.png)

