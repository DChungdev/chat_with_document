"""Bộ câu hỏi chuẩn khởi điểm (D7). TỔNG HỢP và dùng dữ liệu bịa — không chứa thông tin thật.

Mục đích: chạy được pipeline đầu-cuối một cách lặp lại để so sánh cấu hình. KHÔNG thay thế bộ câu hỏi
thật do Lan/PO cung cấp trên tài liệu thật [TBD: OQ-009]; số liệu trên bộ này chỉ phản ánh đường ống
và mô hình đang cắm vào (với embedding/LLM giả thì chỉ là kiểm tra đường ống).

Mỗi tài liệu có 3 trang; mỗi sự kiện (fact) nằm ở một trang cố định để kiểm tra trích dẫn đúng trang.
Câu hỏi được diễn đạt lại, không sao chép nguyên câu của tài liệu.
"""

from __future__ import annotations

from dataclasses import dataclass

# Câu đệm dùng chung ở mọi tài liệu: tạo nhiễu giống tài liệu thật (điều khoản mẫu, văn phong hành chính).
FILLER = [
    "Hai bên cam kết thực hiện đầy đủ các nội dung đã được thỏa thuận trong văn bản này.",
    "Mọi thay đổi chỉ có hiệu lực khi được cả hai bên đồng ý bằng văn bản.",
    "Văn bản được lập thành hai bản có giá trị pháp lý như nhau.",
    "Các nội dung chưa được quy định sẽ được hai bên trao đổi và thống nhất sau.",
]


@dataclass(frozen=True)
class Fact:
    page: int  # 1..3
    sentence: str
    question: str
    keyword: str  # phải xuất hiện trong câu trả lời đúng


@dataclass(frozen=True)
class Doc:
    name: str
    title: str
    facts: tuple[Fact, ...]


