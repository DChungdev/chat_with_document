# B1 — Domain model và quy tắc trạng thái

| Thuộc tính | Giá trị |
|---|---|
| Workstream | B — Backend lõi |
| Sprint | S1 |
| Cỡ ước lượng | M (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | BE |
| Story liên quan | US-101, US-201, US-301 |
| Trạng thái | Chưa bắt đầu |

## Mô tả

Định nghĩa các thực thể thuần (không phụ thuộc hạ tầng) và quy tắc chuyển trạng thái.

## Phạm vi

- Thực thể: `Document`, `Chunk`, `Conversation`, `Message`, `Citation`.
- Trạng thái `Document`: `processing → ready | error`; không quay ngược.
- Trạng thái `Message`: `sending`, `streaming`, `completed`, `interrupted`, `stopped`, `failed`; trường `grounded`.
- `Citation`: `document_id`, `file_name`, `page`, `snippet`, `valid`.
- Lỗi miền: `DocumentNotReady`, `InvalidDocumentScope`, `QaDisabled`…

## Hướng dẫn kỹ thuật

- Đặt trong `packages/core/domain`; không import SQLAlchemy/FastAPI.
- Dùng dataclass/pydantic thuần; hàm chuyển trạng thái ném lỗi khi chuyển không hợp lệ.
- Giới hạn số tài liệu mỗi câu hỏi (10) là quy tắc miền đọc từ cấu hình.

## Đầu ra / sản phẩm bàn giao

- `packages/core/domain`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [A1](A1-khoi-tao-monorepo-ci.md) — Khởi tạo monorepo, lint/format và CI

**Mở khóa:**
- [B2](B2-ports-repository.md) — Ports và repository PostgreSQL
- [G1](G1-unit-test-nghiep-vu.md) — Unit test domain, retrieval và answering

## Tiêu chí chấp nhận

- [ ] Chuyển trạng thái hợp lệ/không hợp lệ được kiểm đúng.
- [ ] Không import hạ tầng trong `domain` (import-linter xanh).
- [ ] Bao phủ test ≥ 90% module domain.

## Kiểm thử

- Unit test bảng chuyển trạng thái, tham số hóa.

## Tham chiếu

- [SAD.md](../../design/SAD.md) mục 3.1, 3.4
- class_diagram.drawio
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
