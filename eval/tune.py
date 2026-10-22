"""Hiệu chỉnh ngưỡng liên quan, k và chunking trên bộ câu hỏi chuẩn (D8).

    python eval/tune.py --out docs/implement/reports/retrieval_tuning.md
    python eval/tune.py --real          # với embedding/LLM thật (sau khi OQ-012/013 được chốt)

Quét lưới, chọn cấu hình tối đa hóa (hit@k + trích dẫn đúng + loại câu ngoài phạm vi)/3, hòa thì ưu
tiên ngưỡng CAO hơn (an toàn hơn trước bịa đặt, ADR-04). KHÔNG tự ghi vào `app_config`: giá trị chốt
cho production phải do người duyệt quyết định sau khi chạy với embedding thật và bộ câu hỏi thật.
"""

from __future__ import annotations

import argparse
import asyncio
import itertools
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from harness import Harness, Metrics, Params, summary_table  # noqa: E402
from run_eval import build_providers  # noqa: E402

MIN_SCORES = (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50)
TOP_KS = (4, 8)
CHUNKS = ((200, 0), (400, 50), (800, 100))


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    logging.getLogger("docchat_core").setLevel(logging.ERROR)

    harness = Harness(*build_providers(args.real))
    results: list[tuple[Params, Metrics]] = []
    for (tokens, overlap), k, ms in itertools.product(CHUNKS, TOP_KS, MIN_SCORES):
        p = Params(chunk_tokens=tokens, chunk_overlap=overlap, top_k=k, min_score=ms)
        results.append((p, await harness.run(p)))  # ingest lại chỉ khi chunking đổi

    # Hòa điểm → ngưỡng cao hơn, rồi k nhỏ hơn (ít ngữ cảnh hơn = rẻ hơn, ít nhiễu hơn).
    best_p, best_m = max(results, key=lambda r: (round(r[1].score, 4), r[0].min_score, -r[0].top_k))
    label = (
        lambda p: f"chunk {p.chunk_tokens}/{p.chunk_overlap}, k={p.top_k}, ngưỡng {p.min_score:.2f}"
    )  # noqa: E731
    top = sorted(results, key=lambda r: (-round(r[1].score, 4), -r[0].min_score))[:8]
    passing = [r for r in results if r[1].passes()]
    default_p = Params()
    default = next(m for p, m in results if p == default_p)

    lines = [
        "# Báo cáo hiệu chỉnh retrieval (D8)\n",
        f"Ngày chạy: {datetime.now(UTC):%Y-%m-%d}. Nhà cung cấp: "
        f"{'THẬT (từ môi trường)' if args.real else '**GIẢ LẬP** (embedding túi-từ băm + LLM trích xuất)'}. "
        f"{len(results)} cấu hình, 40 câu trong phạm vi + 12 ngoài phạm vi, 10 tài liệu × 3 trang.\n",
        "Ngưỡng nghiệm thu đề xuất (VectorDB mục 10, chờ PO chốt): hit@k ≥ 90%, trích dẫn đúng ≥ 90%, "
        "câu ngoài phạm vi bị loại ≥ 90%.\n",
        "## Cấu hình mặc định hiện tại\n",
        summary_table([(label(default_p), default)]),
        "\n## Cấu hình tốt nhất tìm được\n",
        summary_table([(label(best_p), best_m)]),
        "\n## 8 cấu hình đứng đầu\n",
        summary_table([(label(p), m) for p, m in top]),
        f"\n## Số cấu hình đạt cả ba ngưỡng: {len(passing)}/{len(results)}\n",
    ]
    if not args.real:
        lines.append(
            "\n> **Cảnh báo:** kết quả dùng embedding GIẢ LẬP nên chỉ kiểm chứng *phương pháp và đường ống*, "
            "**không** dùng để chọn giá trị cho production. Điểm cosine của mô hình thật nằm ở thang khác; "
            "phải chạy lại bằng `--real` với mô hình embedding đã duyệt và bộ câu hỏi thật [TBD: OQ-009, "
            "OQ-012/013] rồi mới ghi `retrieval_min_score`, `retrieval_top_k`, `chunk_*` vào `app_config`.\n"
        )
    report = "\n".join(lines)
    print(report)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
