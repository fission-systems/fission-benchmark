"""Speed diagnostics for envelope summary.extensions.speed (non-ranking).

Two sources:
  1. Row ``time_ms`` from a normal benchmark envelope (amortized batch decompile).
  2. Optional dedicated micro-bench JSON (cold/warm trials on fixed subjects).

Never feeds semantic ranking.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence


SPEED_SCHEMA = "speed-diagnostics-v1"


def _percentile(sorted_vals: Sequence[float], p: float) -> float | None:
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    idx = (len(sorted_vals) - 1) * p
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    w = idx - lo
    return float(sorted_vals[lo] * (1.0 - w) + sorted_vals[hi] * w)


def timing_stats(times: Iterable[float]) -> dict[str, Any]:
    clean = sorted(float(t) for t in times if isinstance(t, (int, float)) and t > 0)
    if not clean:
        return {
            "n": 0,
            "mean_ms": None,
            "p50_ms": None,
            "p95_ms": None,
            "min_ms": None,
            "max_ms": None,
            "sum_ms": 0.0,
        }
    s = sum(clean)
    return {
        "n": len(clean),
        "mean_ms": round(s / len(clean), 3),
        "p50_ms": round(_percentile(clean, 0.5) or 0.0, 3),
        "p95_ms": round(_percentile(clean, 0.95) or 0.0, 3),
        "min_ms": round(clean[0], 3),
        "max_ms": round(clean[-1], 3),
        "sum_ms": round(s, 3),
    }


def _is_timed_row(row: Mapping[str, Any]) -> bool:
    t = row.get("time_ms")
    if not isinstance(t, (int, float)) or t <= 0:
        return False
    if row.get("error"):
        return False
    if row.get("fail_category") == "adapter_error":
        return False
    return True


def aggregate_row_times(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate envelope row time_ms by decompiler (+ fission vs ghidra pairs)."""
    by_dec: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if not _is_timed_row(row):
            continue
        d = str(row.get("decompiler") or "")
        if d:
            by_dec[d].append(float(row["time_ms"]))

    by_decompiler = {
        name: timing_stats(vals)
        for name, vals in sorted(by_dec.items(), key=lambda kv: (kv[0] != "fission", kv[0]))
    }

    # Paired cells
    cells: dict[tuple[str, str], dict[str, float]] = {}
    for row in rows:
        if not _is_timed_row(row):
            continue
        d = row.get("decompiler")
        if d not in ("fission", "ghidra"):
            continue
        key = (str(row.get("function_name") or ""), str(row.get("compiler_variant") or ""))
        if not key[0]:
            continue
        cells.setdefault(key, {})[str(d)] = float(row["time_ms"])

    pairs: list[dict[str, Any]] = []
    speedups: list[float] = []
    for (fn, var), c in cells.items():
        if "fission" not in c or "ghidra" not in c:
            continue
        f_ms, g_ms = c["fission"], c["ghidra"]
        speedup = (g_ms / f_ms) if f_ms > 0 else None
        if speedup is not None and speedup > 0:
            speedups.append(speedup)
        pairs.append(
            {
                "function_name": fn,
                "compiler_variant": var,
                "fission_ms": round(f_ms, 3),
                "ghidra_ms": round(g_ms, 3),
                "speedup": round(speedup, 4) if speedup is not None else None,
            }
        )
    pairs.sort(key=lambda p: -float(p["fission_ms"]))
    speedups_sorted = sorted(speedups)
    faster = sum(1 for p in pairs if p["fission_ms"] < p["ghidra_ms"])
    geo = None
    if speedups_sorted:
        import math

        geo = math.exp(sum(math.log(s) for s in speedups_sorted) / len(speedups_sorted))

    return {
        "source": "envelope_rows",
        "metric": "adapter_decompile_time_ms",
        "by_decompiler": by_decompiler,
        "fission_vs_ghidra": {
            "paired_n": len(pairs),
            "median_speedup": round(_percentile(speedups_sorted, 0.5) or 0.0, 4)
            if speedups_sorted
            else None,
            "geometric_mean_speedup": round(geo, 4) if geo is not None else None,
            "fission_faster_share": round(faster / len(pairs), 4) if pairs else None,
            "pairs_head": pairs[:40],
        },
    }


def normalize_microbench(raw: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Validate/normalize a micro-bench JSON document for extensions.speed.microbench."""
    if not raw or not isinstance(raw, dict):
        return None
    if raw.get("schema") not in (
        SPEED_SCHEMA,
        "speed-microbench-v1",
        "speed-microbench-v2",
        None,
    ):
        # Accept documents that look like microbench even if schema key varies.
        if "subjects" not in raw and "trials" not in raw and "by_decompiler" not in raw:
            return None
    return {
        "schema": str(raw.get("schema") or "speed-microbench-v2"),
        "run_id": raw.get("run_id"),
        "started_at": raw.get("started_at"),
        "finished_at": raw.get("finished_at"),
        "config": raw.get("config") or {},
        "by_decompiler": raw.get("by_decompiler") or {},
        "subjects": raw.get("subjects") or [],
        "notes": raw.get("notes")
        or (
            "cold = first timed request after subject load; "
            "warm = subsequent requests on the same binary (no container restart)."
        ),
    }


def build_speed_extension(
    rows: Sequence[Mapping[str, Any]],
    *,
    microbench: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build summary.extensions.speed block."""
    row_agg = aggregate_row_times(rows)
    micro = normalize_microbench(microbench)
    return {
        "schema": SPEED_SCHEMA,
        "ranking": False,
        "note": (
            "Decompile latency diagnostics only. Not a semantic ranking axis. "
            "Row times are adapter wall-clock; microbench adds cold/warm trials."
        ),
        "from_rows": row_agg,
        "microbench": micro,
    }
