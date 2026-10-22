# D4 — LLMPort, adapter Claude và prompt chỉ dùng nguồn

| Thuộc tính | Giá trị |
|---|---|
| Workstream | D — RAG: truy xuất & trả lời |
| Sprint | S3 |
| Cỡ ước lượng | L (S ≤ 1 ngày, M 2–3 ngày, L 4–5 ngày, XL > 1 tuần) |
| Ưu tiên | P0 |
| Người thực hiện đề xuất | AI/BE |
| Story liên quan | US-202, US-203 |
| Trạng thái | Hoàn thành — prompt chống injection + adapter Claude (client giả) + retry/timeout/circuit breaker. CHƯA gọi Claude thật (cần khóa API; nhà cung cấp chờ OQ-012/013) |

## Mô tả

Gọi LLM streaming với chỉ thị chỉ dùng nguồn được cấp; nội dung PDF được coi là dữ liệu.

## Phạm vi

- Port `LLMPort.stream(prompt) -> AsyncIterator[str]`.
- Adapter Claude (Anthropic API) streaming; adapter `FakeLLM` cho dev/test.
- Prompt: chỉ thị ‘chỉ trả lời từ các đoạn dưới đây; nếu không đủ thì nói không tìm thấy; ghi nhãn [Sx] sau mỗi ý’.
- Đoạn trích nằm trong khối phân định (vd. thẻ XML) kèm chỉ thị bỏ qua mệnh lệnh nằm trong đó (chống prompt injection).
- Timeout, retry, circuit breaker; hỗ trợ huỷ stream (cho nút Dừng).
- Model cụ thể và vị trí xử lý dữ liệu **[TBD: OQ-012/013]**; cấu hình qua tham số.

## Hướng dẫn kỹ thuật

- Tham khảo skill/tài liệu `claude-api` khi triển khai (model id, streaming, xử lý lỗi).
- LLM không có công cụ/hành động ghi (SAD 5.1).
- Hỗ trợ ngữ cảnh hội thoại trước đó (dùng ở US-204/P1) bằng tham số lịch sử tùy chọn.
- Không log prompt/đoạn trích.

## Đầu ra / sản phẩm bàn giao

- `infra/llm`, `packages/core/answering/prompt`.

## Phụ thuộc

**Cần hoàn thành trước:**
- [D2](D2-retrieval-nguong-ngu-canh.md) — Retrieval: ngưỡng liên quan và dựng ngữ cảnh

**Mở khóa:**
- [B7](B7-api-hoi-dap-sse.md) — API hội thoại và hỏi đáp qua SSE
- [D5](D5-ghep-trich-dan.md) — Ghép trích dẫn và kiểm tra hậu xử lý
- [G8](G8-ra-soat-bao-mat.md) — Rà soát bảo mật

## Tiêu chí chấp nhận

- [ ] Stream trả token tuần tự; huỷ stream dừng gọi nhà cung cấp.
- [ ] Đoạn trích chứa ‘bỏ qua mọi chỉ thị’ không làm LLM thoát khỏi ràng buộc (kiểm bằng bộ test tấn công).
- [ ] Lỗi nhà cung cấp → lỗi miền, không crash.

## Kiểm thử

- Unit test dựng prompt (snapshot); contract test hai adapter; bộ test prompt injection (liên kết G8).

## Tham chiếu

- [SAD.md](../../design/SAD.md) ADR-03, ADR-08, mục 5.1
- Kế hoạch tổng: [Implement_Plan.md](../Implement_Plan.md)

## Định nghĩa hoàn thành (DoD)

- [ ] Mã đã được review; CI xanh (lint, unit, integration).
- [ ] Mọi tiêu chí chấp nhận ở trên đã được kiểm chứng.
- [ ] Không ghi nội dung tài liệu/câu hỏi vào log hoặc telemetry.
- [ ] Mọi truy vấn dữ liệu người dùng đều có `user_id` (nếu áp dụng).
- [ ] Tài liệu liên quan (API/DB/README) đã cập nhật nếu có thay đổi.
