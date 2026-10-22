"""Benchmark pipeline ingest (task C7): đo từng giai đoạn trên PDF tổng hợp 10/50/200 trang.

    python scripts/bench_ingest.py --runs 3 --embed-latency-ms 150 --out docs/implement/reports/ingest_benchmark.md

Mặc định dùng embedding GIẢ với độ trễ giả lập mỗi lô (`--embed-latency-ms`) — kết quả cho thấy chi
phí của chính pipeline (trích xuất, chunk, ghi) cộng độ trễ mạng GIẢ ĐỊNH. Số liệu thật phải đo lại
trên staging với nhà cung cấp embedding đã chọn [TBD: OQ-012/013] (xem báo cáo).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import statistics
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from docchat_core.application.chunking import ChunkingConfig, chunk_pages, clean_pages
from docchat_core.application.ingest import IngestService
from docchat_core.config import AppConfig
from docchat_core.domain import Document
from docchat_infra.embedding import FakeEmbedding
from docchat_infra.memory import (
    InMemoryFileStorage,
    MemoryStore,
    MemoryUnitOfWorkFactory,
    MemoryWorkerUnitOfWorkFactory,
)
from docchat_infra.pdf import PypdfExtractor
from docchat_infra.pdf.synthetic import make_pdf

PARA = (
    "Điều khoản thanh toán quy định rằng bên mua phải thanh toán toàn bộ giá trị hợp đồng trong "
    "vòng 30 ngày kể từ ngày nhận hóa đơn hợp lệ. Mọi khoản chậm trả sẽ chịu lãi suất 0,05% mỗi "
    "ngày. Bên bán bảo hành thiết bị 12 tháng kể từ ngày bàn giao và nghiệm thu. "
)
TARGET_SECONDS = 60.0  # PRD 5.1


class SlowEmbedding(FakeEmbedding):
    def __init__(self, latency: float) -> None:
        super().__init__(1024)
        self.latency = latency

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        await asyncio.sleep(self.latency)  # độ trễ mạng giả định cho MỖI lô
        return await super().embed_documents(texts)


class Cfg:
    async def load_all(self) -> dict[str, object]:
        return {}


def make_document(pages: int, chars_per_page: int) -> bytes:
    body = (PARA * (chars_per_page // len(PARA) + 1))[:chars_per_page]
    return make_pdf([f"Trang {i}\n{body}" for i in range(1, pages + 1)])


async def one_run(pages: int, chars_per_page: int, latency: float) -> dict[str, float]:
    data = make_document(pages, chars_per_page)
    extractor, embedder = PypdfExtractor(), SlowEmbedding(latency)

    # --- từng giai đoạn, đo riêng ---
    t = time.perf_counter()
    extracted = extractor.extract(data, max_pages=10_000)
    t_extract = time.perf_counter() - t
    t = time.perf_counter()
    drafts = chunk_pages(clean_pages(extracted), ChunkingConfig())
    t_chunk = time.perf_counter() - t
    t = time.perf_counter()
    batches = [drafts[i : i + 64] for i in range(0, len(drafts), 64)]
    sem = asyncio.Semaphore(3)

    async def embed(batch: Sequence[object]) -> None:
        async with sem:
            await embedder.embed_documents([d.text for d in batch])

    await asyncio.gather(*(embed(b) for b in batches))
    t_embed = time.perf_counter() - t

    # --- tổng thể qua IngestService (đã gồm ghi chỉ mục trong bộ nhớ) ---
    store, storage = MemoryStore(), InMemoryFileStorage()
    user, doc_id = uuid4(), uuid4()
    key = f"{user}/{doc_id}.pdf"
    storage.objects[key] = data
    api = MemoryUnitOfWorkFactory(store)
    async with api.for_user(user) as uow:
        await uow.documents.add(
            Document(doc_id, user, "bench.pdf", len(data), key, datetime.now(UTC))
        )
        await uow.jobs.enqueue(doc_id, {})
    service = IngestService(
        MemoryWorkerUnitOfWorkFactory(store),
        storage,
        extractor,
        embedder,
        AppConfig(Cfg()),
        worker_id="bench",
    )
    t = time.perf_counter()
    await service.process_next()
    total = time.perf_counter() - t
    assert store.documents[doc_id].status.value == "ready", "ingest không thành công"
    return {
        "chunks": float(len(drafts)), "extract": t_extract, "chunk": t_chunk,
        "embed": t_embed, "total": total, "size_mb": len(data) / 1e6,
    }  # fmt: skip


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]


async def main() -> None:
    logging.getLogger("docchat_core").setLevel(logging.ERROR)  # bỏ cảnh báo "thiếu khóa app_config"
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="10,50,200")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--chars-per-page", type=int, default=2500)
    ap.add_argument("--embed-latency-ms", type=float, default=150.0)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    rows = []
    for pages in [int(s) for s in args.sizes.split(",")]:
        runs = [
            await one_run(pages, args.chars_per_page, args.embed_latency_ms / 1000)
            for _ in range(args.runs)
        ]
        med = lambda k, runs=runs: statistics.median(r[k] for r in runs)  # noqa: E731
        totals = [r["total"] for r in runs]
        rows.append(
            f"| {pages} | {runs[0]['size_mb']:.2f} | {int(runs[0]['chunks'])} | {med('extract'):.2f} | "
            f"{med('chunk'):.2f} | {med('embed'):.2f} | {med('total'):.2f} | {p95(totals):.2f} | "
            f"{'đạt' if p95(totals) <= TARGET_SECONDS else 'KHÔNG đạt'} |"
        )
    table = (
        "| Số trang | PDF (MB) | Chunk | Trích xuất (s) | Chunk hóa (s) | Embed (s) | Tổng p50 (s) | Tổng p95 (s) | ≤ 60s |\n"
        "|---|---|---|---|---|---|---|---|---|\n" + "\n".join(rows)
    )
    print(table)
    if args.out:
        out = Path(args.out)  # noqa: ASYNC240
        out.parent.mkdir(parents=True, exist_ok=True)  # noqa: ASYNC240
        out.write_text(  # noqa: ASYNC240
            f"# Báo cáo hiệu năng ingest (C7)\n\nNgày chạy: {datetime.now(UTC):%Y-%m-%d}. "
            f"{args.runs} lượt/kích cỡ, {args.chars_per_page} ký tự/trang, embedding giả lập với "
            f"độ trễ {args.embed_latency_ms:.0f} ms/lô (64 chunk/lô, 3 lô song song).\n\n{table}\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    asyncio.run(main())
