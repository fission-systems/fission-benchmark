"""Standard decompiler benchmark summary (MVP + extension pivots).

Canonical public contract for the metric set:

  MVP-0 same-function matrix (request contract: binary+addr; core vs multi)
  MVP-1 semantic pass rate (correctness ranking axis)
  MVP-2 coverage (attempted / adapter_clean / invalid_boundary / tested / no_wrapper)
  MVP-3 fail taxonomy (stable exclusive buckets)
  MVP-4 cfg match (optional secondary; attached when JSONL present)
  MVP-5 runtime
  EXT-7 cross-variant pivot (compiler × opt)

Source similarity, AST, and readability proxies are intentionally excluded from
ranking surfaces — they may still appear under diagnostics elsewhere.

Extension pivots (bare-compile, readability axis, track/ISA) are attached under
``extensions`` / ``diagnostics`` and must never feed correctness ranking.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from .same_function_matrix import build_same_function_matrix
except ImportError:
    from same_function_matrix import build_same_function_matrix

try:
    from .bare_compile import (
        aggregate_bare_compile,
        aggregate_readability_axis,
        aggregate_track_taxonomy,
    )
except ImportError:
    from bare_compile import (
        aggregate_bare_compile,
        aggregate_readability_axis,
        aggregate_track_taxonomy,
    )

try:
    from .speed_summary import build_speed_extension
except ImportError:
    from speed_summary import build_speed_extension

try:
    from .recompilation import aggregate_recompilation
except ImportError:
    from recompilation import aggregate_recompilation

SUMMARY_SCHEMA = "standard-set-v1"
MEASUREMENT_HEALTH_SCHEMA = "measurement-health-v1"

# Exclusive fail taxonomy buckets (each row maps to exactly one).
TAXONOMY_BUCKETS = (
    "adapter_error",
    "boundary_mismatch",
    "whole_program_output",
    "compile_error",
    "runtime_error",
    "timeout",
    "assertion_fail",
    "fixture_error",
    "oracle_error",
    "no_wrapper",
    "ok",
    "other",
)

_BOUNDARY_STATUSES = frozenset({"boundary_mismatch", "whole_program_output", "no_output"})

_VARIANT_RE = re.compile(
    r"^(?P<compiler>[^\s]+(?:-m32)?)\s+(?P<opt>-O\d+|-Os|-Ofast|-Og)?",
    re.IGNORECASE,
)


def normalize_fail_taxonomy(row: Mapping[str, Any]) -> str:
    """Map a result row to exactly one canonical fail-taxonomy bucket."""
    diagnostics = row.get("output_diagnostics") or {}
    status = str(diagnostics.get("status") or "")
    fail_cat = str(row.get("fail_category") or "")
    error = row.get("error")

    if status == "whole_program_output" or fail_cat == "whole_program_output":
        return "whole_program_output"
    if status == "boundary_mismatch" or fail_cat == "boundary_mismatch":
        return "boundary_mismatch"
    if status == "no_output":
        return "adapter_error"
    if error or fail_cat == "adapter_error":
        return "adapter_error"
    if fail_cat == "no_wrapper":
        return "no_wrapper"
    if fail_cat == "compile_error":
        return "compile_error"
    if fail_cat == "runtime_error":
        return "runtime_error"
    if fail_cat == "timeout":
        return "timeout"
    if fail_cat == "assertion_fail":
        return "assertion_fail"
    if fail_cat == "fixture_error":
        return "fixture_error"
    if fail_cat == "oracle_error":
        return "oracle_error"
    if fail_cat and fail_cat not in {"", "ok"}:
        return "other"

    semantic = row.get("semantic_score")
    if semantic is None:
        # Clean output but untested — treat as no_wrapper-ish only if not already
        # classified; otherwise ok with unmeasured semantic.
        return "ok" if not error else "adapter_error"
    if float(semantic) >= 1.0:
        return "ok"
    # Finite semantic < 1 without a more specific category.
    return "assertion_fail" if fail_cat in {"", "assertion_fail"} else "other"


def annotate_rows_with_taxonomy(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return shallow-copied rows with ``fail_taxonomy`` set."""
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["fail_taxonomy"] = normalize_fail_taxonomy(item)
        out.append(item)
    return out


