import unicodedata

import pytest

from docchat_core.application.chunking import (
    ChunkingConfig,
    chunk_pages,
    clean_pages,
    estimate_tokens,
)
from docchat_core.ports.ingest import PageText

SENT = "Điều khoản thanh toán quy định rõ thời hạn và phương thức thanh toán giữa hai bên. "


def page(n: int, text: str) -> PageText:
    return PageText(n, text)


def long_page(n: int, sentences: int = 12) -> PageText:
    return page(n, (SENT * sentences).strip())


SMALL = ChunkingConfig(max_tokens=60, overlap_tokens=15, min_tokens=5)


# ---------- chunking ----------
def test_chunks_respect_size_pages_and_numbering() -> None:
    pages = [long_page(i) for i in range(1, 6)]
    chunks = chunk_pages(pages, SMALL)
    assert len(chunks) > 5
    assert [c.ordinal for c in chunks] == list(range(len(chunks)))
    for c in chunks:
        assert c.token_count <= SMALL.max_tokens
        assert 1 <= c.page_start <= c.page_end <= 5
        assert c.page_end - c.page_start < SMALL.max_page_span  # không vượt quá 2 trang
        assert c.text.strip() == c.text and c.text


def test_chunk_covers_all_pages_in_order() -> None:
    chunks = chunk_pages([long_page(i) for i in range(1, 5)], SMALL)
    starts = [c.page_start for c in chunks]
    assert starts == sorted(starts) and starts[0] == 1 and chunks[-1].page_end == 4


def test_overlap_repeats_trailing_text_in_next_chunk() -> None:
    chunks = chunk_pages([long_page(1, 20)], SMALL)
    assert len(chunks) >= 3
    shared = 0
    for prev, nxt in zip(chunks, chunks[1:], strict=False):
        last_sentence = prev.text.split(". ")[-1]
        shared += int(last_sentence in nxt.text)
    assert shared >= len(chunks) - 2  # hầu hết cặp chunk liền kề có phần chồng lấn


def test_no_overlap_when_configured_zero() -> None:
    cfg = ChunkingConfig(max_tokens=60, overlap_tokens=0, min_tokens=5)
    chunks = chunk_pages([long_page(1, 20)], cfg)
    joined = " ".join(c.text for c in chunks)
    assert joined.count(SENT.strip()) == 20  # mỗi câu đúng một lần


def test_is_deterministic() -> None:
    pages = [long_page(i) for i in range(1, 4)]
    assert chunk_pages(pages, SMALL) == chunk_pages(pages, SMALL)


def test_long_text_without_punctuation_is_split_by_words() -> None:
    words = " ".join(f"tu{i}" for i in range(400))
    chunks = chunk_pages([page(1, words)], SMALL)
    assert len(chunks) > 3 and all(c.token_count <= SMALL.max_tokens for c in chunks)
    assert " ".join(c.text for c in chunks).count("tu399") >= 1


def test_single_gigantic_word_is_hard_split() -> None:
    chunks = chunk_pages([page(1, "x" * 5000)], SMALL)
    assert len(chunks) > 1 and all(c.token_count <= SMALL.max_tokens for c in chunks)


def test_short_chunks_dropped_but_kept_if_whole_document_is_short() -> None:
    cfg = ChunkingConfig(max_tokens=60, overlap_tokens=0, min_tokens=20)
    mixed = chunk_pages([page(1, "Mục lục."), long_page(2, 6)], cfg)
    assert all(c.token_count >= 20 for c in mixed)  # "Mục lục." bị bỏ
    tiny = chunk_pages([page(1, "Giá: 5 triệu.")], cfg)
    assert len(tiny) == 1  # tài liệu chỉ có chữ ít vẫn tìm được


def test_empty_and_blank_pages_produce_no_chunks() -> None:
    assert chunk_pages([page(1, ""), page(2, "  \n \n")], SMALL) == []


def test_soft_line_wraps_become_spaces_and_paragraphs_stay_separate_units() -> None:
    text = "Dòng một\nvẫn cùng câu.\n\nĐoạn hai bắt đầu ở đây."
    (chunk,) = chunk_pages([page(1, text)], ChunkingConfig(min_tokens=1))
    assert "\n" not in chunk.text and "Dòng một vẫn cùng câu." in chunk.text