DOCS: tuple[Doc, ...] = (
    Doc(
        "baogia_thiet_bi.pdf",
        "BÁO GIÁ THIẾT BỊ CAMERA",
        (
            Fact(
                1,
                "Giá trọn gói của hệ thống camera giám sát là 250 triệu đồng đã bao gồm thuế giá trị gia tăng.",
                "Hệ thống camera giám sát trọn gói có giá bao nhiêu triệu đồng?",
                "250 triệu",
            ),
            Fact(
                1,
                "Thời gian giao hàng và lắp đặt camera tối đa là 15 ngày làm việc kể từ ngày ký hợp đồng.",
                "Giao hàng và lắp đặt camera mất tối đa bao nhiêu ngày làm việc?",
                "15 ngày",
            ),
            Fact(
                2,
                "Bên bán bảo hành thiết bị camera trong 24 tháng kể từ ngày nghiệm thu.",
                "Thiết bị camera được bảo hành bao lâu kể từ ngày nghiệm thu?",
                "24 tháng",
            ),
            Fact(
                3,
                "Báo giá này có hiệu lực trong 30 ngày kể từ ngày phát hành.",
                "Báo giá có hiệu lực trong bao nhiêu ngày kể từ ngày phát hành?",
                "30 ngày",
            ),
        ),
    ),
    Doc(
        "hopdong_dich_vu.pdf",
        "HỢP ĐỒNG DỊCH VỤ BẢO TRÌ",
        (
            Fact(
                1,
                "Phí bảo trì hằng năm bằng 8 phần trăm giá trị hợp đồng dịch vụ.",
                "Phí bảo trì hằng năm là bao nhiêu phần trăm giá trị hợp đồng dịch vụ?",
                "8 phần trăm",
            ),
            Fact(
                2,
                "Bên mua thanh toán trong vòng 30 ngày kể từ khi nhận hóa đơn hợp lệ.",
                "Bên mua phải thanh toán trong bao nhiêu ngày kể từ khi nhận hóa đơn hợp lệ?",
                "30 ngày",
            ),
            Fact(
                2,
                "Khoản thanh toán chậm chịu lãi suất 0,05 phần trăm mỗi ngày chậm.",
                "Thanh toán chậm bị tính lãi suất bao nhiêu mỗi ngày chậm?",
                "0,05 phần trăm",
            ),
            Fact(
                3,
                "Mỗi bên muốn chấm dứt hợp đồng phải báo trước cho bên kia 60 ngày.",
                "Muốn chấm dứt hợp đồng thì phải báo trước cho bên kia bao nhiêu ngày?",
                "60 ngày",
            ),
        ),
    ),
    Doc(
        "chinh_sach_nghi_phep.pdf",
        "CHÍNH SÁCH NGHỈ PHÉP NHÂN VIÊN",
        (
            Fact(
                1,
                "Nhân viên chính thức được hưởng 12 ngày nghỉ phép năm có lương.",
                "Nhân viên chính thức được hưởng bao nhiêu ngày nghỉ phép năm có lương?",
                "12 ngày",
            ),
            Fact(
                1,
                "Nghỉ ốm được hưởng 75 phần trăm lương trong tối đa 30 ngày mỗi năm.",
                "Nghỉ ốm được hưởng bao nhiêu phần trăm lương trong tối đa 30 ngày mỗi năm?",
                "75 phần trăm",
            ),
            Fact(
                2,
                "Nhân viên phải đăng ký nghỉ phép trước ít nhất 3 ngày làm việc.",
                "Phải đăng ký nghỉ phép trước ít nhất bao nhiêu ngày làm việc?",
                "3 ngày làm việc",
            ),
            Fact(
                3,
                "Ngày phép chưa dùng được chuyển sang năm sau tối đa 5 ngày.",
                "Ngày phép chưa dùng chuyển sang năm sau được tối đa bao nhiêu ngày?",
                "5 ngày",
            ),
        ),
    ),
    Doc(
        "quy_trinh_mua_sam.pdf",
        "QUY TRÌNH MUA SẮM NỘI BỘ",
        (
            Fact(
                1,
                "Đề nghị mua sắm có giá trị trên 50 triệu đồng phải kèm 3 báo giá cạnh tranh.",
                "Đề nghị mua sắm trên 50 triệu đồng phải kèm mấy báo giá cạnh tranh?",
                "3 báo giá",
            ),
            Fact(
                2,
                "Giám đốc phê duyệt các khoản mua sắm có giá trị trên 200 triệu đồng.",
                "Ai phê duyệt các khoản mua sắm có giá trị trên 200 triệu đồng?",
                "Giám đốc",
            ),
            Fact(
                2,
                "Phòng kế toán thanh toán cho nhà cung cấp trong vòng 45 ngày sau nghiệm thu.",
                "Phòng kế toán thanh toán cho nhà cung cấp trong vòng bao nhiêu ngày sau nghiệm thu?",
                "45 ngày",
            ),
            Fact(
                3,
                "Hồ sơ mua sắm được lưu trữ trong 10 năm kể từ ngày kết thúc.",
                "Hồ sơ mua sắm được lưu trữ trong bao nhiêu năm kể từ ngày kết thúc?",
                "10 năm",
            ),
        ),
    ),
    Doc(
        "huong_dan_bao_mat.pdf",
        "HƯỚNG DẪN AN TOÀN THÔNG TIN",
        (
            Fact(
                1,
                "Mật khẩu tài khoản phải có tối thiểu 12 ký tự gồm chữ hoa, chữ thường và số.",
                "Mật khẩu tài khoản phải có tối thiểu bao nhiêu ký tự?",
                "12 ký tự",
            ),
            Fact(
                1,
                "Người dùng phải đổi mật khẩu định kỳ sau mỗi 90 ngày.",
                "Người dùng phải đổi mật khẩu định kỳ sau mỗi bao nhiêu ngày?",
                "90 ngày",
            ),
            Fact(
                2,
                "Mọi sự cố an ninh phải được báo cho bộ phận an ninh mạng trong vòng 24 giờ.",
                "Sự cố an ninh phải báo cho bộ phận an ninh mạng trong vòng bao nhiêu giờ?",
                "24 giờ",
            ),
            Fact(
                3,
                "Hệ thống sao lưu dữ liệu tự động hằng đêm vào lúc 2 giờ sáng.",
                "Hệ thống sao lưu dữ liệu tự động hằng đêm vào lúc mấy giờ?",
                "2 giờ sáng",
            ),
        ),
    ),
    Doc(
        "bien_ban_nghiem_thu.pdf",
        "BIÊN BẢN NGHIỆM THU PHẦN MỀM KẾ TOÁN",
        (
            Fact(
                1,
                "Dự án phần mềm kế toán được nghiệm thu vào ngày 15 tháng 3 năm 2026.",
                "Dự án phần mềm kế toán được nghiệm thu vào ngày nào?",
                "15 tháng 3",
            ),
            Fact(
                2,
                "Còn 4 lỗi mức thấp cần được nhà thầu sửa trong vòng 10 ngày.",
                "Nhà thầu phải sửa các lỗi mức thấp còn lại trong vòng bao nhiêu ngày?",
                "10 ngày",
            ),
            Fact(
                2,
                "Tổng giá trị nghiệm thu của dự án phần mềm là 1,2 tỷ đồng.",
                "Tổng giá trị nghiệm thu của dự án phần mềm là bao nhiêu tỷ đồng?",
                "1,2 tỷ",
            ),
            Fact(
                3,
                "Nhà thầu đào tạo cho 20 người dùng trong 2 buổi.",
                "Nhà thầu đào tạo cho bao nhiêu người dùng trong 2 buổi?",
                "20 người",
            ),
        ),
    ),
    Doc(
        "thue_van_phong.pdf",
        "THỎA THUẬN THUÊ VĂN PHÒNG",
        (
            Fact(
                1,
                "Diện tích văn phòng cho thuê là 180 mét vuông tại tầng 5.",
                "Diện tích văn phòng cho thuê là bao nhiêu mét vuông?",
                "180 mét vuông",
            ),
            Fact(
                1,
                "Giá thuê văn phòng là 45 triệu đồng mỗi tháng chưa gồm phí quản lý.",
                "Giá thuê văn phòng mỗi tháng là bao nhiêu triệu đồng?",
                "45 triệu",
            ),
            Fact(
                2,
                "Bên thuê đặt cọc tương đương ba tháng tiền thuê văn phòng.",
                "Bên thuê phải đặt cọc tương đương mấy tháng tiền thuê văn phòng?",
                "ba tháng",
            ),
            Fact(
                3,
                "Thời hạn thuê văn phòng là 36 tháng kể từ ngày bàn giao mặt bằng.",
                "Thời hạn thuê văn phòng là bao nhiêu tháng kể từ ngày bàn giao mặt bằng?",
                "36 tháng",
            ),
        ),
    ),
    Doc(
        "quy_che_hoc_bong.pdf",
        "QUY CHẾ XÉT HỌC BỔNG",
        (
            Fact(
                1,
                "Sinh viên cần điểm trung bình tích lũy tối thiểu 3,2 để được xét học bổng.",
                "Sinh viên cần điểm trung bình tích lũy tối thiểu bao nhiêu để được xét học bổng?",
                "3,2",
            ),
            Fact(
                2,
                "Học bổng toàn phần miễn 100 phần trăm học phí trong một năm học.",
                "Học bổng toàn phần miễn bao nhiêu phần trăm học phí trong một năm học?",
                "100 phần trăm",
            ),
            Fact(
                2,
                "Hạn cuối nộp hồ sơ xét học bổng là ngày 30 tháng 9.",
                "Hạn cuối nộp hồ sơ xét học bổng là ngày nào?",
                "30 tháng 9",
            ),
            Fact(
                3,
                "Mỗi năm học nhà trường xét cấp 50 suất học bổng.",
                "Mỗi năm học nhà trường xét cấp bao nhiêu suất học bổng?",
                "50 suất",
            ),
        ),
    ),
    Doc(
        "chinh_sach_hoan_tra.pdf",
        "CHÍNH SÁCH ĐỔI TRẢ HÀNG",
        (
            Fact(
                1,
                "Khách hàng được trả hàng trong vòng 7 ngày kể từ khi nhận hàng.",
                "Khách hàng được trả hàng trong vòng bao nhiêu ngày kể từ khi nhận hàng?",
                "7 ngày",
            ),
            Fact(
                1,
                "Sản phẩm trả lại phải còn nguyên tem mác và bao bì.",
                "Sản phẩm trả lại phải còn nguyên những gì?",
                "tem mác",
            ),
            Fact(
                2,
                "Cửa hàng hoàn tiền trong 5 ngày làm việc sau khi nhận lại sản phẩm.",
                "Cửa hàng hoàn tiền trong bao nhiêu ngày làm việc sau khi nhận lại sản phẩm?",
                "5 ngày làm việc",
            ),
            Fact(
                3,
                "Phí vận chuyển trả hàng do khách hàng chịu nếu lỗi thuộc về khách hàng.",
                "Ai chịu phí vận chuyển trả hàng nếu lỗi thuộc về khách hàng?",
                "khách hàng chịu",
            ),
        ),
    ),
    Doc(
        "ke_hoach_trien_khai.pdf",
        "KẾ HOẠCH TRIỂN KHAI DỰ ÁN",
        (
            Fact(
                1,
                "Giai đoạn khảo sát yêu cầu kéo dài 4 tuần đầu tiên của dự án.",
                "Giai đoạn khảo sát yêu cầu kéo dài bao nhiêu tuần?",
                "4 tuần",
            ),
            Fact(
                1,
                "Nhóm dự án gồm 8 thành viên do một quản lý dự án phụ trách.",
                "Nhóm dự án gồm bao nhiêu thành viên?",
                "8 thành viên",
            ),
            Fact(
                2,
                "Ngân sách dự kiến cho toàn bộ dự án là 900 triệu đồng.",
                "Ngân sách dự kiến cho toàn bộ dự án là bao nhiêu triệu đồng?",
                "900 triệu",
            ),
            Fact(
                3,
                "Cuộc họp tiến độ được tổ chức vào thứ Hai hằng tuần.",
                "Cuộc họp tiến độ được tổ chức vào thứ mấy hằng tuần?",
                "thứ Hai",
            ),
        ),
    ),
)

