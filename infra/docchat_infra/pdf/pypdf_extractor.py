"""Trích xuất văn bản theo trang bằng pypdf (C3). Không OCR trong MVP (ADR-09, OQ-008).

PDF quét (không có lớp văn bản) ⇒ `NO_TEXT`; có mật khẩu ⇒ `PDF_PASSWORD`; hỏng ⇒ `PDF_CORRUPT`.
Mã lỗi khớp API_Design 3.4.1. Không bao giờ log hay đưa nội dung PDF vào thông điệp ngoại lệ.
"""

from __future__ import annotations

import io
import logging
import time
from collections.abc import Callable

from pypdf import PdfReader

from docchat_core.ports.ingest import (
    NO_TEXT,
    PDF_CORRUPT,
    PDF_PASSWORD,
    PDF_TOO_MANY_PAGES,
    ExtractionError,
    PageText,
)

logger = logging.getLogger(__name__)

PDF_TOO_COMPLEX = "PDF_TOO_COMPLEX"


class PypdfExtractor:
    def __init__(
        self,
        *,
        max_seconds: float = 120.0,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_seconds = max_seconds  # chặn PDF "bom" làm worker treo
        self._mono = monotonic

    def extract(self, data: bytes, *, max_pages: int) -> list[PageText]:
        started = self._mono()
        try:
            reader = PdfReader(io.BytesIO(data), strict=False)
            if reader.is_encrypted and not reader.decrypt(""):
                # Nhiều PDF chỉ đặt mật khẩu chủ (hạn chế in/sao chép) — mật khẩu rỗng mở được.
                raise ExtractionError(PDF_PASSWORD)
            total = len(reader.pages)
        except ExtractionError:
            raise
        except Exception:
            raise ExtractionError(PDF_CORRUPT) from None
        if total == 0:
            raise ExtractionError(PDF_CORRUPT)
        if total > max_pages:
            raise ExtractionError(PDF_TOO_MANY_PAGES)

        pages: list[PageText] = []
        failed = 0
        for index in range(total):
            if self._mono() - started > self._max_seconds:
                raise ExtractionError(PDF_TOO_COMPLEX)
            try:
                text = reader.pages[index].extract_text() or ""
            except Exception:
                text, failed = "", failed + 1  # một trang hỏng không làm hỏng cả tài liệu
            pages.append(PageText(index + 1, text))
        if failed:
            logger.warning(
                "some pages could not be extracted",
                extra={"event": "pdf_page_failed", "count": failed},
            )
        if not any(p.text.strip() for p in pages):
            raise ExtractionError(NO_TEXT)  # PDF quét: chỉ có ảnh
        return pages
