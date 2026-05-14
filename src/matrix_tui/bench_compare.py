"""Compare two BenchResults JSON files.

Usage:
    python -m matrix_tui.bench_compare before.json after.json
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict


METRICS = [
    ("fps", "fps", "higher", ".1f"),
    ("cells_per_second", "cells/s", "higher", ",.0f"),
    ("bytes_per_second", "bytes/s", "lower", ",.0f"),
    ("write_calls_per_frame", "writes/frame", "lower", ",.1f"),
    ("write_calls_per_second", "writes/s", "lower", ",.0f"),
    ("avg_bytes_per_write", "avg write size", "higher", ",.1f"),
    ("cpu_time_s", "CPU s", "lower", ".2f"),
    ("rss_max_mb", "RSS MB", "lower", ".1f"),
]


def _fmt(v: float, spec: str) -> str:
    return format(v, spec)


def _pct(before: float, after: float) -> str:
    if before == 0:
        return "  n/a "
    delta = (after - before) / before * 100
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:6.1f}%"


def main(before_path: str, after_path: str) -> int:
    before: Dict[str, Any] = json.loads(Path(before_path).read_text())
    after: Dict[str, Any] = json.loads(Path(after_path).read_text())

    print()
    print(f"BEFORE: {before_path}  ({before['config'].get('label', '')})")
    print(f"AFTER:  {after_path}  ({after['config'].get('label', '')})")
    print()
    print(f"{'Metric':<20} {'Before':>16} {'After':>16} {'Δ':>10}  Direction")
    print("-" * 78)
    for key, label, want, spec in METRICS:
        b = before.get(key, 0.0) or 0.0
        a = after.get(key, 0.0) or 0.0
        better = (a > b) if want == "higher" else (a < b)
        marker = "✓" if better else "✗"
        print(
            f"{label:<20} {_fmt(b, spec):>16} {_fmt(a, spec):>16} "
            f"{_pct(b, a):>10}  {want:>6} {marker}"
        )
    print()
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m matrix_tui.bench_compare BEFORE.json AFTER.json")
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