def parse_compiler_variant(variant: str) -> tuple[str, str]:
    """Split ``gcc -O0`` / ``gcc-m32 -O2`` into (compiler, opt)."""
    text = (variant or "").strip()
    match = _VARIANT_RE.match(text)
    if not match:
        parts = text.split(None, 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return text or "unknown", ""
    compiler = match.group("compiler") or "unknown"
    opt = match.group("opt") or ""
    return compiler, opt


def _empty_taxonomy() -> dict[str, int]:
    return {bucket: 0 for bucket in TAXONOMY_BUCKETS}


def _oracle_subject_for_rows(rows: list[Mapping[str, Any]]) -> str | None:
    subjects: set[str] = set()
    for row in rows:
        evidence = row.get("oracle_evidence") or {}
        subject = evidence.get("oracle_subject")
        if isinstance(subject, str) and subject:
            subjects.add(subject)
    if not subjects:
        return None
    if len(subjects) == 1:
        return next(iter(subjects))
    return ",".join(sorted(subjects))


def _subject_cell(row: Mapping[str, Any]) -> tuple[str, str, str]:
    """Return the tool-independent identity used by shared denominators."""
    return (
        str(row.get("corpus") or ""),
        str(row.get("function_name") or ""),
        str(row.get("compiler_variant") or ""),
    )


def _valid_semantic_score(row: Mapping[str, Any]) -> float | None:
    bucket = row.get("fail_taxonomy") or normalize_fail_taxonomy(row)
    if row.get("error") or bucket in {"adapter_error", "no_wrapper"}:
        return None
    if row.get("fail_category") == "no_wrapper":
        return None
    score = row.get("semantic_score")
    return float(score) if score is not None else None


def _percentile(values: list[float], quantile: float) -> float | None:
    """Return a deterministic nearest-rank percentile for dashboard costs."""
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * quantile + 0.5)))
    return round(ordered[index], 2)


def _clean_output(row: Mapping[str, Any]) -> bool:
    """Whether a row produced the requested function as usable decompiled text."""
    bucket = str(row.get("fail_taxonomy") or normalize_fail_taxonomy(row))
    status = str((row.get("output_diagnostics") or {}).get("status") or "")
    code = str(row.get("decompiled_code") or "").strip()
    return bool(code) and not row.get("error") and bucket not in {
        "adapter_error",
        "boundary_mismatch",
        "whole_program_output",
    } and status not in _BOUNDARY_STATUSES


def _preset_memberships(row: Mapping[str, Any]) -> set[str]:
    """Return stable, non-overlapping dashboard filters plus the all preset."""
    memberships = {"all"}
    _, opt = parse_compiler_variant(str(row.get("compiler_variant") or ""))
    memberships.add("unoptimized" if opt in {"", "-O0", "-Og"} else "optimized")

    language = str(row.get("language") or "").strip().lower()
    if language:
        memberships.add(f"language:{language}")
    isa_format = row.get("isa_format") or {}
    if isinstance(isa_format, Mapping):
        arch = str(isa_format.get("arch") or "").strip().lower()
        fmt = str(isa_format.get("format") or isa_format.get("fmt") or "").strip().lower()
        if arch:
            memberships.add(f"arch:{arch}")
        if fmt:
            memberships.add(f"format:{fmt}")
    track = str(row.get("track") or "").strip().lower()
    if track:
        memberships.add(f"track:{track}")
    return memberships


