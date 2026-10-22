"""Làm sạch văn bản PDF và chia chunk giữ số trang (C3/C4, Database_Design_VectorDB 4.1).

Hàm thuần, không phụ thuộc hạ tầng: cùng đầu vào ⇒ cùng đầu ra.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

from docchat_core.ports.ingest import PageText


@dataclass(frozen=True)
class ChunkingConfig:
    max_tokens: int = 800
    overlap_tokens: int = 100
    # Chỉ bỏ mảnh vụn (nhãn trang lạc, dòng đơn lẻ). 20 như thiết kế ban đầu làm MẤT các trang chỉ có
    # một câu ngắn nhưng có thật (đánh giá D7: hit@k 98% → 72%), nên mặc định là 5.
    min_tokens: int = 5
    chars_per_token: float = 4.0  # xấp xỉ; thay bằng tokenizer thật khi chọn mô hình [TBD: OQ-012]
    # Số trang tối đa một chunk được trải qua (thiết kế cho phép ≤ 2, VectorDB 4.1). Mặc định 1: trích
    # dẫn chỉ ghi MỘT số trang (`page_start`), nên chunk vắt qua 2 trang làm trích dẫn sai trang khi đáp
    # án nằm ở nửa sau. Chunk trong một trang cho trích dẫn chính xác (US-301, KR2.2).
    max_page_span: int = 1

    def __post_init__(self) -> None:
        if not 0 <= self.overlap_tokens < self.max_tokens:
            raise ValueError("overlap_tokens phải nhỏ hơn max_tokens")
        if self.max_tokens < 1 or self.chars_per_token <= 0 or self.max_page_span < 1:
            raise ValueError("cấu hình chunking không hợp lệ")


@dataclass(frozen=True)
class ChunkDraft:
    ordinal: int
    page_start: int
    page_end: int
    text: str
    token_count: int


def estimate_tokens(text: str, chars_per_token: float = 4.0) -> int:
    return max(1, math.ceil(len(text) / chars_per_token))


# ---------- làm sạch ----------
_PAGE_NUMBER = re.compile(
    r"^(?:trang|page|tr\.?)?\s*\d{1,4}(?:\s*(?:/|of|trên)\s*\d{1,4})?$", re.IGNORECASE
)
_DIGITS = re.compile(r"\d+")
_EDGE_LINES = 2  # xét 2 dòng đầu và 2 dòng cuối mỗi trang để tìm header/footer
_REPEAT_RATIO = 0.6
_MIN_PAGES_FOR_REPEAT = 3
_MAX_HEADER_CHARS = 100


def _lines(text: str) -> list[str]:
    out = []
    for raw in unicodedata.normalize("NFC", text).replace("\r", "\n").split("\n"):
        out.append(re.sub(r"[ \t ]+", " ", raw).strip())
    return out


def _edge(indices: list[int]) -> list[int]:
    """Vị trí có thể là header/footer. Trang ngắn chỉ xét dòng đầu/cuối để không nuốt nội dung."""
    n = _EDGE_LINES if len(indices) >= 3 * _EDGE_LINES else 1
    return indices[:n] + indices[-n:]


def clean_pages(pages: list[PageText]) -> list[PageText]:
    """NFC, gộp khoảng trắng, bỏ số trang và header/footer lặp lại (dòng ngắn xuất hiện ở ≥ 60% trang)."""
    split = [_lines(p.text) for p in pages]
    repeated: set[str] = set()
    if len(pages) >= _MIN_PAGES_FOR_REPEAT:
        counts: Counter[str] = Counter()
        for lines in split:
            non_empty_idx = [i for i, ln in enumerate(lines) if ln]
            edge = [lines[i] for i in _edge(non_empty_idx)]
            counts.update({_DIGITS.sub("#", ln) for ln in edge if len(ln) <= _MAX_HEADER_CHARS})
        threshold = _REPEAT_RATIO * len(pages)
        repeated = {key for key, n in counts.items() if n >= threshold}

    result: list[PageText] = []
    for page, lines in zip(pages, split, strict=True):
        kept: list[str] = []
        dropped_repeat: list[str] = []
        non_empty_idx = [i for i, ln in enumerate(lines) if ln]
        edge_idx = set(_edge(non_empty_idx))
        for i, ln in enumerate(lines):
            if ln and _PAGE_NUMBER.match(ln):
                continue
            if ln and i in edge_idx and _DIGITS.sub("#", ln) in repeated:
                dropped_repeat.append(ln)
                continue
            kept.append(ln)
        if dropped_repeat and not any(kept):
            # Trang chỉ gồm các dòng "lặp" (vd. mẫu biểu giống nhau): giữ lại, không được xóa hết nội dung.
            kept = dropped_repeat
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()
        result.append(PageText(page.number, text))
    return result


# ---------- chia chunk ----------
@dataclass(frozen=True)
class _Piece:
    page: int
    text: str
    tokens: int


_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")


def _split_long(text: str, max_tokens: int, cpt: float) -> list[str]:
    """Đơn vị dài hơn một chunk (không có dấu câu): cắt theo từ."""
    max_chars = max(1, int(max_tokens * cpt))
    out: list[str] = []
    current: list[str] = []
    size = 0
    for word in text.split():
        if current and size + 1 + len(word) > max_chars:
            out.append(" ".join(current))
            current, size = [], 0
        while len(word) > max_chars:  # một "từ" dài bất thường (chuỗi liền)
            out.append(word[:max_chars])
            word = word[max_chars:]
        current.append(word)
        size += len(word) + (1 if size else 0)
    if current:
        out.append(" ".join(current))
    return out


def _pieces(pages: list[PageText], cfg: ChunkingConfig) -> list[_Piece]:
    pieces: list[_Piece] = []
    for page in pages:
        for paragraph in re.split(r"\n\s*\n", page.text):
            flat = re.sub(r"\s*\n\s*", " ", paragraph).strip()  # xuống dòng mềm → khoảng trắng
            if not flat:
                continue
            for sentence in _SENTENCE_END.split(flat):
                pieces_text = (
                    [sentence]
                    if estimate_tokens(sentence, cfg.chars_per_token) <= cfg.max_tokens
                    else _split_long(sentence, cfg.max_tokens, cfg.chars_per_token)
                )
                for t in pieces_text:
                    pieces.append(_Piece(page.number, t, estimate_tokens(t, cfg.chars_per_token)))
    return pieces


def chunk_pages(pages: list[PageText], cfg: ChunkingConfig | None = None) -> list[ChunkDraft]:
    cfg = cfg or ChunkingConfig()
    drafts: list[tuple[int, int, str, int]] = []  # (page_start, page_end, text, tokens)
    current: list[_Piece] = []
    total = 0
    has_new = False  # có phần tử mới ngoài phần chồng lấn kể từ lần phát gần nhất

    def span_ok(piece: _Piece) -> bool:
        return not current or piece.page - current[0].page < cfg.max_page_span

    def emit() -> None:
        text = " ".join(p.text for p in current)
        drafts.append(
            (
                min(p.page for p in current),
                max(p.page for p in current),
                text,
                estimate_tokens(text, cfg.chars_per_token),
            )
        )

    for piece in _pieces(pages, cfg):
        if current and (total + piece.tokens > cfg.max_tokens or not span_ok(piece)):
            if has_new:
                emit()
            # phần chồng lấn: các đơn vị cuối có tổng ≤ overlap_tokens
            tail: list[_Piece] = []
            acc = 0
            for p in reversed(current):
                if acc + p.tokens > cfg.overlap_tokens:
                    break
                tail.insert(0, p)
                acc += p.tokens
            current, total, has_new = tail, acc, False
            while current and (total + piece.tokens > cfg.max_tokens or not span_ok(piece)):
                total -= current.pop(0).tokens
        current.append(piece)
        total += piece.tokens
        has_new = True
    if current and has_new:
        emit()

    # Bỏ chunk quá ngắn (số trang, mục lục), trừ khi cả tài liệu chỉ có chunk ngắn.
    kept = [d for d in drafts if d[3] >= cfg.min_tokens] or drafts
    return [ChunkDraft(i, ps, pe, t, n) for i, (ps, pe, t, n) in enumerate(kept)]
