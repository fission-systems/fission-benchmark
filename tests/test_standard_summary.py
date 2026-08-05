"""Tests for standard-set summary and fail taxonomy."""
from __future__ import annotations

from pathlib import Path

from runner.run_validity import build_envelope
from runner.standard_summary import (
    SUMMARY_SCHEMA,
    annotate_rows_with_taxonomy,
    build_standard_summary,
    normalize_fail_taxonomy,
    parse_compiler_variant,
)


def test_normalize_fail_taxonomy_exclusive_buckets() -> None:
    assert normalize_fail_taxonomy({"error": "boom", "fail_category": ""}) == "adapter_error"
    assert (
        normalize_fail_taxonomy(
            {"error": None, "output_diagnostics": {"status": "whole_program_output"}}
        )
        == "whole_program_output"
    )
    assert (
        normalize_fail_taxonomy(
            {"error": None, "output_diagnostics": {"status": "boundary_mismatch"}}
        )
        == "boundary_mismatch"
    )
    assert normalize_fail_taxonomy({"error": None, "fail_category": "no_wrapper"}) == "no_wrapper"
    assert (
        normalize_fail_taxonomy({"error": None, "fail_category": "compile_error"}) == "compile_error"
    )
    assert (
        normalize_fail_taxonomy(
            {"error": None, "fail_category": "", "semantic_score": 1.0}
        )
        == "ok"
    )
    assert (
        normalize_fail_taxonomy(
            {"error": None, "fail_category": "assertion_fail", "semantic_score": 0.5}
        )
        == "assertion_fail"
    )


def test_build_standard_summary_denominators() -> None:
    rows = [
        {
            "decompiler": "fission",
            "function_name": "clamp",
            "compiler_variant": "gcc -O0",
            "error": None,
            "fail_category": "",
            "semantic_score": 1.0,
            "correctness_score": 1.0,
            "time_ms": 10,
            "output_diagnostics": {"status": "direct_function"},
        },
        {
            "decompiler": "fission",
            "function_name": "max",
            "compiler_variant": "gcc -O2",
            "error": None,
            "fail_category": "no_wrapper",
            "semantic_score": None,
            "correctness_score": None,
            "time_ms": 5,
            "output_diagnostics": {"status": "direct_function"},
        },
        {
            "decompiler": "fission",
            "function_name": "bad",
            "compiler_variant": "gcc -O0",
            "error": "boom",
            "fail_category": "adapter_error",
            "semantic_score": 0.0,
            "correctness_score": 0.0,
            "time_ms": 1,
            "output_diagnostics": {"status": "no_output"},
        },
        {
            "decompiler": "ghidra",
            "function_name": "clamp",
            "compiler_variant": "gcc -O0",
            "error": None,
            "fail_category": "assertion_fail",
            "semantic_score": 0.5,
            "correctness_score": 0.5,
            "time_ms": 20,
            "output_diagnostics": {"status": "direct_function"},
        },
    ]
    summary = build_standard_summary(rows)
    assert summary["schema"] == SUMMARY_SCHEMA
    fission = summary["mvp"]["by_decompiler"]["fission"]
    assert fission["coverage"]["attempted"] == 3
    assert fission["coverage"]["semantic_tested"] == 1  # only clamp
    assert fission["coverage"]["no_wrapper"] == 1
    assert fission["semantic"]["mean_pass_rate"] == 1.0
    assert fission["fail_taxonomy"]["ok"] == 1
    assert fission["fail_taxonomy"]["no_wrapper"] == 1
    assert fission["fail_taxonomy"]["adapter_error"] == 1
    # taxonomy buckets sum to attempted
    assert sum(fission["fail_taxonomy"].values()) == 3

    ghidra = summary["mvp"]["by_decompiler"]["ghidra"]
    assert ghidra["semantic"]["mean_pass_rate"] == 0.5
    assert ghidra["fail_taxonomy"]["assertion_fail"] == 1

    cross = summary["extensions"]["cross_variant"]["by_decompiler_variant"]["fission"]
    assert any(v["compiler_variant"] == "gcc -O0" and v["mean_pass_rate"] == 1.0 for v in cross)