# Câu hỏi NGOÀI phạm vi: tài liệu không chứa đáp án — hệ thống phải trả “không tìm thấy”.
OUT_OF_SCOPE: tuple[str, ...] = (
    "Thời tiết Hà Nội ngày mai ra sao?",
    "Thủ đô của nước Pháp là thành phố nào?",
    "Cách nấu một nồi phở bò ngon tại nhà?",
    "Đội tuyển nào vô địch World Cup năm 2022?",
    "Hướng dẫn cài đặt hệ điều hành trên máy tính xách tay mới?",
    "Con sông dài nhất thế giới là sông nào?",
    "Tỷ giá đô la Mỹ hôm nay là bao nhiêu?",
    "Ai là tác giả của truyện Kiều?",
    "Làm sao để tập chạy bộ cho người mới bắt đầu?",
    "Nên trồng loại cây nào trong chung cư?",
    "Ngọn núi cao nhất Việt Nam tên là gì?",
    "Phim nào đang chiếu rạp cuối tuần này?",
)


def page_text(doc: Doc, page: int) -> str:
    """Nội dung một trang: tiêu đề (trang 1), các sự kiện của trang và câu đệm giống nhau ở mọi tài liệu."""
    lines = [doc.title] if page == 1 else []
    for i, fact in enumerate(f for f in doc.facts if f.page == page):
        lines.append(fact.sentence)
        lines.append(FILLER[(i + page) % len(FILLER)])
    if not any(f.page == page for f in doc.facts):
        lines.append(FILLER[page % len(FILLER)])
    return "\n".join(lines)


def doc_pages(doc: Doc) -> list[str]:
    return [page_text(doc, p) for p in (1, 2, 3)]
