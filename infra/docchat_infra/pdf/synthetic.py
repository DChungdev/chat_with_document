"""Sinh PDF tổng hợp có lớp văn bản Unicode (kể cả tiếng Việt) cho test và benchmark.

Không dùng cho production. PDF dùng font Type0/Identity-H không nhúng kèm bảng ToUnicode ánh xạ
mã ký tự → Unicode, nên pypdf trích xuất đúng văn bản dù PDF không hiển thị đẹp trong trình xem.
"""

from __future__ import annotations

import io

from pypdf import PdfReader, PdfWriter

_PAGE_W, _PAGE_H = 595, 842


def _hex(text: str) -> str:
    return "".join(f"{ord(ch):04X}" for ch in text if ord(ch) <= 0xFFFF)


def _to_unicode_cmap(chars: set[str]) -> bytes:
    codes = sorted({ord(c) for c in chars if ord(c) <= 0xFFFF})
    blocks = []
    for i in range(0, len(codes), 100):  # tối đa 100 mục mỗi khối beginbfchar
        part = codes[i : i + 100]
        body = "\n".join(f"<{c:04X}> <{c:04X}>" for c in part)
        blocks.append(f"{len(part)} beginbfchar\n{body}\nendbfchar")
    return (
        "/CIDInit /ProcSet findresource begin 12 dict begin begincmap\n"
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
        "/CMapName /Adobe-Identity-UCS def /CMapType 2 def\n"
        "1 begincodespacerange <0000> <FFFF> endcodespacerange\n"
        + "\n".join(blocks)
        + "\nendcmap CMapName currentdict /CMap defineresource pop end end"
    ).encode("ascii")


def make_pdf(pages: list[str], *, font_size: int = 11) -> bytes:
    """Mỗi phần tử của `pages` là văn bản một trang ('' = trang không có chữ, như PDF quét)."""
    chars = {ch for text in pages for ch in text if ch != "\n"}
    objs: list[bytes] = []  # objs[i] là đối tượng số i+1

    def add(body: bytes) -> int:
        objs.append(body)
        return len(objs)

    def stream(content: bytes) -> bytes:
        return b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream"

    catalog = add(b"")  # 1: điền sau
    pages_root = add(b"")  # 2: điền sau
    cmap = add(stream(_to_unicode_cmap(chars)))
    cid_font = add(
        b"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /Helvetica "
        b"/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> >>"
    )
    font = add(
        b"<< /Type /Font /Subtype /Type0 /BaseFont /Helvetica /Encoding /Identity-H "
        b"/DescendantFonts [%d 0 R] /ToUnicode %d 0 R >>" % (cid_font, cmap)
    )

    page_ids = []
    for text in pages:
        lines = [ln for ln in text.split("\n")] if text else []
        ops = [f"BT /F1 {font_size} Tf 50 {_PAGE_H - 60} Td {font_size + 3} TL"]
        ops += [f"<{_hex(ln)}> Tj T*" for ln in lines]
        ops.append("ET")
        content = add(stream("\n".join(ops).encode("ascii") if lines else b""))
        page_ids.append(
            add(
                b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] "
                b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"
                % (pages_root, _PAGE_W, _PAGE_H, font, content)
            )
        )
    objs[catalog - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages_root
    kids = b" ".join(b"%d 0 R" % p for p in page_ids)
    objs[pages_root - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(page_ids))

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % i + body + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1))
    for off in offsets:
        out.write(b"%010d 00000 n \n" % off)
    out.write(
        b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objs) + 1, catalog, xref)
    )
    return out.getvalue()


def encrypt_pdf(data: bytes, password: str) -> bytes:
    """Đặt mật khẩu MỞ tệp (người dùng) — pypdf không giải mã được bằng mật khẩu rỗng."""
    writer = PdfWriter()
    for page in PdfReader(io.BytesIO(data)).pages:
        writer.add_page(page)
    writer.encrypt(user_password=password, owner_password=password + "-owner", algorithm="AES-256")
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
