# Tài liệu yêu cầu nghiệp vụ (BRD) — Công cụ “Chat với tài liệu”

## Tóm tắt xác thực đầu vào

- **Đầu vào nhận được:** mô tả bối cảnh giả định trong [BRD_Prompt_IEEE_standard.md](../BRD_Prompt_IEEE_standard.md): đội phát triển kinh doanh gặp khó khăn khi tổng hợp thông tin từ nhiều PDF; quản lý yêu cầu xây dựng MVP dạng ứng dụng web để tải PDF lên và trao đổi với AI nhằm truy vấn nội dung tài liệu. Đề xuất bổ sung từ BA được cho phép nhưng chưa có nội dung cụ thể. Nguồn: `SRC-001`.
- **Thông tin còn thiếu:** tổ chức/dự án cụ thể, người bảo trợ và chủ nghiệp vụ, quy mô và loại tài liệu, số liệu hiện trạng, KPI mục tiêu, ngân sách, mốc thời gian, chính sách dữ liệu/bảo mật, nhóm người dùng và tiêu chí chất lượng câu trả lời.
- **Ba rủi ro lớn nhất đối với chất lượng yêu cầu:** (1) chưa có số liệu cơ sở và mục tiêu đo lường lợi ích; (2) chưa rõ tài liệu có dữ liệu nhạy cảm, quyền sở hữu, lưu trữ và xóa như thế nào; (3) chưa định nghĩa tiêu chuẩn chấp nhận cho độ chính xác, phạm vi và nguồn dẫn của câu trả lời AI.

> **Quy ước bằng chứng:** `SRC-001` là duy nhất nguồn nghiệp vụ hiện có, tức mô tả trong prompt được cung cấp. Các nội dung suy luận hoặc chưa được xác nhận được đánh dấu `[Chưa xác minh]`, đưa vào giả định/rủi ro/câu hỏi mở; không được xem là quyết định đã phê duyệt. Ngày lập tài liệu: 19/10/2026.

## 4.1. Kiểm soát tài liệu

| Thuộc tính | Giá trị |
|---|---|
| Tên tài liệu | Tài liệu yêu cầu nghiệp vụ (BRD) — Công cụ “Chat với tài liệu” |
| Số tài liệu | BRD-DOCCHAT-001 |
| Phiên bản | 0.1 |
| Trạng thái | Bản nháp — chưa được xác nhận |
| Tác giả | [TBD: OQ-001] |
| Người đóng góp | [TBD: OQ-001] |
| Người rà soát | [TBD: OQ-001] |
| Người phê duyệt | [TBD: OQ-001] |
| Phân loại bảo mật | [TBD: OQ-012] |

### Lịch sử phiên bản

| Phiên bản | Ngày | Tác giả | Nội dung thay đổi |
|---|---|---|---|
| 0.1 | 19/10/2026 | [TBD: OQ-001] | Tạo bản nháp từ mô tả nghiệp vụ ban đầu (`SRC-001`). |

### Danh sách phân phối

| Nhóm/người nhận | Mục đích | Trạng thái |
|---|---|---|
| Nhà bảo trợ, chủ nghiệp vụ, đội phát triển kinh doanh, BA, nhóm sản phẩm/kỹ thuật | Rà soát và xác nhận yêu cầu | Danh sách cụ thể [TBD: OQ-001] |

## 4.2. Tóm tắt điều hành

Đội phát triển kinh doanh được mô tả là gặp khó khăn khi nắm bắt và tổng hợp thông tin từ nhiều tài liệu PDF; việc tìm thông tin phải thực hiện bằng cách tổng hợp thủ công giữa các tệp. Mô tả chưa kèm số lượng tài liệu, thời gian xử lý hay chi phí nên mức độ tác động chưa được định lượng (`SRC-001`).

Sáng kiến đề xuất xây dựng MVP dưới dạng ứng dụng web cho phép người dùng tải PDF lên và đặt câu hỏi bằng AI về nội dung các tài liệu đã tải lên. Mục tiêu nghiệp vụ dự kiến là giúp người dùng tra cứu và tổng hợp thông tin tài liệu thuận tiện hơn; mục tiêu này cần được nhà bảo trợ xác nhận và đo bằng số liệu cơ sở cùng mục tiêu định lượng trước khi phê duyệt baseline.

Chưa có thông tin được xác nhận về ngân sách, thời hạn, nguồn lực, chi phí vận hành hoặc thời điểm triển khai. Rủi ro trọng yếu gồm chất lượng câu trả lời AI, quyền riêng tư/bảo mật tài liệu và thiếu tiêu chí đo hiệu quả. **Quyết định đề nghị:** xác nhận vấn đề, nhóm người dùng, phạm vi MVP, tiêu chí thành công, quy tắc dữ liệu và người có thẩm quyền phê duyệt. Tài liệu hiện **chưa sẵn sàng để baseline hoặc phê duyệt triển khai**.

## 4.3. Bối cảnh nghiệp vụ và phát biểu vấn đề

### Hiện trạng và vấn đề

Theo mô tả duy nhất hiện có, đội phát triển kinh doanh phải làm việc với nhiều tệp PDF và khó nắm bắt đầy đủ thông tin; khi cần tìm thông tin, họ mất thời gian tổng hợp từ nhiều tệp. Đây là mô tả định tính, chưa có phỏng vấn, quan sát quy trình, dữ liệu thời gian hay xác nhận từ người bảo trợ (`SRC-001`).

