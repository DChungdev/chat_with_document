"""G7: đo hiệu năng cục bộ qua HTTP thật (devserver, không Docker).

Đo: thời gian tải→sẵn sàng (ingest) và thời gian tới token đầu / tổng thời gian trả lời khi N người dùng
hỏi đồng thời. LƯU Ý: dùng FakeLLM/FakeEmbedding ⇒ chỉ đo phần mềm của ta (API, SSE, retrieval trong bộ nhớ),
KHÔNG đại diện cho độ trễ nhà cung cấp LLM/embedding thật hay Postgres/pgvector. Số liệu thật phải đo trên staging
(deploy/perf/k6-chat.js). Dùng:  python scripts/perf_local.py --users 20 --questions 5
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

import httpx

from docchat_infra.pdf.synthetic import make_pdf

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    f"MỤC {i}\nĐiều khoản số {i}: thanh toán trong vòng {10 + i} ngày kể từ ngày nhận hóa đơn hợp lệ."
    for i in range(30)
]
QUESTIONS = [
    "Thanh toán trong vòng bao nhiêu ngày kể từ ngày nhận hóa đơn?",
    "Điều khoản số 7 quy định gì?",
]


def f(xs: list[float]) -> dict[str, object]:
    return {
        "n": len(xs),
        "p50": round(pct(xs, 50), 1),
        "p95": round(pct(xs, 95), 1),
        "max": round(max(xs, default=float("nan")), 1),
        "mean": round(statistics.fmean(xs), 1) if xs else None,
    }


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))] if xs else float("nan")


async def one_user(
    base: str,
    i: int,
    n_q: int,
    ingest_ms: list[float],
    first_ms: list[float],
    total_ms: list[float],
    errors: list[str],
) -> None:
    async with httpx.AsyncClient(base_url=base, timeout=60) as c:
        tok = (
            await c.post("/api/v1/dev/login", json={"name": f"perf{i}-{int(time.time())}"})
        ).json()["accessToken"]
        h = {"Authorization": f"Bearer {tok}"}
        v = (await c.get("/api/v1/data-notice", headers=h)).json()["version"]
        await c.post("/api/v1/data-notice/acceptances", json={"version": v}, headers=h)
        t0 = time.perf_counter()
        r = await c.post(
            "/api/v1/documents",
            files={"file": ("tai-lieu.pdf", make_pdf(PAGES), "application/pdf")},
            headers={**h, "Idempotency-Key": f"00000000-0000-4000-8000-{i:012d}"},
        )
        if r.status_code != 202:
            errors.append(f"upload {r.status_code}")
            return
        doc = r.json()["id"]
        while True:
            d = (await c.get(f"/api/v1/documents/{doc}", headers=h)).json()
            if d["status"] != "processing":
                break
            await asyncio.sleep(0.05)
        if d["status"] != "ready":
            errors.append(f"ingest {d['status']} {d.get('errorCode')}")
            return
        ingest_ms.append((time.perf_counter() - t0) * 1000)
        conv = (await c.post("/api/v1/conversations", headers=h)).json()["id"]
        for q in range(n_q):
            t1 = time.perf_counter()
            first = None
            async with c.stream(
                "POST",
                f"/api/v1/conversations/{conv}/messages",
                json={"question": QUESTIONS[q % 2]},
                headers=h,
            ) as s:
                if s.status_code != 200:
                    errors.append(f"ask {s.status_code}")
                    continue
                async for line in s.aiter_lines():
                    if first is None and line.startswith("event: token"):
                        first = (time.perf_counter() - t1) * 1000
            if first is None:
                errors.append("no token")
                continue
            first_ms.append(first)
            total_ms.append((time.perf_counter() - t1) * 1000)


async def run(base: str, users: int, n_q: int) -> dict[str, object]:
    ingest_ms: list[float] = []
    first_ms: list[float] = []
    total_ms: list[float] = []
    errors: list[str] = []
    t = time.perf_counter()
    await asyncio.gather(
        *(one_user(base, i, n_q, ingest_ms, first_ms, total_ms, errors) for i in range(users))
    )
    wall = time.perf_counter() - t
    return {
        "users": users,
        "questions_per_user": n_q,
        "pdf_pages": len(PAGES),
        "wall_s": round(wall, 2),
        "ingest_ms": f(ingest_ms),
        "first_token_ms": f(first_ms),
        "answer_total_ms": f(total_ms),
        "errors": errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=20)
    ap.add_argument("--questions", type=int, default=5)
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--fake-llm-delay", default="0.03")
    ap.add_argument("--base", help="đo máy chủ có sẵn thay vì tự khởi động devserver")
    ap.add_argument("--out", help="ghi JSON kết quả")
    a = ap.parse_args()
    proc = None
    base = a.base
    if not base:
        env = {**os.environ, "ENVIRONMENT": "dev", "FAKE_LLM_DELAY": a.fake_llm_delay}
        proc = subprocess.Popen(  # noqa: S603 - đối số cố định, không nhận từ bên ngoài
            [sys.executable, "-m", "docchat_api.devserver", "--port", str(a.port), "--no-static"],
            env=env,
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        base = f"http://127.0.0.1:{a.port}"
        for _ in range(100):
            try:
                if httpx.get(base + "/health", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.1)
    try:
        res = asyncio.run(run(base, a.users, a.questions))
    finally:
        if proc:
            proc.terminate()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if a.out:
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf8")
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
