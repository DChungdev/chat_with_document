# Test report — API-038: PUT /messages/{id}/feedback (P1)

| Mục | Giá trị |
|---|---|
| **Kết quả** | **PASS** |
| Test case | [API-038](../../cases/API-038.md) |
| URL kiểm thử | http://127.0.0.1:8000 |
| Trình duyệt | Microsoft Edge (Chromium) (1280×720) |
| Bắt đầu / kết thúc | 2026-10-30T12:03:55.866Z → 2026-10-30T12:04:05.908Z (10.0s) |
| Số bước | PASS: 6 · FAIL: 0 · SKIP: 0 |
| Video | [video/API-038.webm](video/API-038.webm) |

<video src="video/API-038.webm" controls width="720"></video>

## Kết quả từng bước

### Bước 1. Chuẩn bị: câu trả lời hoàn tất — ✅ PASS

- **Mong đợi:** messageId
- **Thực tế:** Đúng như mong đợi

![Bước 1](screenshots/01-post-documents-baogia-pdf.png)

![Bước 1](screenshots/02-get-documents-id-baogia-pdf-sau-khi-xu-ly.png)

![Bước 1](screenshots/03-post-conversations.png)

![Bước 1](screenshots/04-post-messages.png)

### Bước 2. PUT feedback {rating:'up'} — ✅ PASS

- **Mong đợi:** 204
- **Thực tế:** Đúng như mong đợi

![Bước 2](screenshots/05-put-feedback-rating-up.png)

### Bước 3. Lặp lại cùng yêu cầu — ✅ PASS

- **Mong đợi:** 204, kết quả như nhau
- **Thực tế:** Đúng như mong đợi

![Bước 3](screenshots/06-put-feedback-rating-up-lan-2.png)

### Bước 4. {rating:'down', reasonCode} — ✅ PASS

- **Mong đợi:** 204
- **Thực tế:** Đúng như mong đợi

![Bước 4](screenshots/07-put-feedback-rating-down-reasoncode.png)

### Bước 5. {rating:'abc'} — ✅ PASS

- **Mong đợi:** 400/422 VALIDATION_ERROR
- **Thực tế:** Đúng như mong đợi

![Bước 5](screenshots/08-put-feedback-rating-abc.png)

### Bước 6. Message của người khác — ✅ PASS

- **Mong đợi:** 404
- **Thực tế:** Đúng như mong đợi

![Bước 6](screenshots/09-b-put-feedback-message-cua-a.png)