**Phát biểu vấn đề:** Nhân sự phát triển kinh doanh cần một cách tra cứu thông tin trong tập tài liệu PDF đã cung cấp mà không phải tự tổng hợp thủ công qua nhiều tệp. Tác động định lượng, nguyên nhân gốc, mức độ thường xuyên và chi phí không hành động đều **[Chưa xác minh]**.

### Quy trình hiện tại (mức khái quát)

```mermaid
flowchart LR
    A[Phát sinh câu hỏi nghiệp vụ] --> B[Người dùng tìm trong nhiều tệp PDF]
    B --> C[Tự đọc và tổng hợp thông tin]
    C --> D[Trả lời hoặc sử dụng thông tin]
```

Các bước trên chỉ khái quát từ mô tả `SRC-001`; trình tự chi tiết, công cụ đang dùng và điểm bàn giao cần xác nhận (`OQ-003`).

### Thay đổi nghiệp vụ dự kiến

```mermaid
flowchart LR
    A[Người dùng có tài liệu PDF] --> B[Tải tài liệu lên công cụ]
    B --> C[Đặt câu hỏi về nội dung tài liệu đã tải]
    C --> D[AI trả lời dựa trên nội dung tài liệu]
    D --> E[Người dùng đánh giá và sử dụng câu trả lời]
```

Đây là luồng nghiệp vụ mục tiêu ở mức khái niệm, được diễn giải từ `SRC-001`; chưa xác định các bước xử lý, quyền truy cập, trường hợp lỗi hay cách người dùng xác thực câu trả lời.

### Bên bị ảnh hưởng và chi phí không hành động

| Bên liên quan | Ảnh hưởng được mô tả | Mức độ bằng chứng |
|---|---|---|
| Đội phát triển kinh doanh | Khó nắm bắt đủ nội dung nhiều PDF; mất thời gian tổng hợp khi tra cứu | Định tính, `SRC-001`; chưa đo lường |
| Quản lý/người yêu cầu sáng kiến | Cần quyết định có đầu tư MVP hay không | Suy ra từ yêu cầu của quản lý; vai trò và người cụ thể chưa xác minh |
| Các nhóm có tài liệu được tải lên hoặc sử dụng kết quả | Ảnh hưởng có thể phát sinh tùy nguồn, quyền và loại tài liệu | [Chưa xác minh: OQ-012, OQ-013] |

Chi phí không hành động về doanh thu, chi phí nhân sự, rủi ro, tuân thủ và tác động khách hàng chưa có dữ liệu để kết luận (`OQ-004`).

## 4.4. Động lực và mục tiêu nghiệp vụ

| ID | Động lực | Mục tiêu nghiệp vụ (dự thảo) | Metric | Baseline | Mục tiêu | Thời hạn | Nguồn |
|---|---|---|---|---|---|---|---|
| BO-001 | Khó tra cứu và tổng hợp thông tin từ nhiều PDF | Cải thiện khả năng tra cứu thông tin trong tập PDF phục vụ công việc phát triển kinh doanh | MET-001: Thời gian hoàn tất một tác vụ tra cứu/tổng hợp đại diện | [TBD: OQ-005] | [TBD: OQ-005] | [TBD: OQ-006] | SRC-001 (vấn đề định tính; chỉ số chưa được cung cấp) |
| BO-002 | Cần xác định giá trị của MVP trước khi mở rộng đầu tư | Xác minh mức độ hữu ích và khả năng sử dụng của quy trình hỏi đáp trên tài liệu | MET-002: Tỷ lệ tác vụ thử nghiệm được người dùng đánh giá là hoàn thành thành công | [TBD: OQ-005] | [TBD: OQ-005] | [TBD: OQ-006] | [Chưa xác minh]; cần nhà bảo trợ xác nhận mục tiêu này |

**Định nghĩa và kế hoạch đo lường metric (đang chờ xác nhận):**

| Metric | Định nghĩa/công thức dự kiến | Nguồn dữ liệu | Chủ sở hữu | Tần suất | Ngày baseline |
|---|---|---|---|---|---|
| MET-001 | Trung vị thời gian từ khi bắt đầu tác vụ tra cứu đại diện đến khi người dùng ghi nhận đã có thông tin cần thiết; cần thống nhất cách lấy mẫu và phạm vi tác vụ | Nhật ký đo/thử nghiệm nghiệp vụ [TBD: OQ-005] | [TBD: OQ-001] | [TBD: OQ-005] | [TBD: OQ-005] |
| MET-002 | Số tác vụ thử nghiệm được người dùng xác nhận hoàn thành thành công / tổng số tác vụ thử nghiệm hợp lệ × 100%; cần định nghĩa “thành công” | Biên bản đánh giá thử nghiệm [TBD: OQ-005] | [TBD: OQ-001] | [TBD: OQ-005] | [TBD: OQ-005] |

Các metric trên là đề xuất để thảo luận, không phải KPI đã được phê duyệt. Không thể xác nhận tính hợp lệ của mục tiêu nghiệp vụ trước khi có baseline, mục tiêu, phương pháp và người chịu trách nhiệm đo lường.

## 4.5. Phạm vi

### Trong phạm vi dự thảo

