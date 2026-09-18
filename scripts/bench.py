"""Sequential vs parallel fetch benchmark.

Run:
    python scripts/bench.py

Output (example):
    Sequential : 3 sources in 4.82s
    Parallel   : 3 sources in 1.43s
    Speedup    : 3.37×

Put these numbers into your README benchmark table.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

# Make sure the repo root is on sys.path when run as a script.
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from dotenv import load_dotenv

from ai import fetch_arxiv, fetch_web, fetch_wikipedia

load_dotenv()

QUERY = "transformer neural network attention mechanism"
MAX_RESULTS = 2


async def sequential(client: httpx.AsyncClient) -> tuple[int, float]:
    """Fetch all three sources one after another."""
    start = time.monotonic()
    total = 0
    for fetcher in [fetch_wikipedia, fetch_arxiv, fetch_web]:
        try:
            results = await fetcher(QUERY, max_results=MAX_RESULTS, client=client)  # type: ignore[call-arg]
        except Exception as exc:
            print(f"  ! sequential source failed: {exc}")
            continue
        total += len(results)
    elapsed = time.monotonic() - start
    return total, elapsed


async def parallel(client: httpx.AsyncClient) -> tuple[int, float]:
    """Fetch all three sources concurrently with asyncio.gather."""
    start = time.monotonic()
    results = await asyncio.gather(
        fetch_wikipedia(QUERY, max_results=MAX_RESULTS, client=client),
        fetch_arxiv(QUERY, max_results=MAX_RESULTS, client=client),
        fetch_web(QUERY, max_results=MAX_RESULTS, client=client),
        return_exceptions=True,
    )
    total = sum(len(r) for r in results if isinstance(r, list))
    elapsed = time.monotonic() - start
    return total, elapsed


async def main() -> None:
    print(f"Benchmark query: {QUERY!r}\n")

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        seq_count, seq_time = await sequential(client)
        par_count, par_time = await parallel(client)

    speedup = seq_time / par_time if par_time > 0 else float("inf")

    print(f"{'Sequential':<12}: {seq_count} sources in {seq_time:.2f}s")
    print(f"{'Parallel':<12}: {par_count} sources in {par_time:.2f}s")
    print(f"{'Speedup':<12}: {speedup:.2f}×")
    print()
    print("─── README benchmark table ───")
    print(f"| Mode       | Sources | Time   | Speedup |")
    print(f"|------------|---------|--------|---------|")
    print(f"| Sequential | {seq_count:<7} | {seq_time:.2f}s  | 1.00×   |")
    print(f"| Parallel   | {par_count:<7} | {par_time:.2f}s  | {speedup:.2f}×   |")


if __name__ == "__main__":
    asyncio.run(main())
