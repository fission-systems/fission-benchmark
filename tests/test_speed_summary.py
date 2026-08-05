"""Unit tests for speed diagnostics (row aggregate + microbench merge)."""
from __future__ import annotations

from runner.speed_summary import (
    SPEED_SCHEMA,
    aggregate_row_times,
    build_speed_extension,
    timing_stats,
)


def test_timing_stats_empty():
    s = timing_stats([])
    assert s["n"] == 0
    assert s["mean_ms"] is None


def test_timing_stats_basic():
    s = timing_stats([10, 20, 30, 40, 100])
    assert s["n"] == 5
    assert s["min_ms"] == 10
    assert s["max_ms"] == 100
    assert s["p50_ms"] is not None
    assert s["mean_ms"] == 40.0


def test_aggregate_row_times_and_pairs():
    rows = [
        {
            "decompiler": "fission",
            "function_name": "add_ints",
            "compiler_variant": "gcc -O0",
            "time_ms": 12,
        },
        {
            "decompiler": "ghidra",
            "function_name": "add_ints",
            "compiler_variant": "gcc -O0",
            "time_ms": 48,
        },
        {
            "decompiler": "fission",
            "function_name": "clamp",
            "compiler_variant": "gcc -O0",
            "time_ms": 20,
            "error": "fail",
            "fail_category": "adapter_error",
        },
    ]
    agg = aggregate_row_times(rows)
    assert "fission" in agg["by_decompiler"]
    assert agg["by_decompiler"]["fission"]["n"] == 1  # error row excluded
    pair = agg["fission_vs_ghidra"]
    assert pair["paired_n"] == 1
    assert pair["pairs_head"][0]["speedup"] == 4.0


def test_build_speed_extension_with_microbench():
    rows = [
        {
            "decompiler": "fission",
            "function_name": "f",
            "compiler_variant": "gcc -O0",
            "time_ms": 15,
        }
    ]
    micro = {
        "schema": "speed-microbench-v2",
        "by_decompiler": {
            "fission": {
                "cold": {"n": 1, "mean_ms": 40.0},
                "warm": {"n": 4, "mean_ms": 12.0},
                "resources": {
                    "all": {
                        "n_trials": 5,
                        "mean_cpu_percent": 75.0,
                        "peak_memory_bytes": 536870912,
                    }
                },
            }
        },
        "subjects": [],
    }
    ext = build_speed_extension(rows, microbench=micro)
    assert ext["schema"] == SPEED_SCHEMA
    assert ext["ranking"] is False
    assert ext["from_rows"]["by_decompiler"]["fission"]["n"] == 1
    assert ext["microbench"]["by_decompiler"]["fission"]["cold"]["mean_ms"] == 40.0
    assert (
        ext["microbench"]["by_decompiler"]["fission"]["resources"]["all"]
        ["peak_memory_bytes"]
        == 536870912
    )


def test_attach_summary_includes_speed_extension():
    from runner.standard_summary import attach_summary_to_envelope

    env = {
        "schema_version": 2,
        "run": {"corpus": "dev", "official": False},
        "rows": [
            {
                "decompiler": "fission",
                "function_name": "f",
                "compiler_variant": "gcc -O0",
                "time_ms": 11,
                "source_similarity": 0.0,
                "semantic_score": 1.0,
                "correctness_score": 1.0,
                "correctness_rank": 1,
                "structural_penalty": 0.0,
                "cases_passed": 1,
                "cases_total": 1,
            }
        ],
    }
    out = attach_summary_to_envelope(env, microbench=None)
    speed = (out.get("summary") or {}).get("extensions", {}).get("speed")
    assert speed is not None
    assert speed["schema"] == SPEED_SCHEMA
    assert "from_rows" in speed