- Nghiệp vụ đội phát triển kinh doanh tra cứu thông tin trong tài liệu PDF.
- Năng lực nghiệp vụ của MVP: tải PDF lên, đặt câu hỏi bằng AI và nhận phản hồi liên quan đến nội dung tài liệu đã tải lên (`SRC-001`).
- Kênh sử dụng ở mức yêu cầu: ứng dụng web (`SRC-001`).
- Đánh giá thử nghiệm MVP bằng tiêu chí và metric được nhà bảo trợ xác nhận (`OQ-005`, `OQ-006`).

### Ngoài phạm vi MVP theo thông tin hiện tại

| Nội dung | Lý do/ghi chú |
|---|---|
| Định dạng tài liệu khác PDF | Chỉ PDF được nêu trong đầu vào; định dạng khác chưa được yêu cầu (`SRC-001`). |
| Tự động cập nhật hoặc đồng bộ tài liệu từ kho bên ngoài | Không có trong yêu cầu hiện tại; cần xác nhận nếu là nhu cầu (`OQ-007`). |
| Duyệt/phê duyệt nội dung nghiệp vụ hoặc thay thế chuyên gia | Không được nêu là mục tiêu; người dùng vẫn cần chịu trách nhiệm đánh giá thông tin [Chưa xác minh]. |
| Phân tích thị trường, tạo báo cáo tự động hoặc tích hợp quy trình bán hàng | Chưa có bằng chứng về nhu cầu; không đưa vào baseline MVP. |

### Hoãn đến giai đoạn sau

- Hỗ trợ nhiều định dạng ngoài PDF, tích hợp kho tài liệu, chia sẻ không gian làm việc, quản trị nâng cao và báo cáo sử dụng: **chưa quyết định**, cần xác định thứ tự ưu tiên qua `OQ-007`.

### Ranh giới

Sáng kiến bắt đầu khi người dùng có nhu cầu tra cứu nội dung PDF và kết thúc khi người dùng xem xét, xác nhận hoặc sử dụng thông tin nhận được. Việc xác minh độ đúng nghiệp vụ và quyết định dựa trên câu trả lời không được mặc định là do công cụ thực hiện. Chi tiết đầu vào/đầu ra với quy trình liền kề cần xác nhận (`OQ-003`, `OQ-010`).

## 4.6. Các bên liên quan và nhu cầu

### Danh sách bên liên quan

| ID | Bên liên quan/nhóm | Vai trò nghiệp vụ | Mối quan tâm | Ảnh hưởng | Nhu cầu | Nguồn |
|---|---|---|---|---|---|---|
| STK-001 | Đội phát triển kinh doanh | Tra cứu, sử dụng thông tin từ tài liệu PDF | Tìm thông tin và tổng hợp nội dung | [TBD] | SN-001 | SRC-001 |
| STK-002 | Quản lý/người yêu cầu sáng kiến | Đề xuất phát triển MVP; danh tính và quyền phê duyệt chưa xác định | Kết quả, phạm vi, chi phí và rủi ro đầu tư | [TBD] | SN-002 | SRC-001 |
| STK-003 | BA | Đề xuất và làm rõ yêu cầu nghiệp vụ | Tính đầy đủ, khả năng kiểm chứng và phạm vi | [TBD] | SN-003 | SRC-001 (vai trò BA được prompt nêu; người cụ thể chưa xác định) |
| STK-004 | Chủ sở hữu tài liệu/bộ phận pháp chế hoặc bảo mật | Vai trò có thể liên quan đến quyền, phân loại và xử lý tài liệu | Quyền sử dụng, bảo mật, lưu giữ và xóa | [TBD] | SN-004 | [Chưa xác minh: OQ-012, OQ-013] |
| STK-005 | Nhóm sản phẩm/kỹ thuật/vận hành | Có thể triển khai và hỗ trợ MVP | Khả năng thực hiện, vận hành và xử lý sự cố | [TBD] | SN-005 | [Chưa xác minh: OQ-001, OQ-006] |

Các nhóm STK-004 và STK-005 là nhóm cần xác nhận, không khẳng định họ đã được chỉ định tham gia. Bên có thể phản đối hoặc chặn việc áp dụng (ví dụ chủ sở hữu dữ liệu, pháp chế, bảo mật) chưa được xác định (`OQ-013`).

### Nhu cầu của các bên liên quan

| ID | Bên liên quan | Phát biểu nhu cầu | Nỗi đau hiện tại | Bằng chứng | Ưu tiên |
|---|---|---|---|---|---|
| SN-001 | STK-001 | Tôi cần tra cứu thông tin trong các PDF liên quan mà không phải tự tổng hợp thủ công qua nhiều tệp cho mỗi câu hỏi. | Mất thời gian và khó nắm bắt đầy đủ thông tin | SRC-001, định tính | Must (dự thảo) |
| SN-002 | STK-002 | Tôi cần có căn cứ đo lường để quyết định MVP có đạt kết quả nghiệp vụ mong muốn hay không. | Chưa có KPI hoặc tiêu chí nghiệm thu được cung cấp | [Chưa xác minh]; cần xác nhận qua OQ-005 | Should (dự thảo) |
| SN-003 | STK-003 | Tôi cần yêu cầu và phạm vi có thể được các bên rà soát, xác nhận và truy vết. | Chưa có đầu vào nghiệp vụ chi tiết ngoài mô tả ban đầu | SRC-001 và yêu cầu chất lượng trong prompt | Should (dự thảo) |
| SN-004 | STK-004 | Tôi cần biết tài liệu nào được phép sử dụng và cách quản lý dữ liệu trước khi cho phép đưa tài liệu vào quy trình. | [Chưa xác minh] | OQ-012, OQ-013 | Must (cần xác nhận) |
| SN-005 | STK-005 | Tôi cần tiêu chí phạm vi, chất lượng và vận hành đủ rõ để đánh giá tính khả thi của MVP. | [Chưa xác minh] | OQ-006, OQ-008, OQ-011 | Should (cần xác nhận) |

