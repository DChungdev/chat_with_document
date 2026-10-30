# Test report — API-037: POST /messages/{id}/regenerate (P1)

| Mục | Giá trị |
|---|---|
| **Kết quả** | **PASS** |
| Test case | [API-037](../../cases/API-037.md) |
| URL kiểm thử | http://127.0.0.1:8000 |
| Trình duyệt | Microsoft Edge (Chromium) (1280×720) |
| Bắt đầu / kết thúc | 2026-10-30T12:03:46.604Z → 2026-10-30T12:03:54.141Z (7.5s) |
| Số bước | PASS: 4 · FAIL: 0 · SKIP: 0 |
| Video | [video/API-037.webm](video/API-037.webm) |

<video src="video/API-037.webm" controls width="720"></video>

## Kết quả từng bước

### Bước 1. Chuẩn bị: tạo message bị dừng — ✅ PASS

- **Mong đợi:** stopped
- **Thực tế:** Đúng như mong đợi

![Bước 1](screenshots/01-post-documents-baogia-pdf.png)

![Bước 1](screenshots/02-get-documents-id-baogia-pdf-sau-khi-xu-ly.png)

![Bước 1](screenshots/03-post-conversations.png)

### Bước 2. POST /messages/{id}/regenerate — ✅ PASS

- **Mong đợi:** 200 SSE; messageId mới; done status=complete
- **Thực tế:** Đúng như mong đợi

![Bước 2](screenshots/04-post-messages-id-regenerate.png)

### Bước 3. Văn bản mới — ✅ PASS

- **Mong đợi:** Chứa “30 ngày”
- **Thực tế:** Đúng như mong đợi

![Bước 3](screenshots/05-van-ban-moi.png)

### Bước 4. regenerate message của người khác — ✅ PASS

- **Mong đợi:** 404
- **Thực tế:** Đúng như mong đợi

![Bước 4](screenshots/06-b-post-messages-id-regenerate.png)

## Lỗi console của trình duyệt (6)

- `Failed to load resource: the server responded with a status of 404 (Not Found)`
- `Applying inline style violates the following Content Security Policy directive 'style-src 'self''. Either the 'unsafe-inline' keyword, a hash ('sha256-EK+SZlIuMZf8cUh+IBy4lh8eovkcnABzCDy0N/SqbS4='), o`
- `Applying inline style violates the following Content Security Policy directive 'style-src 'self''. Either the 'unsafe-inline' keyword, a hash ('sha256-irFBMySPhXR+HTgXgxtSlvMg9lIX6UyQ5ZisOG5mXl8='), o`
- `Applying inline style violates the following Content Security Policy directive 'style-src 'self''. Either the 'unsafe-inline' keyword, a hash ('sha256-VLlNtlGTRiQsnLfeR8aJ4wo/gy/o6rjghN2TEkJm2iQ='), o`
- `Applying inline style violates the following Content Security Policy directive 'style-src 'self''. Either the 'unsafe-inline' keyword, a hash ('sha256-irFBMySPhXR+HTgXgxtSlvMg9lIX6UyQ5ZisOG5mXl8='), o`
- `Applying inline style violates the following Content Security Policy directive 'style-src 'self''. Either the 'unsafe-inline' keyword, a hash ('sha256-VLlNtlGTRiQsnLfeR8aJ4wo/gy/o6rjghN2TEkJm2iQ='), o`

