"""Chạy bộ câu hỏi chuẩn một lần (D7).

python eval/run_eval.py                       # embedding + LLM giả lập (kiểm tra đường ống)
python eval/run_eval.py --real                # dùng EMBEDDING_*/LLM_* từ môi trường (cần OQ-012/013)
python eval/run_eval.py --csv out.csv --show-failures
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from docchat_core.config import Settings  # noqa: E402
from docchat_infra.embedding import FakeEmbedding, build_embedding  # noqa: E402
from docchat_infra.llm import FakeLLM, build_llm  # noqa: E402
from harness import Harness, Params, summary_table  # noqa: E402


def build_providers(real: bool):  # type: ignore[no-untyped-def]
    if real:
        settings = Settings()
        return build_embedding(settings), build_llm(settings)
    return FakeEmbedding(256), FakeLLM()


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true", help="dùng nhà cung cấp thật từ biến môi trường")
    ap.add_argument("--chunk-tokens", type=int, default=Params.chunk_tokens)
    ap.add_argument("--overlap", type=int, default=Params.chunk_overlap)
    ap.add_argument("--top-k", type=int, default=Params.top_k)
    ap.add_argument("--min-score", type=float, default=Params.min_score)
    ap.add_argument("--csv", default="")
    ap.add_argument("--show-failures", action="store_true")
    args = ap.parse_args()
    logging.getLogger("docchat_core").setLevel(logging.ERROR)

    embedder, llm = build_providers(args.real)
    params = Params(
        chunk_tokens=args.chunk_tokens,
        chunk_overlap=args.overlap,
        top_k=args.top_k,
        min_score=args.min_score,
    )
    m = await Harness(embedder, llm).run(params)
    print(summary_table([("hiện tại", m)]))
    print(
        f"\nin-scope: {sum(c.in_scope for c in m.cases)}, out-of-scope: {sum(not c.in_scope for c in m.cases)}"
    )
    if args.show_failures:
        for c in m.cases:
            if (c.in_scope and not (c.hit and c.citation_ok)) or (not c.in_scope and c.grounded):
                print(
                    f"- {c.question}\n    mong đợi {c.expected}; truy xuất {c.retrieved[:3]}; trích dẫn {c.cited}"
                )
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "question",
                    "in_scope",
                    "expected",
                    "hit",
                    "grounded",
                    "citation_ok",
                    "keyword_ok",
                    "cited",
                    "answer",
                ]
            )
            for c in m.cases:
                w.writerow(
                    [
                        c.question,
                        c.in_scope,
                        c.expected,
                        c.hit,
                        c.grounded,
                        c.citation_ok,
                        c.keyword_ok,
                        ";".join(c.cited),
                        c.answer,
                    ]
                )


if __name__ == "__main__":
    asyncio.run(main())