def _difficulty_by_cell(rows: list[Mapping[str, Any]]) -> dict[tuple[str, str, str], str]:
    """Classify a structural difficulty proxy from cross-tool exact GED agreement."""
    exact: dict[tuple[str, str, str], list[bool]] = defaultdict(list)
    cells = {_subject_cell(row) for row in rows}
    for row in rows:
        if row.get("ged_score") is not None:
            exact[_subject_cell(row)].append(float(row["ged_score"]) == 0.0)
    out: dict[tuple[str, str, str], str] = {}
    for cell in cells:
        measured = exact.get(cell, [])
        if not measured:
            out[cell] = "unmeasured"
            continue
        rate = sum(measured) / len(measured)
        out[cell] = "easy" if rate >= 2 / 3 else "hard" if rate <= 1 / 3 else "medium"
    return out


def _metric_summary(
    tool_rows: list[Mapping[str, Any]],
    all_rows: list[Mapping[str, Any]],
    field: str,
    *,
    exact: float,
    lower_is_better: bool = False,
) -> dict[str, Any]:
    def metric_value(row: Mapping[str, Any]) -> float | None:
        if field == "semantic_score":
            return _valid_semantic_score(row)
        value = row.get(field)
        return float(value) if value is not None else None

    cells = {_subject_cell(row) for row in all_rows if metric_value(row) is not None}
    observed = {
        _subject_cell(row): value
        for row in tool_rows
        if (value := metric_value(row)) is not None
    }
    values = list(observed.values())
    perfect = sum(value == exact for value in values)
    output = {
        "shared_rows": len(cells),
        "observed_rows": len(values),
        "perfect_rows": perfect,
        "perfect_rate": round(perfect / len(cells), 4) if cells else None,
    }
    if lower_is_better:
        output["observed_mean"] = round(sum(values) / len(values), 4) if values else None
    else:
        shared_values = [observed.get(cell, 0.0) for cell in cells]
        output["shared_mean"] = (
            round(sum(shared_values) / len(shared_values), 4) if shared_values else None
        )
        output["observed_mean"] = round(sum(values) / len(values), 4) if values else None
    return output