def test_chunk_spanning_two_pages_records_both() -> None:
    cfg = ChunkingConfig(max_tokens=200, overlap_tokens=0, min_tokens=1, max_page_span=2)
    (chunk,) = chunk_pages([page(3, "Cuối trang ba."), page(4, "Đầu trang bốn.")], cfg)
    assert (chunk.page_start, chunk.page_end) == (3, 4)


def test_page_span_never_exceeds_two_even_when_text_is_short() -> None:
    cfg = ChunkingConfig(max_tokens=500, overlap_tokens=0, min_tokens=1, max_page_span=2)
    chunks = chunk_pages([page(i, f"Nội dung trang {i}.") for i in range(1, 6)], cfg)
    assert all(c.page_end - c.page_start <= 1 for c in chunks)
    assert [c.page_start for c in chunks] == [1, 3, 5]


def test_invalid_config_rejected() -> None:
    with pytest.raises(ValueError):
        ChunkingConfig(max_tokens=100, overlap_tokens=100)
    with pytest.raises(ValueError):
        ChunkingConfig(chars_per_token=0)


def test_estimate_tokens_is_at_least_one() -> None:
    assert estimate_tokens("") == 1 and estimate_tokens("a" * 40) == 10


# ---------- làm sạch ----------
def test_removes_page_numbers_and_normalizes_unicode() -> None:
    decomposed = unicodedata.normalize("NFD", "Điều khoản")  # dấu rời, chưa NFC
    assert decomposed != "Điều khoản"
    cleaned = clean_pages([page(1, f"{decomposed}   thanh   toán\n12\nTrang 3 / 10\nPage 4 of 9")])
    assert cleaned[0].text == "Điều khoản thanh toán"


def test_removes_repeated_header_and_footer_but_keeps_body() -> None:
    pages = [
        page(i, f"CÔNG TY ABC - BÁO CÁO\nNội dung riêng của trang {i}.\nTài liệu mật {i}")
        for i in range(1, 6)
    ]
    for c in clean_pages(pages):
        assert "CÔNG TY ABC" not in c.text and "Tài liệu mật" not in c.text
        assert c.text.startswith("Nội dung riêng của trang")


def test_header_removal_needs_enough_pages() -> None:
    pages = [page(1, "Tiêu đề\nA"), page(2, "Tiêu đề\nB")]
    assert "Tiêu đề" in clean_pages(pages)[0].text  # chỉ 2 trang: không đủ bằng chứng "lặp lại"


def test_body_lines_that_repeat_in_the_middle_are_kept() -> None:
    body = "\n".join(f"dòng {i} của nội dung" for i in range(6))
    pages = [page(i, f"{body}\nCâu trùng giữa trang\n{body}") for i in range(1, 5)]
    assert "Câu trùng giữa trang" in clean_pages(pages)[0].text


def test_cleaning_keeps_page_numbers_of_pages() -> None:
    cleaned = clean_pages([page(7, "a"), page(9, "b")])
    assert [p.number for p in cleaned] == [7, 9]


def test_default_chunks_never_cross_a_page_boundary_so_citations_name_the_right_page() -> None:
    pages = [
        page(1, "Giá trọn gói là 250 triệu."),
        page(2, "Thanh toán 30 ngày."),
        page(3, "Bảo hành 12 tháng."),
    ]
    chunks = chunk_pages(pages, ChunkingConfig(min_tokens=1))
    assert [(c.page_start, c.page_end) for c in chunks] == [(1, 1), (2, 2), (3, 3)]
    assert (
        "Bảo hành 12 tháng" in chunks[2].text and "Thanh toán" not in chunks[2].text
    )  # không mượn chữ trang trước


def test_page_made_only_of_repeated_lines_is_never_emptied() -> None:
    """Mẫu biểu 2 dòng giống nhau ở mọi trang: header/footer-removal không được làm mất toàn bộ nội dung."""
    pages = [
        page(i, f"MỤC {i}\nĐiều khoản số {i}: thanh toán trong vòng {10 + i} ngày.")
        for i in range(1, 8)
    ]
    cleaned = clean_pages(pages)
    assert all(c.text for c in cleaned)
    assert "thanh toán" in cleaned[0].text