## 4.7. Yêu cầu nghiệp vụ

Ưu tiên và tiêu chí dưới đây là **dự thảo** dựa trên mô tả ban đầu. Các ngưỡng định lượng chưa được đặt tùy tiện; phải được xác nhận trước khi đưa vào baseline. Từ **shall** được giữ làm từ quy phạm theo tiêu chuẩn của prompt; trong tài liệu này có nghĩa là **phải**.

### Năng lực sử dụng tài liệu và tra cứu

| ID | Phát biểu yêu cầu (shall) | Lý do | Nguồn | Ưu tiên | Tiêu chí chấp nhận | Phương pháp xác minh | Trạng thái |
|---|---|---|---|---|---|---|---|
| BR-001 | Khi người dùng cần tra cứu tài liệu thuộc phạm vi MVP, người dùng **shall** có khả năng đưa một tệp PDF vào tập tài liệu phục vụ tra cứu. | Đầu vào nghiệp vụ nêu rõ tải PDF lên là năng lực cốt lõi. | BO-001 / SN-001; SRC-001 | Must | AC-001: Trong buổi trình diễn nghiệp vụ, người dùng chọn được một PDF thuộc phạm vi đã thống nhất và tệp đó xuất hiện trong tập tài liệu có thể dùng để hỏi đáp. Loại PDF, giới hạn kích thước/số lượng và xử lý PDF không đọc được [TBD: OQ-008]. | Demonstration; Inspection | Draft |
| BR-002 | Khi có PDF trong tập tài liệu phục vụ tra cứu, người dùng **shall** có khả năng đặt câu hỏi bằng ngôn ngữ tự nhiên về nội dung tài liệu đó. | Cho phép người dùng truy vấn thay vì tự tìm thủ công trong nhiều tệp. | BO-001 / SN-001; SRC-001 | Must | AC-002: Với bộ câu hỏi nghiệp vụ và PDF thử nghiệm đã được chủ nghiệp vụ duyệt, người dùng gửi được câu hỏi về nội dung tài liệu; danh sách câu hỏi thử nghiệm và tiêu chí hợp lệ [TBD: OQ-009]. | Demonstration; Test | Draft |
| BR-003 | Khi người dùng đặt câu hỏi về tập PDF đã tải lên, người dùng **shall** nhận được phản hồi AI có nội dung liên quan đến câu hỏi và tập tài liệu đó. | Đây là kết quả sử dụng được mô tả trực tiếp trong mục tiêu công cụ. | BO-001 / SN-001; SRC-001 | Must | AC-003: Với bộ câu hỏi và đáp án tham chiếu được chủ nghiệp vụ phê duyệt, phản hồi được đánh giá theo thang đo và ngưỡng đạt do chủ nghiệp vụ xác nhận trước thử nghiệm [TBD: OQ-009]. | Test; Review | Draft |

### Năng lực đánh giá giá trị nghiệp vụ

| ID | Phát biểu yêu cầu (shall) | Lý do | Nguồn | Ưu tiên | Tiêu chí chấp nhận | Phương pháp xác minh | Trạng thái |
|---|---|---|---|---|---|---|---|
| BR-004 | Trước khi kết thúc đánh giá MVP, chủ nghiệp vụ **shall** xác nhận kết quả đo MET-001 và MET-002 theo định nghĩa, baseline, mục tiêu và phương pháp đo đã được phê duyệt. | Tránh tuyên bố hiệu quả khi chưa có bằng chứng đo được. | BO-001 / BO-002 / SN-002; metric cần xác nhận OQ-005 | Should | AC-004: Biên bản đánh giá ghi rõ dữ liệu đầu vào, kết quả MET-001/MET-002, so sánh baseline/mục tiêu và quyết định của chủ nghiệp vụ; nếu chưa có mục tiêu được duyệt, kết quả được ghi là chưa thể kết luận. | Inspection; Analysis | Draft |

### Yêu cầu chất lượng được để mở

Độ chính xác tối thiểu, khả năng trích dẫn vị trí nguồn, thời gian phản hồi, khả năng xử lý PDF quét/OCR, ngôn ngữ, tính sẵn sàng, quyền truy cập, nhật ký hoạt động và thời hạn lưu/xóa dữ liệu chưa có căn cứ để viết thành yêu cầu đã xác nhận. Các nội dung này được giữ ở `OQ-008` đến `OQ-013`; không được hiểu là không cần thiết.

## 4.8. Quy tắc nghiệp vụ

| ID | Quy tắc | Loại | Phạm vi | Chủ sở hữu thực thi | Nguồn |
|---|---|---|---|---|---|
| BRU-001 | Chỉ được sử dụng trong MVP các tệp PDF mà tổ chức/người dùng có quyền cung cấp cho mục đích tra cứu; phạm vi quyền và cách xác minh phải được chủ sở hữu dữ liệu/pháp chế xác nhận trước triển khai. | Chính sách (dự thảo, chưa được phê duyệt) | Tài liệu đầu vào | [TBD: OQ-001, OQ-013] | [Chưa xác minh: OQ-012, OQ-013] |
| BRU-002 | Người dùng phải xem xét tính phù hợp của phản hồi trước khi sử dụng để đưa ra quyết định nghiệp vụ; phản hồi AI không mặc nhiên là phê duyệt hoặc nguồn sự thật có thẩm quyền. | Quyết định nghiệp vụ (đề xuất cần phê duyệt) | Sử dụng kết quả tra cứu | [TBD: OQ-001] | [Chưa xác minh: OQ-010] |