def test_shared_denominator_counts_peer_measurable_missing_rows_as_misses() -> None:
    rows = [
        {
            "decompiler": "fission",
            "function_name": "clamp",
            "compiler_variant": "gcc -O0",
            "error": None,
            "semantic_score": 1.0,
            "type_match_score": 1.0,
            "ged_score": 0.0,
        },
        {
            "decompiler": "ghidra",
            "function_name": "clamp",
            "compiler_variant": "gcc -O0",
            "error": None,
            "semantic_score": 0.5,
            "type_match_score": 0.5,
            "ged_score": 1.0,
        },
        {
            "decompiler": "fission",
            "function_name": "sum_array",
            "compiler_variant": "gcc -O0",
            "error": "adapter failed",
            "semantic_score": None,
            "type_match_score": None,
            "ged_score": None,
        },
        {
            "decompiler": "ghidra",
            "function_name": "sum_array",
            "compiler_variant": "gcc -O0",
            "error": None,
            "semantic_score": 1.0,
            "type_match_score": 1.0,
            "ged_score": 0.0,
        },
    ]
    summary = build_standard_summary(rows)
    fission = summary["mvp"]["by_decompiler"]["fission"]
    ghidra = summary["mvp"]["by_decompiler"]["ghidra"]

    assert fission["semantic"]["observed_mean_pass_rate"] == 1.0
    assert fission["semantic"]["mean_pass_rate"] == 0.5
    assert fission["semantic"]["observed_rows"] == 1
    assert fission["semantic"]["shared_rows"] == 2
    assert ghidra["semantic"]["mean_pass_rate"] == 0.75

    assert fission["type_match"]["observed_rows"] == 1
    assert fission["type_match"]["shared_rows"] == 2
    assert fission["type_match"]["perfect_rate"] == 0.5
    assert fission["ged"]["observed_rows"] == 1
    assert fission["ged"]["shared_rows"] == 2
    assert fission["ged"]["perfect_rate"] == 0.5
    fission_variant = summary["extensions"]["cross_variant"][
        "by_decompiler_variant"
    ]["fission"][0]
    assert fission_variant["observed_rows"] == 1
    assert fission_variant["shared_rows"] == 2
    assert fission_variant["observed_mean_pass_rate"] == 1.0
    assert fission_variant["mean_pass_rate"] == 0.5
    assert summary["diagnostics"]["denominator_contract"].startswith(
        "shared-by-subject-v1"
    )


def test_parse_compiler_variant() -> None:
    assert parse_compiler_variant("gcc -O0") == ("gcc", "-O0")
    assert parse_compiler_variant("gcc-m32 -O2") == ("gcc-m32", "-O2")


def test_build_envelope_attaches_summary() -> None:
    row = {
        "decompiler": "fission",
        "function_name": "clamp",
        "compiler_variant": "gcc -O0",
        "source_similarity": 0.5,
        "semantic_score": 1.0,
        "correctness_score": 1.0,
        "correctness_rank": 1,
        "structural_penalty": 0.0,
        "time_ms": 10,
        "cases_passed": 5,
        "cases_total": 5,
        "error": None,
        "fail_category": "",
    }
    envelope = build_envelope(
        [row],
        run_meta={"official": False, "corpus": "dev"},
        matrix={
            "expected_decompilers": ["fission"],
            "expected_rows": 1,
            "observed_rows": 1,
            "expected_cells": [
                {
                    "decompiler": "fission",
                    "function_name": "clamp",
                    "compiler_variant": "gcc -O0",
                }
            ],
        },
    )
    assert envelope["summary"]["schema"] == SUMMARY_SCHEMA
    assert envelope["rows"][0]["fail_taxonomy"] == "ok"
    assert "fission" in envelope["summary"]["mvp"]["by_decompiler"]


def test_annotate_rows_with_taxonomy_does_not_mutate_input() -> None:
    row = {"error": None, "fail_category": "", "semantic_score": 1.0}
    out = annotate_rows_with_taxonomy([row])
    assert "fail_taxonomy" not in row
    assert out[0]["fail_taxonomy"] == "ok"


def test_cfg_absent_when_missing(tmp_path: Path) -> None:
    summary = build_standard_summary([], cfg_jsonl=tmp_path / "missing.jsonl")
    assert summary["secondary"]["cfg"]["status"] == "absent"
