"""Sinh PDF mẫu (tổng hợp) cho test e2e: python scripts/make_fixtures.py"""

from pathlib import Path

from docchat_infra.pdf.synthetic import encrypt_pdf, make_pdf

OUT = Path(__file__).resolve().parents[1] / "apps" / "web" / "e2e" / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)

baogia = make_pdf(
    [
        "BÁO GIÁ THIẾT BỊ\nGiá trọn gói của hệ thống camera là 250 triệu đồng đã bao gồm thuế.",
        "ĐIỀU KHOẢN THANH TOÁN\nThanh toán trong vòng 30 ngày kể từ ngày nhận hóa đơn hợp lệ.",
        "BẢO HÀNH\nThiết bị camera được bảo hành 24 tháng kể từ ngày nghiệm thu.",
    ]
)
(OUT / "baogia.pdf").write_bytes(baogia)
(OUT / "hopdong.pdf").write_bytes(
    make_pdf(["HỢP ĐỒNG DỊCH VỤ\nPhí bảo trì hằng năm bằng 8 phần trăm giá trị hợp đồng dịch vụ."])
)
(OUT / "scan.pdf").write_bytes(make_pdf(["", ""]))  # PDF quét: không có lớp văn bản
(OUT / "matkhau.pdf").write_bytes(encrypt_pdf(make_pdf(["Nội dung bí mật"]), "mat-khau"))
(OUT / "khong-phai-pdf.pdf").write_bytes(b"day khong phai la mot tep pdf that")
print("ok", sorted(p.name for p in OUT.iterdir()))