Không có quy tắc pháp lý, tính toán, chính sách lưu trữ hoặc phân quyền nào khác được cung cấp (`SRC-001`).

## 4.9. Ràng buộc

| ID | Ràng buộc | Loại | Bên áp đặt | Tác động | Nguồn |
|---|---|---|---|---|---|
| CON-001 | Sáng kiến được yêu cầu ở phạm vi MVP. Định nghĩa MVP, giới hạn chức năng và thời gian chưa được xác nhận. | Tổ chức/phạm vi | Quản lý/người yêu cầu | Cần xác định phạm vi tối thiểu và tiêu chí dừng/mở rộng. | SRC-001; chi tiết OQ-006 |
| CON-002 | Kênh nghiệp vụ được nêu là ứng dụng web. | Kênh/phạm vi | Người yêu cầu | Các phương án ngoài kênh web không thuộc phát biểu hiện tại; yêu cầu tiếp cận và môi trường dùng cần xác nhận. | SRC-001 |

Ngân sách, thời hạn, hợp đồng, nền tảng công nghệ, quy định pháp lý và tiêu chuẩn bảo mật chưa được cung cấp; không ghi nhận các yếu tố đó như ràng buộc đã xác nhận (`OQ-006`, `OQ-012`).

## 4.10. Giả định, phụ thuộc và rủi ro

| ID | Loại | Mô tả | Tác động nếu sai/chưa xử lý | Chủ sở hữu | Xác thực/giảm thiểu | Hạn |
|---|---|---|---|---|---|---|
| ASM-001 | Giả định | Đội phát triển kinh doanh là nhóm người dùng chính của MVP. | Phạm vi, nhu cầu và tiêu chí thử nghiệm có thể không phù hợp nhóm sử dụng thực tế. | [TBD: OQ-001] | Nhà bảo trợ xác nhận nhóm người dùng và đại diện tham gia thử nghiệm. | [TBD: OQ-006] |
| ASM-002 | Giả định | Có thể xác định một tập PDF đại diện và có quyền sử dụng để đánh giá MVP. | Không có dữ liệu thử nghiệm hợp lệ hoặc phát sinh rủi ro quyền dữ liệu. | [TBD: OQ-013] | Chủ sở hữu tài liệu/pháp chế xác nhận quyền, phân loại và tập dữ liệu được phép dùng. | Trước thử nghiệm |
| DEP-001 | Phụ thuộc | Nhà bảo trợ/chủ nghiệp vụ xác nhận KPI, baseline, mục tiêu, phương pháp đo và thời hạn đánh giá. | Không thể kết luận MVP có đạt mục tiêu nghiệp vụ. | [TBD: OQ-001] | Chốt MET-001/MET-002 qua phiên làm việc và biên bản quyết định. | [TBD: OQ-005, OQ-006] |
| DEP-002 | Phụ thuộc | Chủ sở hữu dữ liệu/pháp chế/bảo mật xác nhận quyền sử dụng, phân loại, lưu trữ và xử lý PDF. | Có thể không được phép đưa dữ liệu vào quy trình hoặc phải thay đổi phạm vi. | [TBD: OQ-013] | Rà soát chính sách hiện hành và phê duyệt tập dữ liệu thử nghiệm. | Trước khi tải dữ liệu thật |
| RSK-001 | Rủi ro | Nếu phản hồi AI không chính xác, thiếu căn cứ hoặc không phản ánh tài liệu, người dùng có thể sử dụng thông tin sai trong nghiệp vụ. | Ảnh hưởng chất lượng quyết định và niềm tin người dùng; mức độ chưa lượng hóa. | [TBD: OQ-001] | Xây dựng bộ câu hỏi/đáp án tham chiếu; xác định ngưỡng đạt và cách hiển thị/xác minh nguồn; thử nghiệm trước khi mở rộng (`OQ-009`, `OQ-010`). | Trước phê duyệt MVP |
| RSK-002 | Rủi ro | Nếu PDF chứa thông tin nhạy cảm hoặc không được phép xử lý, việc tải lên có thể vi phạm chính sách hoặc quyền của chủ sở hữu. | Có thể phải dừng thử nghiệm, xóa dữ liệu hoặc xử lý sự cố. | [TBD: OQ-013] | Xác định phân loại dữ liệu, phạm vi được phép, lưu giữ/xóa và người phê duyệt trước thử nghiệm (`OQ-012`, `OQ-013`). | Trước khi tải dữ liệu |
| RSK-003 | Rủi ro | Nếu không có baseline và tiêu chí thành công được duyệt, đánh giá MVP có thể không chứng minh được giá trị hoặc dẫn đến quyết định đầu tư thiếu căn cứ. | Không thể so sánh kết quả với hiện trạng. | [TBD: OQ-001] | Chốt phép đo và baseline trước thử nghiệm (`OQ-005`). | Trước thử nghiệm |
| RSK-004 | Rủi ro | Nếu không giới hạn loại, kích thước và số lượng PDF, độ phức tạp/phạm vi MVP có thể vượt khả năng thời gian hoặc nguồn lực. | Chậm tiến độ hoặc giảm chất lượng kiểm thử. | [TBD: OQ-001] | Chốt giới hạn MVP, quy mô thử nghiệm và thời hạn (`OQ-006`, `OQ-008`). | Trước baseline |

