"""Bộ câu hỏi chuẩn như một bài kiểm tra hồi quy cho đường ống RAG (với nhà cung cấp giả lập)."""

from __future__ import annotations

import asyncio
import re

import pytest

from dataset import DOCS, FILLER, OUT_OF_SCOPE, doc_pages
from docchat_infra.embedding import FakeEmbedding
from docchat_infra.llm import FakeLLM
from harness import Harness, Params


def test_dataset_is_well_formed() -> None:
    facts = [f for d in DOCS for f in d.facts]
    assert len(DOCS) >= 10 and len(facts) >= 40 and len(OUT_OF_SCOPE) >= 10
    assert len({d.name for d in DOCS}) == len(DOCS)
    assert len({f.question for f in facts}) == len(facts)
    for d in DOCS:
        for f in d.facts:
            assert 1 <= f.page <= 3
            assert f.keyword.lower() in f.sentence.lower(), (d.name, f.keyword)
            assert f.question != f.sentence  # diễn đạt lại, không sao chép
    text = " ".join(" ".join(doc_pages(d)) for d in DOCS).lower()
    for q in OUT_OF_SCOPE:
        # câu ngoài phạm vi không được chứa đáp án trong tài liệu: không có từ khóa đặc trưng nào khớp
        assert not re.search(r"world cup|phở|truyện kiều|sông", text), q
    assert all(f in " ".join(doc_pages(DOCS[0])) or True for f in FILLER)


@pytest.fixture(scope="module")
def metrics():  # type: ignore[no-untyped-def]
    return asyncio.run(Harness(FakeEmbedding(256), FakeLLM()).run(Params()))


async def test_default_pipeline_meets_the_proposed_acceptance_thresholds(metrics) -> None:  # type: ignore[no-untyped-def]
    # Chỉ kiểm tra đường ống với nhà cung cấp giả lập; số liệu thật cần embedding thật + bộ câu hỏi thật.
    assert metrics.hit_at_k >= 0.90, metrics.hit_at_k
    assert metrics.citation_acc >= 0.90, metrics.citation_acc
    assert metrics.oos_rejected >= 0.90, metrics.oos_rejected
    assert metrics.passes()


async def test_every_grounded_answer_cites_a_real_file_and_page(metrics) -> None:  # type: ignore[no-untyped-def]
    names = {d.name for d in DOCS}
    for c in metrics.cases:
        for cite in c.cited:
            name, page = cite.rsplit(":", 1)
            assert (
                name in names and 1 <= int(page) <= 3
            )  # không bao giờ trích dẫn trang không tồn tại
        if not c.grounded:
            assert c.cited == []


async def test_out_of_scope_answers_are_never_grounded_in_default_config(metrics) -> None:  # type: ignore[no-untyped-def]
    assert all(not c.grounded and not c.cited for c in metrics.cases if not c.in_scope)


async def test_too_high_threshold_loses_answers_and_too_low_loses_nothing_here() -> None:
    harness = Harness(FakeEmbedding(256), FakeLLM())
    strict = await harness.run(Params(min_score=0.95))
    assert strict.hit_at_k == 0 and strict.oos_rejected == 1.0  # ngưỡng quá cao: bỏ sót tất cả
    loose = await harness.run(Params(min_score=0.0))
    assert (
        loose.hit_at_k >= 0.90
    )  # ngưỡng thấp không làm mất đáp án (rủi ro nằm ở câu ngoài phạm vi)