def _view_measurement_health(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    tools = sorted({str(row.get("decompiler") or "unknown") for row in rows})
    cells = {_subject_cell(row) for row in rows}
    difficulty = _difficulty_by_cell(rows)
    difficulty_counts = {name: 0 for name in ("easy", "medium", "hard", "unmeasured")}
    for bucket in difficulty.values():
        difficulty_counts[bucket] += 1

    source_available: dict[tuple[str, str, str], bool] = {}
    source_basis: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for row in rows:
        cell = _subject_cell(row)
        ged = row.get("ged_metadata") or {}
        available = ged.get("source_cfg_available")
        if available is None:
            available = row.get("ged_score") is not None or ged.get("source_nodes") is not None
        source_available[cell] = source_available.get(cell, False) or bool(available)
        basis = str(ged.get("source_basis") or "missing")
        source_basis[basis].add(cell)

    by_tool: dict[str, Any] = {}
    output_cfg: dict[str, Any] = {}
    for tool in tools:
        tool_rows = [row for row in rows if str(row.get("decompiler") or "unknown") == tool]
        clean = sum(_clean_output(row) for row in tool_rows)
        taxonomy = _empty_taxonomy()
        times: list[float] = []
        cfg_available = 0
        recomp_measured = 0
        compilable = 0
        byte_match = 0
        by_difficulty: dict[str, dict[str, int]] = {
            name: {"rows": 0, "semantic_perfect": 0, "compilable": 0}
            for name in difficulty_counts
        }
        for row in tool_rows:
            bucket = str(row.get("fail_taxonomy") or normalize_fail_taxonomy(row))
            taxonomy[bucket if bucket in taxonomy else "other"] += 1
            time_ms = row.get("time_ms")
            if isinstance(time_ms, (int, float)) and time_ms > 0:
                times.append(float(time_ms))
            ged = row.get("ged_metadata") or {}
            decompiled_available = ged.get("decompiled_cfg_available")
            if decompiled_available is None:
                decompiled_available = (
                    row.get("ged_score") is not None or ged.get("decompiled_nodes") is not None
                )
            cfg_available += bool(decompiled_available)
            recomp = row.get("recompilation") or {}
            if row.get("recompilation_score") is not None:
                recomp_measured += 1
                byte_match += float(row["recompilation_score"]) >= 1.0
            compilable += recomp.get("compilable") is True
            diff = difficulty[_subject_cell(row)]
            by_difficulty[diff]["rows"] += 1
            by_difficulty[diff]["semantic_perfect"] += (
                _valid_semantic_score(row) == 1.0
            )
            by_difficulty[diff]["compilable"] += recomp.get("compilable") is True

        output_cfg[tool] = {
            "attempted": len(tool_rows),
            "available": cfg_available,
            "rate": round(cfg_available / len(tool_rows), 4) if tool_rows else None,
        }
        by_tool[tool] = {
            "attempted": len(tool_rows),
            "output_clean": clean,
            "output_clean_rate": round(clean / len(tool_rows), 4) if tool_rows else None,
            "semantic": _metric_summary(
                tool_rows, rows, "semantic_score", exact=1.0
            ),
            "ged": _metric_summary(
                tool_rows, rows, "ged_score", exact=0.0, lower_is_better=True
            ),
            "type_match": _metric_summary(
                tool_rows, rows, "type_match_score", exact=1.0
            ),
            "compile": {
                "measured_rows": recomp_measured,
                "compilable_rows": compilable,
                "compilable_rate": (
                    round(compilable / recomp_measured, 4) if recomp_measured else None
                ),
                "byte_match_rows": byte_match,
                "byte_match_rate": (
                    round(byte_match / recomp_measured, 4) if recomp_measured else None
                ),
            },
            "failures": taxonomy,
            "cost": {
                "basis": "per-function wall time",
                "rows_with_time": len(times),
                "total_ms": round(sum(times), 2),
                "mean_ms": round(sum(times) / len(times), 2) if times else None,
                "p50_ms": _percentile(times, 0.5),
                "p95_ms": _percentile(times, 0.95),
                "usd": None,
            },
            "by_difficulty": by_difficulty,
        }

    source_count = sum(source_available.values())
    return {
        "scope": {
            "rows": len(rows),
            "subjects": len(cells),
            "decompilers": len(tools),
            "difficulty": difficulty_counts,
        },
        "by_decompiler": by_tool,
        "pipeline": {
            "source_cfg": {
                "subjects": len(cells),
                "available": source_count,
                "rate": round(source_count / len(cells), 4) if cells else None,
                "by_basis": {
                    basis: len(basis_cells)
                    for basis, basis_cells in sorted(source_basis.items())
                },
            },
            "decompiled_cfg": output_cfg,
            "oracle": {
                "attempted": len(rows),
                "tested": sum(_valid_semantic_score(row) is not None for row in rows),
                "no_wrapper": sum(
                    (row.get("fail_taxonomy") or normalize_fail_taxonomy(row))
                    == "no_wrapper"
                    for row in rows
                ),
            },
        },
    }


def build_measurement_health(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Build DecBench-inspired scope, normalization, failure, and cost pivots."""
    preset_rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        for preset in _preset_memberships(row):
            preset_rows[preset].append(row)

    presets: list[dict[str, Any]] = []
    for preset_id, selected in sorted(
        preset_rows.items(), key=lambda item: (item[0] != "all", item[0])
    ):
        tools = {str(row.get("decompiler") or "unknown") for row in selected}
        clean_by_cell: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        for row in selected:
            if _clean_output(row):
                clean_by_cell[_subject_cell(row)].add(
                    str(row.get("decompiler") or "unknown")
                )
        intersection_cells = {
            cell for cell, clean_tools in clean_by_cell.items() if clean_tools == tools
        }
        intersection = [
            row for row in selected if _subject_cell(row) in intersection_cells
        ]
        presets.append(
            {
                "id": preset_id,
                "label": preset_id.replace(":", " · ").replace("-", " ").title(),
                "views": {
                    "shared": _view_measurement_health(selected),
                    "intersection": _view_measurement_health(intersection),
                },
            }
        )
    return {
        "schema": MEASUREMENT_HEALTH_SCHEMA,
        "ranking": False,
        "default_preset": "all",
        "default_normalization": "shared",
        "normalization_contract": {
            "shared": (
                "Any-tool measurable subjects stay in every tool's metric denominator; "
                "a missing peer measurement is a miss."
            ),
            "intersection": (
                "Restrict scope to subjects for which every active decompiler produced "
                "usable requested-function output."
            ),
        },
        "difficulty_contract": (
            "Structural proxy: easy >= 2/3 exact GED agreement, hard <= 1/3, "
            "medium otherwise; unmeasured is explicit."
        ),
        "cost_contract": (
            "Per-function wall time is comparable within this run. USD is null unless "
            "an explicit priced execution source exists."
        ),
        "presets": presets,
    }


def build_mvp_by_decompiler(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    # DecBench-style fairness contract: once any compared tool can measure a
    # subject cell, that cell belongs to every tool's denominator. A missing
    # result is therefore a miss, not an invisible row that improves the mean.
    semantic_cells = {
        _subject_cell(row) for row in rows if _valid_semantic_score(row) is not None
    }
    type_cells = {
        _subject_cell(row) for row in rows if row.get("type_match_score") is not None
    }
    ged_cells = {
        _subject_cell(row) for row in rows if row.get("ged_score") is not None
    }

    by_tool: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_tool[str(row.get("decompiler") or "unknown")].append(row)

    result: dict[str, Any] = {}
    for decompiler, tool_rows in sorted(by_tool.items()):
        taxonomy = _empty_taxonomy()
        invalid_boundary = 0
        adapter_clean = 0
        semantic_scores: list[float] = []
        perfect = 0
        no_wrapper = 0
        times: list[float] = []
        # Type correctness vs DWARF ground truth (diagnostic evidence, not
        # part of semantic ranking). None = no ground truth for that
        # function, excluded rather than counted as a miss.
        type_match_scores: list[float] = []
        type_match_perfect = 0
        # Structural correctness vs source CFG (diagnostic evidence, not
        # part of semantic ranking). None = no CFG pair extracted for that
        # function (degenerate/unparseable), excluded rather than a miss.
        ged_scores: list[float] = []
        ged_perfect = 0

        for row in tool_rows:
            bucket = row.get("fail_taxonomy") or normalize_fail_taxonomy(row)
            if bucket not in taxonomy:
                bucket = "other"
            taxonomy[bucket] += 1

            diagnostics = row.get("output_diagnostics") or {}
            status = str(diagnostics.get("status") or "")
            if status in _BOUNDARY_STATUSES or bucket in {
                "boundary_mismatch",
                "whole_program_output",
            }:
                invalid_boundary += 1

            has_adapter_error = bool(row.get("error")) or bucket == "adapter_error"
            if not has_adapter_error and bucket not in {
                "boundary_mismatch",
                "whole_program_output",
            }:
                adapter_clean += 1

            if bucket == "no_wrapper" or row.get("fail_category") == "no_wrapper":
                no_wrapper += 1

            semantic = row.get("semantic_score")
            if (
                semantic is not None
                and not has_adapter_error
                and row.get("fail_category") != "no_wrapper"
                and bucket != "no_wrapper"
            ):
                value = float(semantic)
                semantic_scores.append(value)
                if value >= 1.0:
                    perfect += 1

            time_ms = row.get("time_ms")
            if isinstance(time_ms, (int, float)) and time_ms > 0:
                times.append(float(time_ms))

            type_match = row.get("type_match_score")
            if type_match is not None:
                tm_value = float(type_match)
                type_match_scores.append(tm_value)
                if tm_value >= 1.0:
                    type_match_perfect += 1

            ged = row.get("ged_score")
            if ged is not None:
                ged_value = float(ged)
                ged_scores.append(ged_value)
                if ged_value == 0.0:
                    ged_perfect += 1

        attempted = len(tool_rows)
        tested = len(semantic_scores)
        semantic_by_cell = {
            _subject_cell(row): score
            for row in tool_rows
            if (score := _valid_semantic_score(row)) is not None
        }
        shared_semantic_scores = [
            semantic_by_cell.get(cell, 0.0) for cell in semantic_cells
        ]
        shared_semantic_rows = len(semantic_cells)
        shared_type_rows = len(type_cells)
        shared_ged_rows = len(ged_cells)
        # Function-boundary diagnostic breakdown (infra first-class).
        boundary_status: dict[str, int] = defaultdict(int)
        addr_hit = 0
        name_hit = 0
        diag_n = 0
        for row in tool_rows:
            diagnostics = row.get("output_diagnostics") or {}
            if not diagnostics:
                continue
            diag_n += 1
            boundary_status[str(diagnostics.get("status") or "unknown")] += 1
            if diagnostics.get("expected_address_present"):
                addr_hit += 1
            if diagnostics.get("target_name_present"):
                name_hit += 1
        result[decompiler] = {
            "semantic": {
                "mean_pass_rate": (
                    round(sum(shared_semantic_scores) / shared_semantic_rows, 4)
                    if shared_semantic_rows
                    else None
                ),
                "observed_mean_pass_rate": (
                    round(sum(semantic_scores) / tested, 4) if tested else None
                ),
                "perfect_rows": perfect,
                "tested_rows": tested,
                "observed_rows": tested,
                "shared_rows": shared_semantic_rows,
                "perfect_rate": (
                    round(perfect / shared_semantic_rows, 4)
                    if shared_semantic_rows
                    else None
                ),
                "oracle_subject": _oracle_subject_for_rows(list(tool_rows)),
            },
            "type_match": {
                "mean_accuracy": (
                    round(sum(type_match_scores) / len(type_match_scores), 4)
                    if type_match_scores
                    else None
                ),
                "perfect_rows": type_match_perfect,
                "tested_rows": len(type_match_scores),
                "observed_rows": len(type_match_scores),
                "shared_rows": shared_type_rows,
                "perfect_rate": (
                    round(type_match_perfect / shared_type_rows, 4)
                    if shared_type_rows
                    else None
                ),
            },
            "ged": {
                "mean_ged": (
                    round(sum(ged_scores) / len(ged_scores), 4) if ged_scores else None
                ),
                "perfect_rows": ged_perfect,
                "tested_rows": len(ged_scores),
                "observed_rows": len(ged_scores),
                "shared_rows": shared_ged_rows,
                "perfect_rate": (
                    round(ged_perfect / shared_ged_rows, 4)
                    if shared_ged_rows
                    else None
                ),
            },
            "coverage": {
                "attempted": attempted,
                "adapter_clean": adapter_clean,
                "invalid_boundary": invalid_boundary,
                "semantic_tested": tested,
                "no_wrapper": no_wrapper,
            },
            "boundary": {
                "rows_with_diagnostics": diag_n,
                "by_status": dict(sorted(boundary_status.items())),
                "address_anchor_rate": (
                    round(addr_hit / diag_n, 4) if diag_n else None
                ),
                "name_anchor_rate": (
                    round(name_hit / diag_n, 4) if diag_n else None
                ),
            },
            "fail_taxonomy": taxonomy,
            "runtime": {
                "mean_ms": round(sum(times) / len(times), 2) if times else None,
                "rows_with_time": len(times),
            },
        }
    return result


def build_cross_variant(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Semantic mean by decompiler × compiler_variant (and parsed compiler/opt)."""
    groups: dict[tuple[str, str], dict[tuple[str, str, str], float]] = defaultdict(dict)
    attempted_groups: set[tuple[str, str]] = set()
    shared_by_variant: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for row in rows:
        decompiler = str(row.get("decompiler") or "unknown")
        variant = str(row.get("compiler_variant") or "unknown")
        key = (decompiler, variant)
        attempted_groups.add(key)
        semantic = _valid_semantic_score(row)
        if semantic is not None:
            cell = _subject_cell(row)
            groups[key][cell] = semantic
            shared_by_variant[variant].add(cell)

    by_decompiler_variant: dict[str, Any] = {}
    for decompiler, variant in sorted(attempted_groups):
        scores_by_cell = groups[(decompiler, variant)]
        observed_scores = list(scores_by_cell.values())
        shared_cells = shared_by_variant[variant]
        shared_scores = [scores_by_cell.get(cell, 0.0) for cell in shared_cells]
        compiler, opt = parse_compiler_variant(variant)
        entry = {
            "compiler_variant": variant,
            "compiler": compiler,
            "opt": opt,
            "tested_rows": len(observed_scores),
            "observed_rows": len(observed_scores),
            "shared_rows": len(shared_cells),
            "mean_pass_rate": (
                round(sum(shared_scores) / len(shared_scores), 4)
                if shared_scores
                else None
            ),
            "observed_mean_pass_rate": (
                round(sum(observed_scores) / len(observed_scores), 4)
                if observed_scores
                else None
            ),
            "perfect_rows": sum(1 for score in observed_scores if score >= 1.0),
        }
        by_decompiler_variant.setdefault(decompiler, []).append(entry)
    return {"by_decompiler_variant": by_decompiler_variant}


def load_cfg_summary(jsonl_path: Path | None) -> dict[str, Any]:
    """Aggregate cfg_parity JSONL into secondary summary (absent-safe)."""
    if jsonl_path is None or not jsonl_path.is_file():
        return {"status": "absent", "by_decompiler": {}}

    by_tool: dict[str, dict[str, int]] = defaultdict(lambda: {"match": 0, "mismatch": 0, "other": 0})
    try:
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            # Support both parity runner shapes.
            decompiler = (
                row.get("candidate")
                or row.get("decompiler")
                or row.get("tool")
                or "unknown"
            )
            status = str(row.get("status") or row.get("result") or "").lower()
            if status == "match":
                by_tool[str(decompiler)]["match"] += 1
            elif status in {"mismatch", "both_empty_invalid", "fetch_error"}:
                by_tool[str(decompiler)]["mismatch"] += 1
            else:
                by_tool[str(decompiler)]["other"] += 1
    except (OSError, json.JSONDecodeError):
        return {"status": "absent", "by_decompiler": {}}

    if not by_tool:
        return {"status": "absent", "by_decompiler": {}}

    out: dict[str, Any] = {}
    for tool, counts in sorted(by_tool.items()):
        total = counts["match"] + counts["mismatch"] + counts["other"]
        comparable = counts["match"] + counts["mismatch"]
        out[tool] = {
            **counts,
            "total": total,
            "match_rate": round(counts["match"] / comparable, 4) if comparable else None,
        }
    return {"status": "present", "by_decompiler": out}


def build_standard_summary(
    rows: Iterable[Mapping[str, Any]],
    *,
    cfg_jsonl: Path | None = None,
    holdout_status: str = "absent",
    oracle_subject: str | None = None,
    microbench: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the standard-set summary block for an envelope."""
    annotated = annotate_rows_with_taxonomy(rows)
    mvp = build_mvp_by_decompiler(annotated)
    if oracle_subject:
        for stats in mvp.values():
            if stats["semantic"].get("oracle_subject") is None:
                stats["semantic"]["oracle_subject"] = oracle_subject

    same_function = build_same_function_matrix(annotated)
    # Compact form for the envelope summary (full matrix available via CLI).
    same_function_summary = {
        "schema": same_function.get("schema"),
        "contract": same_function.get("contract"),
        "totals": same_function.get("totals"),
        "cohorts": same_function.get("cohorts"),
        "by_decompiler": {
            name: {
                "cohort": stats.get("cohort"),
                "by_status": stats.get("by_status"),
                "same_function_rate": stats.get("same_function_rate"),
                "same_function_loose_rate": stats.get("same_function_loose_rate"),
                "strict_denominator": stats.get("strict_denominator"),
                "loose_denominator": stats.get("loose_denominator"),
            }
            for name, stats in (same_function.get("by_decompiler") or {}).items()
        },
        "matrix": same_function.get("matrix"),
    }

    bare = aggregate_bare_compile(annotated)
    recompilation = aggregate_recompilation(annotated)
    readability_axis = aggregate_readability_axis(annotated)
    tracks = aggregate_track_taxonomy(annotated)
    speed = build_speed_extension(annotated, microbench=microbench)
    measurement_health = build_measurement_health(annotated)

    return {
        "schema": SUMMARY_SCHEMA,
        "mvp": {
            "same_function": same_function_summary,
            "by_decompiler": mvp,
            "measurement_health": measurement_health,
        },
        "secondary": {"cfg": load_cfg_summary(cfg_jsonl)},
        "extensions": {
            "holdout": {"status": holdout_status},
            "cross_variant": build_cross_variant(annotated),
            # EXT-10: bare-compile form quality (not ranking)
            "bare_compile": bare,
            # EXT-14: same-toolchain normalized assembly match (not ranking)
            "recompilation": recompilation,
            # EXT-11: readability diagnostic 2-axis (goto/temp/flag soup)
            "readability_axis": readability_axis,
            # EXT-12: realworld / multi-ISA / track pivots + fail taxonomy
            "tracks": tracks,
            # EXT-13: decompile latency (row time_ms + optional microbench)
            "speed": speed,
        },
        "diagnostics": {
            "denominator_contract": (
                "shared-by-subject-v1: if any compared decompiler measures a "
                "subject cell, missing measurements from peers remain in that "
                "metric's denominator"
            ),
            "note": (
                "source_similarity, ast_similarity, readability_proxy, bare_compile, "
                "track/ISA pivots, and speed are non-ranking diagnostic axes; "
                "correctness uses semantic evidence only (original_binary oracle). "
                "mvp.same_function is the infra honesty axis (requested function "
                "boundary), not a semantic ranking substitute."
            ),
            "bare_compile": bare,
            "recompilation": recompilation,
            "readability_axis": readability_axis,
            "tracks": tracks,
            "speed": speed,
        },
    }


def attach_summary_to_envelope(
    envelope: dict[str, Any],
    *,
    cfg_jsonl: Path | None = None,
    holdout_status: str | None = None,
    microbench: Mapping[str, Any] | Path | None = None,
) -> dict[str, Any]:
    """Mutate/return envelope with annotated rows and summary block."""
    rows = list(envelope.get("rows") or [])
    annotated = annotate_rows_with_taxonomy(rows)
    envelope["rows"] = annotated

    oracle = envelope.get("oracle") or {}
    oracle_subject = oracle.get("oracle_subject") if isinstance(oracle, dict) else None
    if holdout_status is None:
        corpus = (envelope.get("run") or {}).get("corpus")
        holdout_status = "linked" if corpus == "holdout" else "absent"

    micro_doc: Mapping[str, Any] | None = None
    if isinstance(microbench, Path):
        if microbench.is_file():
            try:
                loaded = json.loads(microbench.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    micro_doc = loaded
            except (OSError, json.JSONDecodeError):
                micro_doc = None
    elif isinstance(microbench, Mapping):
        micro_doc = microbench
    else:
        # Auto-attach latest microbench when present next to results/.
        default_micro = (
            Path(__file__).resolve().parent.parent
            / "results"
            / "speed"
            / "microbench_latest.json"
        )
        if default_micro.is_file():
            try:
                loaded = json.loads(default_micro.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    micro_doc = loaded
            except (OSError, json.JSONDecodeError):
                micro_doc = None

    default_cfg = Path(__file__).resolve().parent.parent / "results" / "cfg_parity" / "latest.jsonl"
    envelope["summary"] = build_standard_summary(
        annotated,
        cfg_jsonl=cfg_jsonl if cfg_jsonl is not None else default_cfg,
        holdout_status=holdout_status,
        oracle_subject=oracle_subject if isinstance(oracle_subject, str) else None,
        microbench=micro_doc,
    )
    return envelope