## 4.11. Truy vết

### Ma trận truy vết xuôi và ngược

| Mục tiêu nghiệp vụ | Nhu cầu bên liên quan | Yêu cầu nghiệp vụ | Tiêu chí chấp nhận | PRD/SRS tiếp theo |
|---|---|---|---|---|
| BO-001 | SN-001 | BR-001 | AC-001 | [TBD] |
| BO-001 | SN-001 | BR-002 | AC-002 | [TBD] |
| BO-001 | SN-001 | BR-003 | AC-003 | [TBD] |
| BO-001, BO-002 | SN-002 | BR-004 | AC-004 | [TBD] |
| BO-002 (dự thảo) | SN-003 | Chưa có yêu cầu trực tiếp; việc quản lý truy vết được phản ánh ở quy trình tài liệu, không phải năng lực MVP | — | [TBD] |
| Chưa xác định | SN-004 | Chưa thể viết yêu cầu dữ liệu/quyền khi quy tắc chưa được xác nhận | — | [TBD: OQ-012, OQ-013] |
| Chưa xác định | SN-005 | Chưa thể viết yêu cầu vận hành/chất lượng khi tiêu chí chưa được xác nhận | — | [TBD: OQ-008, OQ-011] |

### Báo cáo độ bao phủ

- **Mục tiêu chưa có yêu cầu:** Không có đối với BO-001 và BO-002 ở mức dự thảo; tuy nhiên BO-002 và tính hợp lệ của metric phải được xác nhận.
- **Yêu cầu không truy vết tới mục tiêu/nhu cầu:** Không có; BR-001–BR-004 đều truy vết tới BO/SN nêu trên.
- **Nhu cầu chưa có yêu cầu:** SN-003, SN-004 và SN-005 chưa có yêu cầu MVP tương ứng; xem `OQ-012`, `OQ-013` và `OQ-014`.
- **Yêu cầu thiếu tiêu chí chấp nhận/phương pháp xác minh:** Không có ở bản nháp; AC-001–AC-004 đã có phương pháp. Một số tiêu chí còn chờ ngưỡng hoặc bộ dữ liệu được phê duyệt (`OQ-008`, `OQ-009`).
- **Liên kết xuống PRD/SRS:** Chưa có mã tài liệu hạ nguồn; cần bổ sung khi tài liệu đó được tạo.

## 4.12. Câu hỏi mở và quyết định cần có

| ID | Câu hỏi/quyết định | Lý do | Chủ sở hữu | Cần trước | Trạng thái | Kết quả |
|---|---|---|---|---|---|---|
| OQ-001 | Ai là nhà bảo trợ, chủ nghiệp vụ, tác giả, người rà soát, người phê duyệt và đại diện từng nhóm liên quan? | Cần quyền quyết định, xác nhận yêu cầu và phân công trách nhiệm. | Quản lý/người yêu cầu | Trước rà soát BRD | Mở | — |
| OQ-002 | Tên tổ chức, tên sáng kiến chính thức và phân loại bảo mật của tài liệu là gì? | Cần hoàn thiện kiểm soát và phân phối tài liệu. | Nhà bảo trợ | Trước phê duyệt | Mở | — |
| OQ-003 | Quy trình hiện tại thực tế gồm những bước nào, ai tham gia, dùng công cụ nào và tác vụ tra cứu đại diện là gì? | Cần xác nhận vấn đề, điểm bắt đầu/kết thúc và phạm vi quy trình. | Chủ nghiệp vụ/đội phát triển kinh doanh | Trước baseline | Mở | — |
| OQ-004 | Có dữ liệu nào chứng minh thời gian, chi phí, lỗi, tần suất hoặc tác động của việc tra cứu thủ công? | Cần lượng hóa vấn đề và chi phí không hành động. | Chủ nghiệp vụ | Trước phê duyệt mục tiêu | Mở | — |
| OQ-005 | Định nghĩa, baseline, mục tiêu, phương pháp lấy mẫu, nguồn dữ liệu, tần suất và chủ sở hữu cho MET-001/MET-002 là gì? | Chưa thể xác nhận lợi ích khi chưa có cách đo được duyệt. | Nhà bảo trợ/chủ nghiệp vụ | Trước thử nghiệm MVP | Mở | — |
| OQ-006 | Thời hạn mục tiêu, ngân sách, nguồn lực, thời lượng thử nghiệm và định nghĩa “MVP” được phê duyệt là gì? | Cần đánh giá tính khả thi và giới hạn đầu tư. | Nhà bảo trợ | Trước baseline | Mở | — |
| OQ-007 | Các năng lực nào ngoài tải PDF và hỏi đáp là bắt buộc cho MVP; mục nào hoãn? | Phạm vi ngoài phần được mô tả chưa được quyết định. | Chủ nghiệp vụ/Product Owner | Trước baseline | Mở | — |
| OQ-008 | PDF nào được hỗ trợ (PDF có văn bản, PDF quét), giới hạn kích thước/số lượng, ngôn ngữ và hành vi khi tệp không đọc được là gì? | Cần tiêu chí khả thi và chấp nhận cho BR-001. | Chủ nghiệp vụ/nhóm kỹ thuật | Trước hoàn thiện AC-001 | Mở | — |
| OQ-009 | Bộ câu hỏi/đáp án tham chiếu, cách chấm mức liên quan/độ chính xác và ngưỡng đạt cho AC-002/AC-003 là gì? | Cần đánh giá được giá trị và chất lượng phản hồi. | Chủ nghiệp vụ | Trước kiểm thử nghiệp vụ | Mở | — |
| OQ-010 | Người dùng cần thấy căn cứ/vị trí nguồn trong PDF không; ai chịu trách nhiệm xác nhận câu trả lời trước khi sử dụng? | Ảnh hưởng khả năng kiểm chứng và cách sử dụng kết quả AI. | Chủ nghiệp vụ | Trước phê duyệt yêu cầu | Mở | — |
| OQ-011 | Có ngưỡng thời gian phản hồi, thời gian sẵn sàng, khả năng tiếp cận hoặc tiêu chí vận hành nào bắt buộc không? | Chưa có yêu cầu chất lượng phi chức năng được xác nhận. | Chủ nghiệp vụ/nhóm vận hành | Trước phê duyệt PRD/SRS | Mở | — |
| OQ-012 | Quy định/chính sách nào áp dụng cho dữ liệu PDF và nội dung câu hỏi/trả lời: phân loại, quyền truy cập, lưu trữ, xóa, vị trí xử lý và thời hạn lưu là gì? | Có thể ảnh hưởng tính hợp pháp và phạm vi xử lý dữ liệu. | Chủ sở hữu dữ liệu/pháp chế/bảo mật | Trước khi tải dữ liệu thật | Mở | — |
| OQ-013 | Ai sở hữu tài liệu thử nghiệm; có quyền sử dụng chúng không; những bên nào có thể ngăn hoặc hạn chế việc sử dụng? | Xác định quyền, trách nhiệm và bên có quyền phủ quyết. | Chủ sở hữu tài liệu/pháp chế | Trước khi chọn dữ liệu | Mở | — |
| OQ-014 | Có cần yêu cầu về phân quyền người dùng, phạm vi tài liệu riêng tư, nhật ký hoạt động hoặc hỗ trợ người dùng không? | Chưa xác định nhu cầu bảo mật và vận hành theo nhóm người dùng. | Chủ nghiệp vụ/bảo mật/vận hành | Trước baseline | Mở | —|

