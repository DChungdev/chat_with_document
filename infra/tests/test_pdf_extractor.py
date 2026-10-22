"""C3: trích xuất văn bản PDF theo trang và phân loại lỗi."""

from __future__ import annotations

import pytest

from docchat_core.ports.ingest import ExtractionError
from docchat_infra.pdf import PypdfExtractor
from docchat_infra.pdf.synthetic import encrypt_pdf, make_pdf

ex = PypdfExtractor()


def code(data: bytes, max_pages: int = 100) -> str:
    with pytest.raises(ExtractionError) as ei:
        ex.extract(data, max_pages=max_pages)
    return ei.value.code


def test_extracts_vietnamese_text_per_page_in_order() -> None:
    pages = ex.extract(
        make_pdf(["Điều khoản thanh toán\nTrong vòng 30 ngày.", "Bảo hành 12 tháng.", "Hết."]),
        max_pages=10,
    )
    assert [p.number for p in pages] == [1, 2, 3]
    assert "Điều khoản thanh toán" in pages[0].text and "Trong vòng 30 ngày." in pages[0].text
    assert "Bảo hành 12 tháng." in pages[1].text and pages[2].text.strip() == "Hết."


def test_blank_page_among_text_pages_is_kept_with_correct_numbering() -> None:
    pages = ex.extract(make_pdf(["Một", "", "Ba"]), max_pages=10)
    assert [p.number for p in pages] == [1, 2, 3] and pages[1].text.strip() == ""


def test_scanned_pdf_without_text_layer_is_no_text() -> None:
    assert code(make_pdf(["", "", ""])) == "NO_TEXT"


def test_password_protected_pdf() -> None:
    assert code(encrypt_pdf(make_pdf(["bí mật"]), "mat-khau")) == "PDF_PASSWORD"


@pytest.mark.parametrize(
    "data",
    [b"", b"khong phai pdf", b"%PDF-1.4 garbage", make_pdf(["abc"])[:150]],
    ids=["empty", "text", "header-only", "truncated"],
)
def test_corrupt_input_is_pdf_corrupt_and_never_crashes(data: bytes) -> None:
    assert code(data) == "PDF_CORRUPT"


def test_page_limit() -> None:
    data = make_pdf(["a"] * 5)
    assert code(data, max_pages=4) == "PDF_TOO_MANY_PAGES"
    assert len(ex.extract(data, max_pages=5)) == 5


def test_time_budget_stops_pathological_pdf() -> None:
    ticks = iter(range(0, 1000, 100))
    slow = PypdfExtractor(max_seconds=150, monotonic=lambda: float(next(ticks)))
    with pytest.raises(ExtractionError) as ei:
        slow.extract(make_pdf(["a"] * 10), max_pages=100)
    assert ei.value.code == "PDF_TOO_COMPLEX"


def test_error_messages_never_contain_pdf_content() -> None:
    secret = "NOI-DUNG-NHAY-CAM"
    with pytest.raises(ExtractionError) as ei:
        ex.extract(encrypt_pdf(make_pdf([secret]), "pw"), max_pages=10)
    assert secret not in str(ei.value) and secret not in repr(ei.value)


def test_one_unreadable_page_does_not_fail_the_document(monkeypatch: pytest.MonkeyPatch) -> None:
    from pypdf import PageObject

    original = PageObject.extract_text
    calls = {"n": 0}

    def flaky(self: PageObject, *a: object, **k: object) -> str:
        calls["n"] += 1
        if calls["n"] == 2:
            raise ValueError("trang hỏng")
        return original(self, *a, **k)  # type: ignore[no-any-return]

    monkeypatch.setattr(PageObject, "extract_text", flaky)
    pages = ex.extract(make_pdf(["Một", "Hai", "Ba"]), max_pages=10)
    assert [p.text.strip() for p in pages] == ["Một", "", "Ba"]