## 4.13. Thuật ngữ và tài liệu tham khảo

### Thuật ngữ

| Thuật ngữ | Định nghĩa |
|---|---|
| BRD | Tài liệu yêu cầu nghiệp vụ; nêu vấn đề, mục tiêu, bên liên quan và yêu cầu nghiệp vụ ở mức độc lập với giải pháp. |
| MVP | Sản phẩm khả dụng tối thiểu; phạm vi tối thiểu cụ thể của sáng kiến này chưa được xác nhận (`OQ-006`). |
| PDF | Định dạng tài liệu PDF; loại nội dung và đặc tính tệp được hỗ trợ chưa xác nhận (`OQ-008`). |
| Metric/KPI | Chỉ số dùng để đo kết quả; chỉ số nêu tại BRD này là đề xuất chờ phê duyệt. |
| Tập tài liệu phục vụ tra cứu | Các PDF đã được đưa vào phạm vi để người dùng đặt câu hỏi; quyền sở hữu, phạm vi chia sẻ và thời hạn tồn tại chưa xác định. |
| Câu trả lời liên quan | Câu trả lời phù hợp với câu hỏi và nội dung tài liệu theo tiêu chí do chủ nghiệp vụ phê duyệt; chưa đồng nghĩa với câu trả lời chính xác cho đến khi có tiêu chí đánh giá (`OQ-009`). |

### Tài liệu tham khảo

| ID | Tên/phiên bản | Vị trí | Ngày truy cập | Nội dung hỗ trợ |
|---|---|---|---|---|
| SRC-001 | BRD Prompt IEEE Standard, phiên bản 1.0; phần “Business foundation” | `docs/BRD_Prompt_IEEE_standard.md` trong workspace | 19/10/2026 | Mô tả bối cảnh giả định, vấn đề, yêu cầu MVP và kênh web. |

Không có business case, phỏng vấn, chính sách, dữ liệu đo lường, tài liệu hệ thống hoặc nguồn bên ngoài nào khác được cung cấp.

## 4.14. Phê duyệt

| Vai trò | Tên | Quyết định | Chữ ký/ngày |
|---|---|---|---|
| Nhà bảo trợ điều hành | [TBD: OQ-001] | Chưa quyết định | — |
| Chủ nghiệp vụ | [TBD: OQ-001] | Chưa quyết định | — |
| Product Manager/Product Owner | [TBD: OQ-001] | Chưa quyết định | — |
| Pháp chế/bảo mật (nếu áp dụng) | [TBD: OQ-001, OQ-012] | Chưa quyết định | — |

**Điều kiện phê duyệt:** xác nhận chủ thể và quyền phê duyệt (`OQ-001`); chốt vấn đề, quy trình và dữ liệu cơ sở (`OQ-003`–`OQ-005`); thống nhất phạm vi, nguồn lực và thời hạn MVP (`OQ-006`–`OQ-008`); duyệt tiêu chí đánh giá chất lượng câu trả lời (`OQ-009`, `OQ-010`); xác nhận chính sách dữ liệu và các yêu cầu vận hành liên quan (`OQ-011`–`OQ-014`). Phiên bản baseline được phê duyệt: chưa có.

## 4.15. Phụ lục

Phân tích hiện có chỉ dựa trên mô tả ngắn trong `SRC-001`. Chưa có biên bản phỏng vấn, dữ liệu trích xuất, sơ đồ quy trình đã xác nhận, tài liệu chính sách hoặc kết quả thử nghiệm để đính kèm. Mermaid trong mục 4.3 là sơ đồ khái quát cần được nghiệp vụ xác nhận.

## 5. Danh sách kiểm tra xác minh và rà soát

### 5.1. Chất lượng yêu cầu

| Kiểm tra | Kết quả | Ghi chú |
|---|---|---|
| Mỗi yêu cầu dùng từ quy phạm shall và chỉ có một nghĩa vụ | Đạt ở mức bản nháp | BR-001–BR-004; cần rà soát nghiệp vụ trước baseline. |
| Yêu cầu không quy định thiết kế kỹ thuật | Đạt | Không chỉ định kiến trúc, nhà cung cấp hoặc công nghệ triển khai. |
| Định lượng khi số lượng ảnh hưởng nghiệm thu | Chưa đạt đầy đủ | Ngưỡng PDF, chất lượng, thời gian và KPI chờ OQ-005, OQ-008, OQ-009, OQ-011. |
| Không còn từ mơ hồ chưa định nghĩa | Chưa đạt | “MVP”, “liên quan”, “thành công” cần định nghĩa/xác nhận (`OQ-006`, `OQ-009`). |
| Thuật ngữ chuyên ngành có trong bảng thuật ngữ | Đạt ở mức bản nháp | Định nghĩa sẽ cần cập nhật theo quyết định nghiệp vụ. |
| Không có yêu cầu trùng lặp hoặc mâu thuẫn đã biết | Đạt theo đầu vào hiện có | Chưa thay thế rà soát với các bên liên quan. |
| Mỗi yêu cầu có mã duy nhất | Đạt | BR-001–BR-004. |

### 5.2. Tính đầy đủ và truy vết

| Kiểm tra | Kết quả | Ghi chú |
|---|---|---|
| Mỗi mục tiêu có ít nhất một yêu cầu | Đạt có điều kiện | BO-001/BO-002; BO-002 và metric là đề xuất chờ xác nhận. |
| Mỗi yêu cầu truy vết về mục tiêu hoặc nhu cầu | Đạt | Thể hiện tại mục 4.11. |
| Mỗi yêu cầu có ít nhất một tiêu chí chấp nhận | Đạt có điều kiện | AC-001–AC-004; một số ngưỡng chờ quyết định. |
| Mỗi yêu cầu có phương pháp xác minh | Đạt | Demonstration/Test/Inspection/Analysis được nêu trong bảng yêu cầu. |
| Mỗi nhóm bên liên quan có ít nhất một nhu cầu | Đạt ở mức dự thảo | STK-004/STK-005 là nhóm cần xác nhận. |
| Phạm vi, giả định, phụ thuộc, rủi ro được ghi nhận | Đạt ở mức dự thảo | Nhiều mục còn cần chủ sở hữu và xác nhận. |
| Mỗi câu hỏi mở có chủ sở hữu và hạn cần có | Chưa đạt | Có ID, lý do và trạng thái; chủ sở hữu/hạn cụ thể cần được chỉ định (`OQ-001`). |

### 5.3. Xác nhận nghiệp vụ

| Kiểm tra | Kết quả | Ghi chú |
|---|---|---|
| Vấn đề có bằng chứng | Chưa đạt đầy đủ | Chỉ có mô tả định tính `SRC-001`; cần xác nhận và dữ liệu (`OQ-003`, `OQ-004`). |
| Baseline và mục tiêu được đo lường, có nguồn | Chưa đạt | Chưa có số liệu; `OQ-005`. |
| Lợi ích và chi phí được trình bày theo nghiệp vụ | Chưa đạt đầy đủ | Lợi ích mới định tính; chi phí đầu tư và chi phí không hành động chưa có dữ liệu (`OQ-004`, `OQ-006`). |
| Nhà bảo trợ xác nhận vấn đề và kết quả | Chưa đạt | Chưa xác định người bảo trợ (`OQ-001`). |
| Tài liệu có thể hiểu bởi độc giả nghiệp vụ | Đạt ở mức bản nháp | Dùng thuật ngữ nghiệp vụ và nêu rõ nội dung chưa xác minh. |

Các điểm chưa đạt được ghi nhận thành câu hỏi mở/điều kiện, không được xem là đã thông qua. Các yêu cầu Must chưa đủ điều kiện để baseline vì tiêu chí nghiệp vụ và giới hạn dữ liệu còn mở.

## 6. Tuyên bố mức độ sẵn sàng

**Not ready — Chưa sẵn sàng phê duyệt hoặc baseline.** Nội dung cốt lõi của vấn đề và năng lực MVP được ghi nhận theo `SRC-001`, nhưng còn thiếu bằng chứng định lượng, người có thẩm quyền, mục tiêu/tiêu chí đo lường, giới hạn dữ liệu và ngưỡng chấp nhận. Các mục chặn chính: `OQ-001`, `OQ-003`–`OQ-006`, `OQ-008`–`OQ-010`, `OQ-012`–`OQ-013`.
