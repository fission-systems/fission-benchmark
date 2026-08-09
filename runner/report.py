"""
Report generation: JSON → Markdown → HTML (GitHub Pages dashboard).
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from scoring import FunctionScore

if TYPE_CHECKING:
    from run_validity import LoadedResult, RunValidity

RESULTS_DIR = Path(__file__).parent.parent / "results"
DOCS_DIR = Path(__file__).parent.parent / "docs"

DECOMPILER_COLORS = {
    "fission":  "#6366f1",
    "ghidra":   "#f59e0b",

    "boomerang": "#10b981",
    "radare2":  "#ef4444",
    "angr":     "#06b6d4",
    "snowman":  "#8b5cf6",
    "revng":    "#ec4899",
    "reko":     "#f97316",
}


def _readability_summary(metrics: dict) -> str:
    if not metrics:
        return "—"
    gnr = metrics.get("generic_naming_ratio", {}).get("raw", {}).get("ratio")
    typ = metrics.get("type_specificity", {}).get("normalized")
    expr = metrics.get("expression_complexity", {}).get("normalized")
    cf = metrics.get("structured_control_flow", {}).get("normalized")
    artifacts = metrics.get("unresolved_artifacts", {}).get("raw", {}).get("total")
    values = []
    if gnr is not None:
        values.append(f"GNR {gnr:.2f}")
    if typ is not None:
        values.append(f"type {typ:.2f}")
    if expr is not None:
        values.append(f"expr {expr:.2f}")
    if cf is not None:
        values.append(f"cf {cf:.2f}")
    if artifacts is not None:
        values.append(f"art {artifacts}")
    return "<br>".join(values) if values else "—"


# ── Markdown ──────────────────────────────────────────────────────────────────

def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    sep = "|".join(["---"] * len(headers))
    head = "| " + " | ".join(headers) + " |"
    lines = [head, f"| {sep} |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def generate_markdown(
    scores: list[FunctionScore],
    corpus_split: str,
    *,
    verdict: RunValidity | None = None,
    measured_at: str | None = None,
    legacy: bool = False,
    standard_summary: dict | None = None,
) -> str:
    """Generate Markdown report.

    Parameters
    ----------
    measured_at:
        ISO timestamp when the benchmark was originally run.  Shown in the
        header as "Measured at" when provided (used for historical renders).
    legacy:
        When True, marks the report as a legacy re-render.
    standard_summary:
        Optional ``summary`` block (``standard-set-v1``). When omitted it is
        rebuilt from scores so MD matches the envelope contract.
    """
    rendered_at = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    try:
        from standard_summary import build_standard_summary, annotate_rows_with_taxonomy
    except ImportError:
        from runner.standard_summary import build_standard_summary, annotate_rows_with_taxonomy

    row_dicts = [
        {
            "decompiler": s.decompiler,
            "function_name": s.function_name,
            "compiler_variant": s.compiler_variant,
            "error": s.error,
            "fail_category": getattr(s, "fail_category", "") or "",
            "fail_taxonomy": getattr(s, "fail_taxonomy", "") or "",
            "semantic_score": s.semantic_score,
            "correctness_score": s.correctness_score,
            "time_ms": s.time_ms,
            "output_diagnostics": getattr(s, "output_diagnostics", None) or {},
            "oracle_evidence": getattr(s, "oracle_evidence", None) or {},
        }
        for s in scores
    ]
    summary = standard_summary or build_standard_summary(annotate_rows_with_taxonomy(row_dicts))


    lines = [
        "# Fission Benchmark Report",
        "",
    ]
    if legacy:
        lines += [
            "> [!WARNING]",
            "> **ARCHIVED LEGACY RESULT** — This file was originally measured before",
            "> the provenance envelope was introduced.  Original run timing and toolchain",
            "> version information are not available.  Official validity is **unverified**.",
            "",
        ]
    if measured_at:
        lines.append(f"**Measured at:** {measured_at}")
    lines += [
        f"**Rendered at:** {rendered_at}",
        f"**Corpus:** `{corpus_split}`",
        f"**Functions evaluated:** {len(set(s.function_name for s in scores))}",
        "",
        "---",
        "",
    ]

    # ── Run validity banner (shared engine) ───────────────────────────────────
    # We now strictly use the pre-evaluated verdict to ensure matrix constraints
    # evaluated in the caller context are faithfully represented here.
    if verdict is None:
        row_dicts = [
            {"decompiler": s.decompiler, "error": s.error,
             "fail_category": getattr(s, "fail_category", "") or ""}
            for s in scores
        ]
        from run_validity import evaluate_run
        verdict = evaluate_run(row_dicts, legacy=legacy)

    if not verdict.valid:
        reasons_str = ", ".join(verdict.reasons)
        if "no_fission_rows" in verdict.reasons:
            lines += [
                "## ⛔ INVALID RUN",
                "",
                "> **No Fission rows found in this result set.**",
                "> The benchmark did not run Fission — scores are not comparable.",
                "",
            ]
        elif legacy or "legacy_flat_list" in verdict.reasons:
            lines += [
                "## ⚠️ LEGACY / UNVERIFIED",
                "",
                f"> Fission {verdict.fission.clean}/{verdict.fission.attempted} rows clean "
                f"({verdict.fission.ratio * 100:.1f}%), "
                f"all-backend {verdict.overall.clean}/{verdict.overall.attempted} "
                f"({verdict.overall.ratio * 100:.1f}%).",
                "> Provenance incomplete — this result predates the envelope format.",
                "> Do not use these numbers as an official comparison.",
                "",
            ]
        else:
            lines += [
                f"## ⛔ INVALID RUN [{reasons_str}]",
                "",
                f"> Fission {verdict.fission.clean}/{verdict.fission.attempted} rows clean "
                f"({verdict.fission.ratio * 100:.1f}%), "
                f"all-backend {verdict.overall.clean}/{verdict.overall.attempted} "
                f"({verdict.overall.ratio * 100:.1f}%).",
                "> Results below are **not publishable** under current thresholds.",
                "",
            ]
    elif not verdict.publishable:
        publish_reasons_str = ", ".join(verdict.publish_reasons)
        lines += [
            "## ✅ VALID SMOKE MEASUREMENT",
            "",
            f"> Fission {verdict.fission.clean}/{verdict.fission.attempted} "
            f"({verdict.fission.ratio * 100:.1f}%), "
            f"all-backend {verdict.overall.clean}/{verdict.overall.attempted} "
            f"({verdict.overall.ratio * 100:.1f}%)",
            f"> ⚪ NOT PUBLISHABLE — {publish_reasons_str}",
            "",
        ]
    else:
        lines += [
            "## ✅ VALID RUN",
            "",
            f"> Fission {verdict.fission.clean}/{verdict.fission.attempted} "
            f"({verdict.fission.ratio * 100:.1f}%), "
            f"all-backend {verdict.overall.clean}/{verdict.overall.attempted} "
            f"({verdict.overall.ratio * 100:.1f}%)",
            "",
        ]

    lines += [
        "## MVP Summary — Standard set",
        "",
        "> **Primary ranking axis:** semantic pass rate (original-binary oracle when available).",
        "> **Also first-class:** coverage (attempted / adapter clean / boundary invalid / tested), "
        "fail taxonomy, runtime.",
        "> **Secondary:** CFG match (attached when cfg_parity JSONL present).",
        "> **Diagnostics only (non-ranking):** source similarity, AST similarity, readability proxies.",
        "> Readability proxies are not a final score until the human validation study completes.",
        "",
    ]

    # ── MVP table from standard_summary (single source of truth) ─────────────
    by_tool = (summary.get("mvp") or {}).get("by_decompiler") or {}

    def _sem_key(name: str) -> float:
        mean = (by_tool.get(name) or {}).get("semantic", {}).get("mean_pass_rate")
        return float(mean) if mean is not None else -1.0

    all_decomps = sorted(by_tool.keys(), key=lambda d: (-_sem_key(d), d))
    # Fission first for readability when present.
    if "fission" in all_decomps:
        all_decomps = ["fission"] + [d for d in all_decomps if d != "fission"]

    mvp_rows = []
    for d in all_decomps:
        stats = by_tool[d]
        cov = stats.get("coverage") or {}
        sem = stats.get("semantic") or {}
        tax = stats.get("fail_taxonomy") or {}
        rt = stats.get("runtime") or {}
        attempted = int(cov.get("attempted") or 0)
        adapter_clean = int(cov.get("adapter_clean") or 0)
        decomp_label = f"**{d}**" if adapter_clean > 0 else f"~~{d}~~ ⛔"
        mean_sem = sem.get("mean_pass_rate")
        mean_ms = rt.get("mean_ms")
        top_tax = sorted(
            ((k, n) for k, n in tax.items() if k != "ok" and n),
            key=lambda item: -item[1],
        )[:3]
        tax_str = " · ".join(f"{k}:{n}" for k, n in top_tax) if top_tax else "—"
        mvp_rows.append([
            decomp_label,
            str(attempted),
            str(adapter_clean),
            str(cov.get("invalid_boundary") or 0) or "—",
            str(cov.get("semantic_tested") or 0),
            f"{mean_sem * 100:.1f}%" if mean_sem is not None else "—",
            str(sem.get("perfect_rows") or 0) if mean_sem is not None else "—",
            str(cov.get("no_wrapper") or 0) or "—",
            tax_str,
            f"{mean_ms:.0f}ms" if mean_ms is not None else "—",
        ])
    lines.append(_md_table(
        [
            "Decompiler", "Attempted", "Adapter clean", "Boundary invalid",
            "Semantic tested", "Semantic mean", "Perfect", "No wrapper",
            "Fail taxonomy (top)", "Mean time",
        ],
        mvp_rows,
    ))

    # Cross-variant extension (compact)
    cross = ((summary.get("extensions") or {}).get("cross_variant") or {}).get(
        "by_decompiler_variant"
    ) or {}
    if cross:
        lines += ["", "### Extension — Cross-compiler / opt", ""]
        xv_rows = []
        for d, entries in sorted(cross.items(), key=lambda kv: (kv[0] != "fission", kv[0])):
            for e in entries:
                rate = e.get("mean_pass_rate")
                xv_rows.append([
                    d,
                    e.get("compiler_variant", ""),
                    e.get("compiler", ""),
                    e.get("opt") or "—",
                    str(e.get("tested_rows") or 0),
                    f"{rate * 100:.1f}%" if rate is not None else "—",
                ])
        lines.append(_md_table(
            ["Decompiler", "Variant", "Compiler", "Opt", "Tested", "Semantic mean"],
            xv_rows,
        ))

    cfg = (summary.get("secondary") or {}).get("cfg") or {}
    if cfg.get("status") == "present" and cfg.get("by_decompiler"):
        lines += ["", "### Secondary — CFG match", ""]
        cfg_rows = []
        for d, c in sorted(cfg["by_decompiler"].items()):
            rate = c.get("match_rate")
            cfg_rows.append([
                d,
                str(c.get("match") or 0),
                str(c.get("mismatch") or 0),
                f"{rate * 100:.1f}%" if rate is not None else "—",
            ])
        lines.append(_md_table(["Decompiler", "Match", "Mismatch", "Match rate"], cfg_rows))

    lines += [
        "",
        "### Diagnostics note",
        "",
        "> Source similarity is **not** listed in the MVP table. It remains on "
        "per-function rows for triage only.",
        "",
        "---",
        "",
        "## Per-Function Results",
        "",
    ]

    # Per function
    by_fn: dict[str, list[FunctionScore]] = defaultdict(list)
    for s in scores:
        by_fn[s.function_name].append(s)

    for fn_name, fn_scores in sorted(by_fn.items()):
        lines.append(f"### `{fn_name}`")
        # Consensus badge for this function
        badge = ""
        fission_scores_fn = [s for s in fn_scores if s.decompiler == "fission" and s.error is None]
        other_scores_fn = [s for s in fn_scores if s.decompiler != "fission" and s.error is None]
        if fission_scores_fn and other_scores_fn:
            fn_comp = fission_scores_fn[0].correctness_score
            other_values = [s.correctness_score for s in other_scores_fn if s.correctness_score is not None]
            others_avg = sum(other_values) / len(other_values) if other_values else None
            if getattr(fission_scores_fn[0], "correctness_rank", fission_scores_fn[0].consensus_rank) == 1:
                badge = " 🟢 Fission leads"
            elif fn_comp is not None and others_avg is not None and fn_comp < 0.20 and others_avg > 0.40:
                badge = " 🔴 Fission-only gap"
            elif fn_comp is not None and others_avg is not None and fn_comp < 0.20 and others_avg < 0.20:
                badge = " ⚪ Universally low (harness)"
        lines[-1] = lines[-1] + badge

        rows = []
        for s in sorted(fn_scores, key=lambda x: -(x.correctness_score if x.correctness_score is not None else -1.0)):
            correctness_rank = getattr(s, "correctness_rank", s.consensus_rank)
            rank = f"#{correctness_rank}" if correctness_rank else "—"
            fail_cat = getattr(s, "fail_category", "") or ""
            cat_icons = {
                "compile_error": "🔴 compile",
                "runtime_error": "🟠 runtime",
                "timeout": "🟡 timeout",
                "assertion_fail": "🟤 assert",
                "no_wrapper": "⚪ no_test",
                "adapter_error": "⚫ adapter",
                "": "✅" if not s.error else "❌",
            }
            status_icon = cat_icons.get(fail_cat, "❌")
            if s.error:
                status_icon = f"❌ {s.error[:30]}"
            sem_str = "n/a" if s.semantic_score is None else f"{s.semantic_score:.1%}"
            if s.semantic_score is not None and hasattr(s, "cases_passed") and getattr(s, "cases_total", 0) > 0:
                sem_str = f"{s.semantic_score:.1%} ({s.cases_passed}/{s.cases_total})"
            intrin_flag = " ⚠️intrin" if getattr(s, "uses_intrinsics", False) else ""
            rows.append([
                s.decompiler, s.compiler_variant,
                f"{s.correctness_score:.3f}" if s.correctness_score is not None else "n/a",
                f"{s.source_similarity:.3f}",
                sem_str + intrin_flag, rank,
                str(s.goto_count), str(s.nesting_depth),
                _readability_summary(getattr(s, "readability_metrics", {}) or {}),
                f"{s.time_ms}ms", status_icon,
            ])
        lines.append(_md_table(
            [
                "Decompiler", "Variant", "Correctness", "Similarity", "Semantic", "Correctness Rank",
                "Gotos", "Depth", "Readability Proxies", "Time", "Status",
            ],
            rows,
        ))
        lines.append("")

    # Overfitting alert
    lines += [
        "---",
        "",
        "## Overfitting Analysis",
        "",
        "Functions where **all** decompilers scored below 0.3 are marked as objectively hard.",
        "Functions where **only Fission** scored below 0.3 are marked as quality gaps.",
        "",
    ]

    hard, gaps = [], []
    for fn_name, fn_scores in by_fn.items():
        valid = [s for s in fn_scores if s.error is None and s.correctness_score is not None]
        if not valid:
            continue
        all_low = all(s.correctness_score < 0.20 for s in valid)
        fission_scores = [s for s in valid if s.decompiler == "fission"]
        others_ok = any(s.correctness_score >= 0.20 for s in valid if s.decompiler != "fission")
        fission_low = fission_scores and all(s.correctness_score < 0.20 for s in fission_scores)

        if all_low:
            hard.append(fn_name)
        elif fission_low and others_ok:
            gaps.append(fn_name)

    if hard:
        lines.append(f"**Objectively hard functions ({len(hard)}):** " + ", ".join(f"`{f}`" for f in hard))
    if gaps:
        lines.append(f"**Fission quality gaps ({len(gaps)}):** " + ", ".join(f"`{f}`" for f in gaps))
    if not hard and not gaps:
        lines.append("✅ No significant quality gaps detected.")

    return "\n".join(lines)


# ── HTML (GitHub Pages) ───────────────────────────────────────────────────────


def generate_html(
    scores: list[FunctionScore],
    corpus_split: str,
    *,
    verdict: RunValidity | None = None,
    measured_at: str | None = None,
    legacy: bool = False,
    results_dir: Path | None = None,
) -> str:
    results_dir = results_dir or RESULTS_DIR
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    by_decomp: dict[str, list[float]] = defaultdict(list)
    by_decomp_sem: dict[str, list[float]] = defaultdict(list)
    for s in scores:
        if s.error is None:
            by_decomp[s.decompiler].append(s.source_similarity)
            if s.semantic_score is not None:
                by_decomp_sem[s.decompiler].append(s.semantic_score)



    fn_names = sorted(set(s.function_name for s in scores))

    import os
    # Load corpus manifests to map (function_name, compiler_variant) to binary_name
    manifest_map = {}
    manifests_dir = Path(f"corpus/{corpus_split}/manifests")
    if manifests_dir.exists():
        for manifest_path in manifests_dir.glob("*.json"):
            try:
                with open(manifest_path) as f:
                    data = json.load(f)
                    for entry in data.get("functions", []):
                        fn_name = entry.get("name")
                        for var in entry.get("compiler_variants", []):
                            comp = var.get("compiler")
                            opt = var.get("opt")
                            bin_path = var.get("binary")
                            if fn_name and comp and opt and bin_path:
                                variant = f"{comp} {opt}"
                                manifest_map[(fn_name, variant)] = os.path.basename(bin_path)
            except Exception as e:
                print(f"Error loading manifest {manifest_path} for map: {e}")

    # We will serialize scores and color dict to JSON to inject directly into script
    serialized_scores = []
    for s in scores:
        has_parity_diff = False
        parity_diff_path = ""
        binary_name = manifest_map.get((s.function_name, s.compiler_variant))
        if binary_name:
            diff_file = results_dir / "parity_diffs" / binary_name / s.function_name / f"{s.decompiler}.json"
            if diff_file.exists():
                has_parity_diff = True
                parity_diff_path = f"../results/parity_diffs/{binary_name}/{s.function_name}/{s.decompiler}.json"
        
        serialized_scores.append({
            "decompiler": s.decompiler,
            "function_name": s.function_name,
            "compiler_variant": s.compiler_variant,
            "source_similarity": s.source_similarity,
            "semantic_score": s.semantic_score,
            "semantic_error": s.semantic_error,
            "fail_category": getattr(s, "fail_category", "") or "",
            "fail_taxonomy": getattr(s, "fail_taxonomy", "") or "",
            "cases_passed": getattr(s, "cases_passed", 0),
            "cases_total": getattr(s, "cases_total", 0),
            "correctness_score": getattr(s, "correctness_score", getattr(s, "composite_score", 0.0)),
            "correctness_rank": getattr(s, "correctness_rank", getattr(s, "consensus_rank", None)),
            "readability_proxy_score": getattr(s, "readability_proxy_score", None),
            "composite_score": getattr(s, "composite_score", 0.0),
            "structural_penalty": getattr(s, "structural_penalty", 0.0),
            "uses_intrinsics": getattr(s, "uses_intrinsics", False),
            "decompiled_code": getattr(s, "decompiled_code", "") or "",
            "decompiled_code_nir": getattr(s, "decompiled_code_nir", "") or "",
            "decompiled_code_hir": getattr(s, "decompiled_code_hir", "") or "",
            "pseudocode_layer": getattr(s, "pseudocode_layer", "") or "",
            "readability_metrics": getattr(s, "readability_metrics", {}) or {},
            "readability_metrics_nir": getattr(s, "readability_metrics_nir", {}) or {},
            "readability_proxy_score_nir": getattr(s, "readability_proxy_score_nir", None),
            "readability_metrics_hir": getattr(s, "readability_metrics_hir", {}) or {},
            "readability_proxy_score_hir": getattr(s, "readability_proxy_score_hir", None),
            "dual_layer_delta": getattr(s, "dual_layer_delta", {}) or {},
            "hir_semantic_guard": getattr(s, "hir_semantic_guard", {}) or {},
            "ast_similarity": getattr(s, "ast_similarity", {}) or {},
            "output_diagnostics": getattr(s, "output_diagnostics", {}) or {},
            "goto_count": s.goto_count,
            "nesting_depth": s.nesting_depth,
            "consensus_rank": s.consensus_rank,
            "time_ms": s.time_ms,
            "error": s.error,
            "has_parity_diff": has_parity_diff,
            "parity_diff_path": parity_diff_path,
            "bare_compile": getattr(s, "bare_compile", {}) or {},
            "track": getattr(s, "track", "") or "",
            "isa_format": getattr(s, "isa_format", {}) or {},
            "binary": getattr(s, "binary", "") or "",
            "corpus": getattr(s, "corpus", "") or "",
        })
    scores_json = json.dumps(serialized_scores, indent=2)

    # Run validity — use externally computed verdict when available.
    # Fallback: compute from rows (backward compat for direct callers).
    if verdict is None:
        row_dicts = [
            {"decompiler": s.decompiler, "error": s.error,
             "fail_category": getattr(s, "fail_category", "") or ""}
            for s in scores
        ]
        from run_validity import evaluate_run
        verdict = evaluate_run(row_dicts, legacy=legacy)

    fission_valid_count = verdict.fission.clean
    fission_total = verdict.fission.attempted

    run_meta_json = json.dumps({
        "valid": verdict.valid,
        "publishable": verdict.publishable,
        "fission_valid": fission_valid_count,
        "fission_total": fission_total,
        "timestamp": ts,
    })

    html_template = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fission Benchmark Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<style>
  :root {
    --bg: #090d16;
    --surface: #111827;
    --surface-hover: #1f2937;
    --border: #374151;
    --text: #f3f4f6;
    --muted: #9ca3af;
    --accent-indigo: #6366f1;
    --accent-cyan: #06b6d4;
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
  }
  
  * { box-sizing: border-box; margin: 0; padding: 0; }
  
  body {
    background:
      radial-gradient(circle at 10% 0%, rgba(20, 184, 166, 0.14), transparent 28rem),
      radial-gradient(circle at 90% 0%, rgba(99, 102, 241, 0.12), transparent 30rem),
      #0b0f17;
    color: var(--text);
    font-family: 'Inter', -apple-system, sans-serif;
    padding: 1.5rem;
    min-height: 100vh;
  }

  body > * {
    max-width: 1760px;
    margin-left: auto;
    margin-right: auto;
  }
  
  header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.5rem;
    gap: 1.5rem;
  }
  
  .brand h1 {
    font-size: 2.2rem;
    font-weight: 700;
    letter-spacing: 0;
    background: linear-gradient(to right, #60a5fa, #22d3ee 55%, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .brand p {
    color: var(--muted);
    font-size: 0.95rem;
    margin-top: 0.25rem;
  }
  
  .meta-badges {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 0.75rem;
  }
  
  .meta-badge {
    background: rgba(55, 65, 81, 0.4);
    border: 1px solid var(--border);
    padding: 0.5rem 1rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #e5e7eb;
  }
  
  .meta-badge strong {
    color: var(--accent-cyan);
  }

  .section-title {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 1rem;
    margin: 1.5rem 0 0.8rem;
  }

  .section-title h2 {
    font-size: 1rem;
    font-weight: 650;
  }

  .section-title p {
    color: var(--muted);
    font-size: 0.82rem;
  }

  .overview-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1rem;
    margin-bottom: 1.25rem;
  }

  .overview-card {
    background: rgba(17, 24, 39, 0.72);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    min-height: 118px;
  }

  .overview-label {
    color: var(--muted);
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .overview-value {
    font-size: 1.9rem;
    font-weight: 750;
    margin-top: 0.45rem;
  }

  .overview-sub {
    color: var(--muted);
    font-size: 0.78rem;
    line-height: 1.45;
    margin-top: 0.45rem;
  }

  .method-strip {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }

  .method-pill {
    background: rgba(31, 41, 55, 0.62);
    border: 1px solid rgba(75, 85, 99, 0.75);
    border-radius: 8px;
    padding: 0.85rem;
  }

  .method-pill strong {
    display: block;
    font-size: 0.83rem;
    margin-bottom: 0.28rem;
  }

  .method-pill span {
    color: var(--muted);
    font-size: 0.76rem;
    line-height: 1.35;
  }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  .kpi-card {
    background: rgba(17, 24, 39, 0.6);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
    backdrop-filter: blur(12px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .kpi-card:hover {
    transform: translateY(-2px);
    border-color: rgba(34, 211, 238, 0.65);
    box-shadow: 0 10px 25px -5px rgba(34, 211, 238, 0.12);
  }
  
  .kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }
  
  .kpi-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  
  .kpi-color-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }
  
  .kpi-value {
    font-size: 1.65rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
  }
  
  .kpi-bar-bg {
    background: #1f2937;
    height: 6px;
    border-radius: 9999px;
    margin-bottom: 0.75rem;
    overflow: hidden;
  }
  
  .kpi-bar-fill {
    height: 100%;
    border-radius: 9999px;
  }
  
  .kpi-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: var(--muted);
  }
  
  .kpi-stat-item strong {
    color: var(--text);
  }

  .charts-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }
  
  @media (max-width: 1024px) {
    .charts-grid { grid-template-columns: 1fr; }
    .overview-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .method-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    header { flex-direction: column; }
    .meta-badges { justify-content: flex-start; }
  }
  
  .card {
    background: rgba(17, 24, 39, 0.6);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    backdrop-filter: blur(12px);
  }

  .notice {
    background: rgba(245, 158, 11, 0.10);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #fcd34d;
    border-radius: 8px;
    padding: 0.85rem 1rem;
    margin-bottom: 1.5rem;
    font-size: 0.9rem;
    line-height: 1.45;
  }

  .taxonomy-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
  }

  .taxonomy-item {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.85rem;
    background: rgba(15, 23, 42, 0.6);
  }

  .taxonomy-item strong {
    display: block;
    font-size: 1.35rem;
    margin-bottom: 0.25rem;
  }

  .taxonomy-item span {
    color: var(--muted);
    font-size: 0.78rem;
  }

  .empty-state {
    border: 1px dashed rgba(148, 163, 184, 0.35);
    border-radius: 8px;
    padding: 2rem;
    color: var(--muted);
    text-align: center;
  }

  @media (max-width: 640px) {
    body { padding: 1rem; }
    .brand h1 { font-size: 1.75rem; }
    .overview-grid, .method-strip, .taxonomy-grid { grid-template-columns: 1fr; }
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.25rem;
  }
  
  .card h2 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #f3f4f6;
  }
  
  .card-actions select {
    background: #1f2937;
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    font-size: 0.85rem;
    outline: none;
    cursor: pointer;
  }
  
  .chart-container {
    position: relative;
    height: 280px;
    width: 100%;
  }

  .table-controls {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 1rem;
    align-items: center;
  }
  
  .search-wrapper {
    flex-grow: 1;
    position: relative;
    min-width: 200px;
  }
  
  .search-wrapper input {
    width: 100%;
    background: #1f2937;
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.875rem;
    outline: none;
    transition: all 0.2s;
  }
  
  .search-wrapper input:focus {
    border-color: var(--accent-indigo);
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
  }
  
  .filter-select {
    background: #1f2937;
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.875rem;
    outline: none;
    cursor: pointer;
  }
  
  .filter-select:focus {
    border-color: var(--accent-indigo);
  }

  .table-container {
    overflow-x: auto;
    border-radius: 8px;
    border: 1px solid var(--border);
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    text-align: left;
  }
  
  th {
    background: #1f2937;
    color: #e5e7eb;
    font-weight: 600;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
    cursor: pointer;
    user-select: none;
  }
  
  th:hover {
    background: #374151;
  }
  
  th.sorted-asc::after { content: " ▲"; font-size: 0.75rem; }
  th.sorted-desc::after { content: " ▼"; font-size: 0.75rem; }
  
  td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
    color: #d1d5db;
    vertical-align: middle;
  }
  
  tr:last-child td { border-bottom: none; }
  
  tr:hover td {
    background: rgba(255, 255, 255, 0.02);
  }
  
  tr.highlighted-row td {
    background: rgba(99, 102, 241, 0.05);
    border-left: 3px solid var(--accent-indigo);
  }
  
  tr.highlighted-row:hover td {
    background: rgba(99, 102, 241, 0.08);
  }
  
  .sim-cell {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .sim-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    min-width: 45px;
    text-align: center;
  }
  
  .sim-badge.excellent { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
  .sim-badge.good { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
  .sim-badge.weak { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
  .sim-badge.poor { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
  
  .sim-bar-bg {
    background: #1f2937;
    height: 6px;
    border-radius: 9999px;
    width: 80px;
    overflow: hidden;
  }
  .sim-bar-fill { height: 100%; border-radius: 9999px; }
  .sim-bar-fill.excellent { background: #10b981; }
  .sim-bar-fill.good { background: #3b82f6; }
  .sim-bar-fill.weak { background: #f59e0b; }
  .sim-bar-fill.poor { background: #ef4444; }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .badge.success { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); }
  .badge.error { background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); }
  .badge.warning { background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.22); }
  .badge.neutral { background: rgba(148, 163, 184, 0.1); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.2); }
  .badge-button { appearance: none; font-family: inherit; cursor: pointer; }
  .badge-button:hover { filter: brightness(1.12); }
  
  .rank-badge {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    display: inline-block;
  }
  .rank-gold { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
  .rank-silver { background: rgba(156, 163, 175, 0.2); color: #e5e7eb; border: 1px solid rgba(156, 163, 175, 0.4); }
  .rank-bronze { background: rgba(180, 83, 9, 0.2); color: #f97316; border: 1px solid rgba(180, 83, 9, 0.4); }
  .rank-other { color: var(--muted); }

  /* ── Export buttons ── */
  .export-btn { background: #1f2937; border: 1px solid #374151; color: #d1d5db; padding: 0.4rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 500; transition: all 0.15s; white-space: nowrap; }
  .export-btn:hover { background: #374151; border-color: #6366f1; color: #fff; }
  .export-btn.copied { background: #065f46; border-color: #10b981; color: #6ee7b7; }
  .code-btn { background: #1e293b; border: 1px solid #334155; color: #94a3b8; padding: 3px 10px; border-radius: 5px; cursor: pointer; font-size: 0.78rem; transition: all 0.15s; }
  .code-btn:hover { background: #334155; color: #e2e8f0; border-color: #6366f1; }
  /* ── Code Viewer Modal ── */
  #codeModal { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:2000; justify-content:center; align-items:center; }
  #codeModal.open { display:flex; }
  .code-modal-inner { background:#0f172a; border:1px solid #334155; border-radius:14px; width:90%; max-width:1000px; max-height:88vh; display:flex; flex-direction:column; box-shadow:0 25px 50px rgba(0,0,0,0.7); }
  .code-modal-header { padding:1rem 1.5rem; border-bottom:1px solid #1e293b; display:flex; justify-content:space-between; align-items:center; background:#1e293b; border-radius:14px 14px 0 0; }
  .code-modal-header h3 { font-size:0.95rem; font-weight:600; color:#e2e8f0; margin:0; }
  .code-modal-body { flex:1; overflow:auto; }
  .code-modal-body pre { margin:0; padding:1.5rem; font-family:'JetBrains Mono','Fira Code','Cascadia Code',monospace; font-size:0.82rem; line-height:1.6; color:#e2e8f0; background:#090d16; white-space:pre; overflow-x:auto; }
  .code-modal-footer { padding:0.75rem 1.5rem; border-top:1px solid #1e293b; display:flex; gap:0.75rem; align-items:center; justify-content:space-between; background:#0f172a; border-radius:0 0 14px 14px; }
  /* ── Syntax highlighting ── */
  .code-keyword { color:#c792ea; font-weight:600; }
  .code-type { color:#82aaff; }
  .code-number { color:#f78c6c; }
  .code-comment { color:#637777; font-style:italic; }
  .code-string { color:#c3e88d; }

  .pagination-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1rem;
    font-size: 0.875rem;
    color: var(--muted);
  }
  
  .pagination-buttons {
    display: flex;
    gap: 0.5rem;
  }
  
  .pagination-btn {
    background: #1f2937;
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .pagination-btn:hover:not(:disabled) {
    background: #374151;
    border-color: var(--accent-indigo);
  }
  
  .pagination-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .parity-btn { background: #1e1b4b; border: 1px solid #312e81; color: #c7d2fe; padding: 3px 10px; border-radius: 5px; cursor: pointer; font-size: 0.78rem; transition: all 0.15s; }
  .parity-btn:hover { background: #312e81; color: #eff6ff; border-color: #6366f1; }
  .tab-btn { background: #1f2937; border: 1px solid var(--border); color: var(--muted); padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: all 0.15s; }
  .tab-btn:hover { background: #374151; color: var(--text); }
  .tab-btn.active { background: var(--accent-indigo); border-color: var(--accent-indigo); color: white; }

  .validity-banner {
    padding: 1rem;
    margin-bottom: 2rem;
    border-radius: 8px;
    font-weight: 500;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .validity-banner.valid {
    background-color: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.2);
    color: #4ade80;
  }
  .validity-banner.invalid {
    background-color: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: #f87171;
  }
  .validity-banner.legacy {
    background-color: rgba(234, 179, 8, 0.1);
    border: 1px solid rgba(234, 179, 8, 0.2);
    color: #facc15;
  }
  
  .validity-reason-list {
    margin: 0;
    padding-left: 1.5rem;
    font-size: 0.9rem;
    color: var(--muted);
  }
</style>
</head>
<body>

<header>
  <div class="brand">
    <h1>🔬 Fission Benchmark</h1>
    <p>Cross-Decompiler Semantic Parity & Similarity Dashboard</p>
  </div>
  <div class="meta-badges">
    <div class="meta-badge">Corpus: <strong id="corpusName">__CORPUS_SPLIT__</strong></div>
    <div class="meta-badge">Functions: <strong id="funcCount">__FUNCTIONS_COUNT__</strong></div>
    <div class="meta-badge">Updated: <strong id="genTime">__TS__</strong></div>
  </div>
</header>

<div id="validityContainer">__VALIDITY_BANNER__</div>

<div class="notice">
  Readability values shown below are unvalidated proxy metrics. They are recorded as raw evidence only;
  no final readability composite is published until the human comprehension study validates which proxies correlate with accuracy and response time.
</div>

<div class="section-title">
  <div>
    <h2>Benchmark Health</h2>
    <p>Correctness and readability are intentionally separate axes.</p>
  </div>
</div>
<div class="overview-grid" id="overviewContainer"></div>

<div class="method-strip">
  <div class="method-pill"><strong>Correctness</strong><span>Semantic score comes from compile and test execution, not text similarity.</span></div>
  <div class="method-pill"><strong>Readability</strong><span>Proxy metrics are raw evidence only until human validation is complete.</span></div>
  <div class="method-pill"><strong>Similarity</strong><span>Source similarity is retained for context, not treated as readability.</span></div>
  <div class="method-pill"><strong>Parity</strong><span>Assembly, decode, p-code, CFG, function discovery, and IR invariant rows are emitted separately.</span></div>
</div>

<div class="section-title">
  <div>
    <h2>Decompiler Scoreboard</h2>
    <p>Cards separate output coverage, semantic correctness, source similarity, proxy evidence emission, AST parse coverage, and runtime.</p>
  </div>
</div>
<div class="kpi-grid" id="kpiContainer"></div>

<!-- Charts Section -->
<div class="charts-grid">
  <div class="card">
    <div class="card-header">
      <h2>Correctness, Readability Proxy, Similarity</h2>
    </div>
    <div class="chart-container">
      <canvas id="barChart"></canvas>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <h2>Readability Proxy Profile</h2>
    </div>
    <div class="chart-container">
      <canvas id="readabilityChart"></canvas>
    </div>
  </div>
  
  <div class="card">
    <div class="card-header">
      <h2>Per-Function Correctness Score</h2>
      <div class="card-actions">
        <select id="functionChartSelector"></select>
      </div>
    </div>
    <div class="chart-container">
      <canvas id="perFuncChart"></canvas>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <h2>Failure Taxonomy</h2>
    </div>
    <div class="taxonomy-grid" id="failureTaxonomy"></div>
  </div>
</div>

<!-- Detailed Table Section -->
<div class="card">
  <div class="card-header">
    <h2>Detailed Decompilation Results</h2>
  </div>
  
  <div class="table-controls">
    <div class="search-wrapper">
      <input type="text" id="searchInput" placeholder="Search functions, compilers, or decompilers...">
    </div>
    <select id="decompilerFilter" class="filter-select">
      <option value="all">All Decompilers</option>
    </select>
    <select id="variantFilter" class="filter-select">
      <option value="all">All Variants</option>
    </select>
    <select id="gapFilter" class="filter-select">
      <option value="all">All Results</option>
      <option value="fission-gap">Fission Quality Gaps</option>
      <option value="hard">Objectively Hard</option>
      <option value="gotos">Fission with Gotos</option>
    </select>
  <div class="export-buttons" style="display:flex;gap:0.5rem;align-items:center;flex-shrink:0;">
    <button onclick="exportJSON()" class="export-btn" title="Download full results as JSON">⬇ JSON</button>
    <button onclick="exportCSV()" class="export-btn" title="Download filtered results as CSV">⬇ CSV</button>
    <button onclick="copyJSON()" class="export-btn copy-btn" id="copyJsonBtn" title="Copy filtered results JSON to clipboard">📋 Copy JSON</button>
    <button onclick="copyCSV()" class="export-btn copy-btn" id="copyCsvBtn" title="Copy filtered results CSV to clipboard">📋 Copy CSV</button>
  </div>
  </div>
  
  <div class="table-container">
    <table id="resultsTable">
      <thead>
        <tr>
          <th data-key="function_name">Function</th>
          <th data-key="compiler_variant">Variant</th>
          <th data-key="decompiler">Decompiler</th>
          <th data-key="correctness_score">Correctness</th>
          <th data-key="semantic_score">Semantic</th>
          <th>Readability Proxies</th>
          <th data-key="correctness_rank">Correctness Rank</th>
          <th data-key="goto_count">Gotos</th>
          <th data-key="time_ms">Time</th>
          <th>Status</th>
          <th>Code</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
  
  <div class="pagination-container">
    <span id="pageInfo"></span>
    <div class="pagination-buttons">
      <button id="prevBtn" class="pagination-btn">Prev</button>
      <button id="nextBtn" class="pagination-btn">Next</button>
    </div>
  </div>
</div>

<script>
const SCORES = __SCORES_JSON__;
const DECOMPILER_COLORS = __DECOMPILER_COLORS__;
const RUN_META = __RUN_META_JSON__;

// Helper to group scores
const scoresByGroup = {};
SCORES.forEach((s, index) => {
  s._rowId = index;
  const key = s.function_name + '|' + s.compiler_variant;
  if (!scoresByGroup[key]) scoresByGroup[key] = [];
  scoresByGroup[key].push(s);
});

// Setup metadata and filters
const fnNames = [...new Set(SCORES.map(s => s.function_name))].sort();
const variants = [...new Set(SCORES.map(s => s.compiler_variant))].sort();
const decompilers = [...new Set(SCORES.map(s => s.decompiler))].sort();

// Populate function selector for chart
const fnChartSel = document.getElementById('functionChartSelector');
fnNames.forEach(fn => {
  const opt = document.createElement('option');
  opt.value = fn;
  opt.textContent = fn;
  fnChartSel.appendChild(opt);
});
if (fnNames.length > 0) fnChartSel.value = fnNames[0];

// Populate filters
const decompFilter = document.getElementById('decompilerFilter');
decompilers.forEach(d => {
  const opt = document.createElement('option');
  opt.value = d;
  opt.textContent = d;
  decompFilter.appendChild(opt);
});

const variantFilter = document.getElementById('variantFilter');
variants.forEach(v => {
  const opt = document.createElement('option');
  opt.value = v;
  opt.textContent = v;
  variantFilter.appendChild(opt);
});

function pct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A';
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function mean(rows, selector) {
  if (!rows.length) return null;
  return rows.reduce((sum, row) => sum + Number(selector(row) || 0), 0) / rows.length;
}

function hasOutput(row) {
  return Boolean(!row.error && row.decompiled_code && row.decompiled_code.trim());
}

function hasSemanticCases(row) {
  return Number(row.cases_total || 0) > 0;
}

function semanticPasses(row) {
  return hasSemanticCases(row) && Number(row.cases_passed || 0) === Number(row.cases_total || 0);
}

function hasReadabilityEvidence(row) {
  return Boolean(row.readability_metrics && Object.keys(row.readability_metrics).length > 0);
}

function hasAstParseEvidence(row) {
  return hasReadabilityEvidence(row) && row.readability_metrics.parse_ok === true;
}

function readabilityValue(row, metric) {
  const rm = row.readability_metrics || {};
  if (metric === 'gnr') return rm.generic_naming_ratio?.raw?.ratio;
  if (metric === 'type') return rm.type_specificity?.normalized;
  if (metric === 'expr') return rm.expression_complexity?.normalized;
  if (metric === 'cf') return rm.structured_control_flow?.normalized;
  if (metric === 'artifacts') return rm.unresolved_artifacts?.raw?.total;
  return undefined;
}

function finiteValues(rows, metric) {
  return rows
    .map(row => readabilityValue(row, metric))
    .filter(value => value !== undefined && value !== null && Number.isFinite(Number(value)))
    .map(Number);
}

function averageReadability(rows, metric) {
  const values = finiteValues(rows, metric);
  return values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
}

// Calculate global and per-decompiler statistics.
const totalRows = SCORES.length;
const totalGroups = Object.keys(scoresByGroup).length;
const totalOutputRows = SCORES.filter(hasOutput).length;
const totalAdapterErrors = SCORES.filter(s => s.error).length;
const totalSemanticRows = SCORES.filter(hasSemanticCases).length;
const totalSemanticPassed = SCORES.filter(semanticPasses).length;
const totalAvgSemantic = mean(SCORES.filter(hasSemanticCases), s => s.semantic_score);
const totalWithReadabilityEvidence = SCORES.filter(s => hasOutput(s) && hasReadabilityEvidence(s)).length;
const totalAstParseOk = SCORES.filter(s => hasOutput(s) && hasAstParseEvidence(s)).length;
const totalDirectFunctions = SCORES.filter(s => s.output_diagnostics?.status === 'direct_function').length;
const totalNeedsNormalization = SCORES.filter(s => s.output_diagnostics?.status === 'needs_normalization').length;
const totalBoundaryMismatch = SCORES.filter(s => s.output_diagnostics?.status === 'boundary_mismatch').length;
const totalWholeProgram = SCORES.filter(s => s.output_diagnostics?.status === 'whole_program_output').length;

const overviewContainer = document.getElementById('overviewContainer');
[
  {
    label: 'Result Rows',
    value: totalRows.toLocaleString(),
    sub: `${fnNames.length} functions × ${variants.length} variants × ${decompilers.length} decompilers`
  },
  {
    label: 'Decompiler Output',
    value: totalRows ? `${((totalOutputRows / totalRows) * 100).toFixed(1)}%` : 'N/A',
    sub: `${totalOutputRows.toLocaleString()} rows returned code, ${totalAdapterErrors.toLocaleString()} adapter errors`
  },
  {
    label: 'Function Boundary',
    value: totalOutputRows ? `${((totalDirectFunctions / totalOutputRows) * 100).toFixed(1)}%` : 'N/A',
    sub: `${totalDirectFunctions} direct, ${totalNeedsNormalization} normalize, ${totalBoundaryMismatch} boundary mismatch, ${totalWholeProgram} whole-program`
  },
  {
    label: 'Semantic Correctness',
    value: totalSemanticRows ? pct(totalAvgSemantic) : 'N/A',
    sub: totalSemanticRows
      ? `${totalSemanticPassed.toLocaleString()} / ${totalSemanticRows.toLocaleString()} tested rows passed every execution check`
      : 'No rows had executable semantic test cases'
  },
  {
    label: 'Proxy Evidence',
    value: totalOutputRows ? `${((totalWithReadabilityEvidence / totalOutputRows) * 100).toFixed(1)}%` : 'N/A',
    sub: `${totalWithReadabilityEvidence.toLocaleString()} output rows include readability proxy fields`
  },
  {
    label: 'AST Parse Coverage',
    value: totalOutputRows ? `${((totalAstParseOk / totalOutputRows) * 100).toFixed(1)}%` : 'N/A',
    sub: `${totalAstParseOk.toLocaleString()} output rows parsed successfully for AST-based metrics`
  }
].forEach(item => {
  const card = document.createElement('div');
  card.className = 'overview-card';
  card.innerHTML = `
    <div class="overview-label">${item.label}</div>
    <div class="overview-value">${item.value}</div>
    <div class="overview-sub">${item.sub}</div>
  `;
  overviewContainer.appendChild(card);
});

const stats = {};
decompilers.forEach(d => {
  const decScores = SCORES.filter(s => s.decompiler === d);
  const outputScores = decScores.filter(hasOutput);
  const semanticRows = decScores.filter(hasSemanticCases);
  const semanticPassed = decScores.filter(semanticPasses).length;
  const avgSim = mean(outputScores, s => s.source_similarity);
  const avgSem = mean(semanticRows, s => s.semantic_score);
  const correctnessRows = outputScores.filter(s => s.correctness_score !== null && s.correctness_score !== undefined);
  const avgCorrectness = mean(correctnessRows, s => s.correctness_score);
  const avgReadabilityProxy = mean(
    outputScores.filter(s => hasAstParseEvidence(s) && s.readability_proxy_score !== null && s.readability_proxy_score !== undefined),
    s => s.readability_proxy_score
  );
  const outputCount = outputScores.length;
  const outputRate = decScores.length ? (outputCount / decScores.length) * 100 : null;
  const semanticRate = semanticRows.length ? semanticPassed / semanticRows.length : null;
  const adapterErrors = decScores.filter(s => s.error).length;
  const totalGotos = decScores.reduce((sum, s) => sum + (s.goto_count || 0), 0);
  const avgTime = mean(decScores.filter(s => Number(s.time_ms || 0) > 0), s => s.time_ms);
  const directFunctions = outputScores.filter(s => s.output_diagnostics?.status === 'direct_function').length;
  const needsNormalization = outputScores.filter(s => s.output_diagnostics?.status === 'needs_normalization').length;
  const boundaryMismatch = outputScores.filter(s => s.output_diagnostics?.status === 'boundary_mismatch').length;
  const wholeProgram = outputScores.filter(s => s.output_diagnostics?.status === 'whole_program_output').length;
  const boundaryRate = outputScores.length ? (directFunctions / outputScores.length) * 100 : null;
  const readabilityEvidenceRows = outputScores.filter(hasReadabilityEvidence);
  const astParseRows = outputScores.filter(hasAstParseEvidence);
  const readabilityEvidenceCoverage = outputScores.length ? (readabilityEvidenceRows.length / outputScores.length) * 100 : null;
  const astParseCoverage = outputScores.length ? (astParseRows.length / outputScores.length) * 100 : null;
  const avgGnr = averageReadability(astParseRows, 'gnr');
  const avgType = averageReadability(astParseRows, 'type');
  const avgExpr = averageReadability(astParseRows, 'expr');
  const avgCf = averageReadability(astParseRows, 'cf');
  const avgArtifacts = averageReadability(readabilityEvidenceRows, 'artifacts');

  stats[d] = {
    avgSim, avgSem, avgCorrectness, avgReadabilityProxy, outputRate, outputCount, adapterErrors,
    semanticRate, semanticPassed, semanticTotal: semanticRows.length,
    totalGotos, avgTime, directFunctions, needsNormalization, boundaryMismatch, wholeProgram, boundaryRate,
    readabilityEvidenceCoverage, astParseCoverage, astParseCount: astParseRows.length,
    avgGnr, avgType, avgExpr, avgCf, avgArtifacts
  };
});

// Render decompiler cards.
const kpiContainer = document.getElementById('kpiContainer');
decompilers.forEach(d => {
  const s = stats[d];
  const color = DECOMPILER_COLORS[d] || '#888';
  const hasAnyOutput = s.outputCount > 0;
  const scoreLabel = hasAnyOutput ? `${pct(s.avgCorrectness)} <span style="font-size: 0.85rem; color: var(--muted); font-weight: normal;">correctness</span>` : '<span style="font-size:1.35rem;color:var(--muted);">No output</span>';
  const semanticText = s.semanticTotal ? `${pct(s.avgSem)} avg (${s.semanticPassed}/${s.semanticTotal} full)` : 'N/A';
  const evidenceText = s.readabilityEvidenceCoverage === null ? 'N/A' : `${s.readabilityEvidenceCoverage.toFixed(0)}%`;
  const astParseText = s.astParseCoverage === null ? 'N/A' : `${s.astParseCoverage.toFixed(0)}% (${s.astParseCount}/${s.outputCount})`;
  const boundaryText = s.boundaryRate === null ? 'N/A' : `${s.boundaryRate.toFixed(0)}% (${s.directFunctions}/${s.outputCount})`;
  const artifactsText = s.readabilityEvidenceCoverage === null ? 'N/A' : s.avgArtifacts.toFixed(1);
  const avgTimeText = s.avgTime === null ? 'N/A' : `${s.avgTime.toFixed(0)}ms`;
  
  const card = document.createElement('div');
  card.className = 'kpi-card';
  card.innerHTML = `
    <div class="kpi-header">
      <span class="kpi-title">${d}</span>
      <span class="kpi-color-dot" style="background-color: ${color}"></span>
    </div>
    <div class="kpi-value">${scoreLabel}</div>
    <div class="kpi-bar-bg">
      <div class="kpi-bar-fill" style="width: ${hasAnyOutput ? Math.min(100, s.avgCorrectness * 100) : 0}%; background-color: ${color}"></div>
    </div>
    <div class="kpi-stats">
      <div class="kpi-stat-item">Semantic: <strong>${semanticText}</strong></div>
      <div class="kpi-stat-item">Similarity: <strong>${pct(s.avgSim)}</strong></div>
      <div class="kpi-stat-item">Output: <strong>${s.outputRate === null ? 'N/A' : `${s.outputRate.toFixed(0)}% (${s.outputCount}/${SCORES.filter(x => x.decompiler === d).length})`}</strong></div>
      <div class="kpi-stat-item">Boundary: <strong>${boundaryText}</strong></div>
      <div class="kpi-stat-item">Readability Proxy: <strong>${s.avgReadabilityProxy === null ? 'N/A' : pct(s.avgReadabilityProxy)}</strong></div>
      <div class="kpi-stat-item">Evidence: <strong>${evidenceText}</strong></div>
      <div class="kpi-stat-item">AST Parse: <strong>${astParseText}</strong></div>
      <div class="kpi-stat-item">Artifacts: <strong>${artifactsText}</strong></div>
      <div class="kpi-stat-item">Avg Time: <strong>${avgTimeText}</strong></div>
      ${s.adapterErrors ? `<div class="kpi-stat-item">Adapter Errors: <strong>${s.adapterErrors}</strong></div>` : ''}
    </div>
  `;
  kpiContainer.appendChild(card);
});

// Setup global metric chart.
const globalBarCtx = document.getElementById('barChart').getContext('2d');
const scoreForSort = d => stats[d].avgCorrectness ?? -1;
const sortedDecompilers = [...decompilers].sort((a, b) => scoreForSort(b) - scoreForSort(a));
new Chart(globalBarCtx, {
  type: 'bar',
  data: {
    labels: sortedDecompilers,
    datasets: [
      {
        label: 'Mean Semantic',
        data: sortedDecompilers.map(d => stats[d].avgSem),
        backgroundColor: 'rgba(16, 185, 129, 0.72)',
        borderRadius: 5
      },
      {
        label: 'Correctness Score',
        data: sortedDecompilers.map(d => stats[d].avgCorrectness),
        backgroundColor: 'rgba(96, 165, 250, 0.74)',
        borderRadius: 5
      },
      {
        label: 'Readability Proxy',
        data: sortedDecompilers.map(d => stats[d].avgReadabilityProxy),
        backgroundColor: 'rgba(168, 85, 247, 0.54)',
        borderRadius: 5
      },
      {
        label: 'Source Similarity',
        data: sortedDecompilers.map(d => stats[d].avgSim),
        backgroundColor: 'rgba(245, 158, 11, 0.70)',
        borderRadius: 5
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top', labels: { color: '#cbd5e1' } } },
    scales: {
      y: { min: 0, max: 1, grid: { color: '#374151' }, ticks: { color: '#9ca3af' } },
      x: { grid: { display: false }, ticks: { color: '#9ca3af' } }
    }
  }
});

// Setup readability proxy chart. GNR/artifacts are lower-is-better and shown raw.
const readabilityCtx = document.getElementById('readabilityChart').getContext('2d');
new Chart(readabilityCtx, {
  type: 'bar',
  data: {
    labels: sortedDecompilers,
    datasets: [
      {
        label: 'Generic Naming Ratio',
        data: sortedDecompilers.map(d => stats[d].astParseCoverage === null ? null : stats[d].avgGnr),
        backgroundColor: 'rgba(239, 68, 68, 0.66)',
        borderRadius: 5
      },
      {
        label: 'Type Specificity',
        data: sortedDecompilers.map(d => stats[d].astParseCoverage === null ? null : stats[d].avgType),
        backgroundColor: 'rgba(34, 211, 238, 0.70)',
        borderRadius: 5
      },
      {
        label: 'Expression Simplicity',
        data: sortedDecompilers.map(d => stats[d].astParseCoverage === null ? null : 1 - Math.min(1, stats[d].avgExpr)),
        backgroundColor: 'rgba(168, 85, 247, 0.66)',
        borderRadius: 5
      },
      {
        label: 'Structured CF',
        data: sortedDecompilers.map(d => stats[d].astParseCoverage === null ? null : stats[d].avgCf),
        backgroundColor: 'rgba(16, 185, 129, 0.66)',
        borderRadius: 5
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top', labels: { color: '#cbd5e1' } } },
    scales: {
      y: { min: 0, max: 1, grid: { color: '#374151' }, ticks: { color: '#9ca3af' } },
      x: { grid: { display: false }, ticks: { color: '#9ca3af' } }
    }
  }
});

const failureCounts = {};
SCORES.forEach(s => {
  const key = s.error ? 'decompiler_error' : (s.fail_category || 'no_failure_category');
  failureCounts[key] = (failureCounts[key] || 0) + 1;
});
const failureTaxonomy = document.getElementById('failureTaxonomy');
Object.entries(failureCounts)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 6)
  .forEach(([label, count]) => {
    const item = document.createElement('div');
    item.className = 'taxonomy-item';
    item.innerHTML = `<strong>${count.toLocaleString()}</strong><span>${label.replaceAll('_', ' ')}</span>`;
    failureTaxonomy.appendChild(item);
  });
if (!Object.keys(failureCounts).length) {
  failureTaxonomy.innerHTML = '<div class="empty-state">No failure records.</div>';
}

// Setup interactive Per-Function Chart
let perFuncChart = null;
function updatePerFuncChart(funcName) {
  const funcScores = SCORES.filter(s => s.function_name === funcName);
  const datasets = decompilers.map(d => {
    const dScores = funcScores.filter(s => s.decompiler === d);
    return {
      label: d,
      data: variants.map(v => {
        const match = dScores.find(s => s.compiler_variant === v);
        return match && hasOutput(match) ? match.correctness_score : null;
      }),
      backgroundColor: DECOMPILER_COLORS[d] || '#888',
      borderRadius: 4
    };
  });
  
  if (perFuncChart) perFuncChart.destroy();
  
  const ctx = document.getElementById('perFuncChart').getContext('2d');
  perFuncChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: variants,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'top', labels: { color: '#9ca3af' } } },
      scales: {
        y: { min: 0, max: 1, grid: { color: '#374151' }, ticks: { color: '#9ca3af' } },
        x: { grid: { display: false }, ticks: { color: '#9ca3af' } }
      }
    }
  });
}

fnChartSel.addEventListener('change', (e) => updatePerFuncChart(e.target.value));
if (fnNames.length > 0) updatePerFuncChart(fnNames[0]);

// ── Export Functions ──────────────────────────────────────────────────────────

function toCSVRow(s) {
  const rm = s.readability_metrics || {};
  const gnr = rm.generic_naming_ratio?.raw?.ratio ?? '';
  const typeScore = rm.type_specificity?.normalized ?? '';
  const exprScore = rm.expression_complexity?.normalized ?? '';
  const cfScore = rm.structured_control_flow?.normalized ?? '';
  const artifactCount = rm.unresolved_artifacts?.raw?.total ?? '';
  const fields = [
    s.function_name, s.compiler_variant, s.decompiler,
    s.correctness_score === null || s.correctness_score === undefined ? '' : Number(s.correctness_score).toFixed(4),
    s.readability_proxy_score === null || s.readability_proxy_score === undefined ? '' : Number(s.readability_proxy_score).toFixed(4),
    s.source_similarity.toFixed(4),
    s.semantic_score === null || s.semantic_score === undefined ? '' : Number(s.semantic_score).toFixed(4),
    gnr, typeScore, exprScore, cfScore, artifactCount,
    s.cases_passed || 0, s.cases_total || 0,
    s.fail_category || '',
    s.output_diagnostics?.status || '',
    (s.output_diagnostics?.issues || []).join(';'),
    s.correctness_rank || s.consensus_rank || '', s.goto_count, s.nesting_depth,
    s.time_ms, s.error || '', s.uses_intrinsics ? 'true' : 'false'
  ];
  return fields.map(f => `"${String(f).replace(/"/g, '""')}"`).join(',');
}

const CSV_HEADER = '"function","variant","decompiler","correctness_score","readability_proxy_score","similarity","semantic","gnr","type_specificity","expression_complexity","structured_control_flow","unresolved_artifacts","cases_passed","cases_total","fail_category","output_status","output_issues","correctness_rank","gotos","depth","time_ms","error","uses_intrinsics"';

function exportCSV() {
  const rows = [CSV_HEADER, ...currentFiltered.map(toCSVRow)].join('\n');
  downloadBlob(rows, 'benchmark_results.csv', 'text/csv');
}
function exportJSON() {
  const data = JSON.stringify(currentFiltered, null, 2);
  downloadBlob(data, 'benchmark_results.json', 'application/json');
}
function copyCSV() {
  const rows = [CSV_HEADER, ...currentFiltered.map(toCSVRow)].join('\n');
  copyToClipboard(rows, 'copyCsvBtn');
}
function copyJSON() {
  const data = JSON.stringify(currentFiltered, null, 2);
  copyToClipboard(data, 'copyJsonBtn');
}
function downloadBlob(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}
function copyToClipboard(text, btnId) {
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    const orig = btn.textContent;
    btn.textContent = '✅ Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 2000);
  });
}

// ── Code Viewer Modal ─────────────────────────────────────────────────────────

function syntaxHighlight(code) {
  const token = /\/\*[\s\S]*?\*\/|\/\/[^\n]*|"([^"\\]|\\.)*"|\b(?:int|void|char|float|double|long|short|unsigned|signed|return|if|else|while|for|do|switch|case|break|continue|goto|struct|typedef|static|const|extern|sizeof|NULL|true|false|uint8_t|uint16_t|uint32_t|uint64_t|int8_t|int16_t|int32_t|int64_t)\b|\b(?:dword|qword|byte|word|undefined[0-9]?|ulong|ulonglong|longlong|uchar|ushort|uint)\b|\b(?:0x[0-9a-fA-F]+|\d+)\b/g;
  const keyword = /^(?:int|void|char|float|double|long|short|unsigned|signed|return|if|else|while|for|do|switch|case|break|continue|goto|struct|typedef|static|const|extern|sizeof|NULL|true|false|uint8_t|uint16_t|uint32_t|uint64_t|int8_t|int16_t|int32_t|int64_t)$/;
  const type = /^(?:dword|qword|byte|word|undefined[0-9]?|ulong|ulonglong|longlong|uchar|ushort|uint)$/;
  const number = /^(?:0x[0-9a-fA-F]+|\d+)$/;
  let html = '';
  let last = 0;
  for (const match of code.matchAll(token)) {
    const value = match[0];
    html += escapeHtml(code.slice(last, match.index));
    const escaped = escapeHtml(value);
    if (value.startsWith('//') || value.startsWith('/*')) {
      html += `<span class="code-comment">${escaped}</span>`;
    } else if (value.startsWith('"')) {
      html += `<span class="code-string">${escaped}</span>`;
    } else if (keyword.test(value)) {
      html += `<span class="code-keyword">${escaped}</span>`;
    } else if (type.test(value)) {
      html += `<span class="code-type">${escaped}</span>`;
    } else if (number.test(value)) {
      html += `<span class="code-number">${escaped}</span>`;
    } else {
      html += escaped;
    }
    last = match.index + value.length;
  }
  html += escapeHtml(code.slice(last));
  return html;
}

let currentCodeData = null;

function showCode(evt, code, decompiler, funcName, variant) {
  evt.stopPropagation();
  currentCodeData = { code, decompiler, funcName, variant };
  document.getElementById('codeModalTitle').textContent = `${decompiler} — ${funcName} [${variant}]`;
  const pre = document.getElementById('codeModalPre');
  if (code && code.trim()) {
    pre.innerHTML = syntaxHighlight(code);
  } else {
    pre.innerHTML = '<span style="color:#6b7280;font-style:italic;">No decompiled output available.</span>';
  }
  document.getElementById('codeModal').classList.add('open');
}

function closeCodeModal() {
  document.getElementById('codeModal').classList.remove('open');
}

function copyCodeToClipboard() {
  if (!currentCodeData) return;
  copyToClipboard(currentCodeData.code, 'copyCodeBtn');
}

function downloadCode() {
  if (!currentCodeData) return;
  const { code, decompiler, funcName, variant } = currentCodeData;
  const safe = variant.replace(/[^a-zA-Z0-9_-]/g, '_');
  downloadBlob(code || '', `${decompiler}_${funcName}_${safe}.c`, 'text/plain');
}

// Table Pagination, Search and Sort Logic
let currentFiltered = [...SCORES];
let currentPage = 1;
const rowsPerPage = 25;
let currentSort = { key: 'function_name', asc: true };

function getSimilarityClass(val, hasError) {
  if (hasError) return 'poor';
  if (val === null || val === undefined) return 'poor';
  if (val >= 0.8) return 'excellent';
  if (val >= 0.5) return 'good';
  if (val >= 0.2) return 'weak';
  return 'poor';
}

function getRankBadge(rank) {
  if (rank === 1) return '<span class="rank-badge rank-gold">#1</span>';
  if (rank === 2) return '<span class="rank-badge rank-silver">#2</span>';
  if (rank === 3) return '<span class="rank-badge rank-bronze">#3</span>';
  if (rank) return `<span class="rank-badge rank-other">#${rank}</span>`;
  return '<span class="rank-badge rank-other">—</span>';
}

function readabilityProxyHtml(s) {
  const rm = s.readability_metrics || {};
  if (!rm || Object.keys(rm).length === 0) return '<span style="color:#6b7280">—</span>';
  const gnr = rm.generic_naming_ratio?.raw?.ratio;
  const typeScore = rm.type_specificity?.normalized;
  const exprScore = rm.expression_complexity?.normalized;
  const cfScore = rm.structured_control_flow?.normalized;
  const artifacts = rm.unresolved_artifacts?.raw?.total;
  const parse = rm.parse_ok === false ? ' parse-fail' : '';
  return `<span style="font-size:0.75rem;line-height:1.35;display:inline-block;color:#d1d5db;">`
    + `${gnr === undefined ? '' : `GNR ${Number(gnr).toFixed(2)}<br>`}`
    + `${typeScore === undefined ? '' : `type ${Number(typeScore).toFixed(2)}<br>`}`
    + `${exprScore === undefined ? '' : `expr ${Number(exprScore).toFixed(2)}<br>`}`
    + `${cfScore === undefined ? '' : `cf ${Number(cfScore).toFixed(2)}<br>`}`
    + `${artifacts === undefined ? '' : `art ${artifacts}`}`
    + `<span style="color:#9ca3af">${parse}</span></span>`;
}

function outputDiagnosticsHtml(s) {
  const diag = s.output_diagnostics || {};
  if (!hasOutput(s)) return '<span class="badge neutral">No output</span>';
  const status = diag.status || 'unknown';
  const labels = {
    direct_function: 'Direct',
    needs_normalization: 'Normalize',
    boundary_mismatch: 'Boundary',
    whole_program_output: 'Whole program',
    no_output: 'No output',
    unknown: 'Unknown'
  };
  const klass = status === 'direct_function'
    ? 'success'
    : (status === 'needs_normalization' ? 'warning' : 'error');
  const title = [
    ...(diag.issues || []),
    ...(diag.harness_blockers || [])
  ].join(', ') || status;
  return `<span class="badge ${klass}" title="${escapeHtml(title)}">${labels[status] || status}</span>`;
}

function semanticHtml(s) {
  if (s.error) {
    return `<button type="button" class="badge error badge-button semantic-detail-btn" data-row-id="${s._rowId}">Adapter error</button>`;
  }
  if (!hasSemanticCases(s)) {
    const label = s.fail_category === 'no_wrapper' ? 'No wrapper' : 'No test';
    return `<span class="badge neutral">${label}</span>`;
  }
  const semPct = `${(s.semantic_score * 100).toFixed(0)}% (${s.cases_passed}/${s.cases_total})`;
  const intrinFlag = s.uses_intrinsics ? ' ⚠️' : '';
  if (semanticPasses(s)) {
    return `<span class="badge success">${semPct}${intrinFlag}</span>`;
  }
  const failCatLabels = {'compile_error':'Compile','runtime_error':'Runtime','timeout':'Timeout','assertion_fail':'Assert','no_wrapper':'No wrapper','adapter_error':'Adapter','':'Fail'};
  const failCat = s.fail_category || '';
  const label = failCatLabels[failCat] || 'Fail';
  return `<button type="button" class="badge error badge-button semantic-detail-btn" data-row-id="${s._rowId}" title="${escapeHtml(failCat)}">${label}: ${semPct}${intrinFlag}</button>`;
}

function renderTable() {
  const tbody = document.querySelector('#resultsTable tbody');
  tbody.innerHTML = '';
  
  // Sort scores
  const k = currentSort.key;
  const isAsc = currentSort.asc ? 1 : -1;
  currentFiltered.sort((a, b) => {
    let valA = a[k];
    let valB = b[k];
    if (valA === null || valA === undefined) valA = '';
    if (valB === null || valB === undefined) valB = '';
    
    if (typeof valA === 'string') {
      return valA.localeCompare(valB) * isAsc;
    }
    return (valA < valB ? -1 : valA > valB ? 1 : 0) * isAsc;
  });
  
  const totalRows = currentFiltered.length;
  const totalPages = Math.ceil(totalRows / rowsPerPage) || 1;
  if (currentPage > totalPages) currentPage = totalPages;
  
  const startIdx = (currentPage - 1) * rowsPerPage;
  const endIdx = Math.min(startIdx + rowsPerPage, totalRows);
  const pageRows = currentFiltered.slice(startIdx, endIdx);
  
  pageRows.forEach(s => {
    const tr = document.createElement('tr');
    if (s.decompiler === 'fission') {
      tr.className = 'highlighted-row';
    }
    
    const rankLabel = getRankBadge(s.correctness_rank || s.consensus_rank);
    const hasCode = hasOutput(s);
    const correctnessScore = hasCode ? s.correctness_score : null;
    const simClass = getSimilarityClass(correctnessScore, s.error);
    const statusClass = s.error ? 'error' : (hasCode ? 'success' : 'warning');
    const statusText = s.error ? 'Error' : (hasCode ? 'Output' : 'No output');
    const scoreHtml = hasCode && correctnessScore !== null && correctnessScore !== undefined
      ? `<div class="sim-cell">
          <span class="sim-badge ${simClass}">${correctnessScore.toFixed(3)}</span>
          <div class="sim-bar-bg">
            <div class="sim-bar-fill ${simClass}" style="width: ${correctnessScore * 100}%"></div>
          </div>
        </div>
        <small style="color:#9ca3af;font-size:0.75em;">sim:${s.source_similarity.toFixed(3)}</small>`
      : `<span class="badge neutral">N/A</span>`;

    tr.innerHTML = `
      <td><strong>${escapeHtml(s.function_name)}</strong></td>
      <td>${escapeHtml(s.compiler_variant)}</td>
      <td>
        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background-color:${DECOMPILER_COLORS[s.decompiler] || '#888'}; margin-right:6px;"></span>
        ${escapeHtml(s.decompiler)}
      </td>
      <td>${scoreHtml}</td>
      <td>${semanticHtml(s)}</td>
      <td>${readabilityProxyHtml(s)}</td>
      <td>${rankLabel}</td>
      <td>${s.goto_count}</td>
      <td>${s.time_ms}ms</td>
      <td>${outputDiagnosticsHtml(s)}<br><span class="badge ${statusClass}" style="margin-top:4px;">${statusText}</span></td>
      <td>
        ${hasCode ? `<button type="button" class="code-btn" data-row-id="${s._rowId}">🔬 View</button>` : '<span style="color:#6b7280">—</span>'}
        ${s.has_parity_diff ? `<button type="button" class="parity-btn" data-row-id="${s._rowId}" style="margin-left: 6px;">🔍 Parity Diff</button>` : ''}
      </td>
    `;
    tbody.appendChild(tr);
  });
  
  document.getElementById('pageInfo').textContent = `Showing ${totalRows ? startIdx + 1 : 0} - ${endIdx} of ${totalRows} results`;
  document.getElementById('prevBtn').disabled = currentPage === 1;
  document.getElementById('nextBtn').disabled = currentPage === totalPages;
}

document.querySelector('#resultsTable tbody').addEventListener('click', event => {
  const codeBtn = event.target.closest('.code-btn');
  if (codeBtn) {
    const row = SCORES[Number(codeBtn.dataset.rowId)];
    if (row) showCode(event, row.decompiled_code || '', row.decompiler, row.function_name, row.compiler_variant);
    return;
  }

  const parityBtn = event.target.closest('.parity-btn');
  if (parityBtn) {
    const row = SCORES[Number(parityBtn.dataset.rowId)];
    if (row) showParityDiff(row);
    return;
  }

  const semanticBtn = event.target.closest('.semantic-detail-btn');
  if (semanticBtn) {
    const row = SCORES[Number(semanticBtn.dataset.rowId)];
    if (!row) return;
    const detail = row.error || row.semantic_error || 'No error details recorded.';
    openModal(row.decompiler, row.function_name, row.compiler_variant, detail);
  }
});

function filterScores() {
  const query = document.getElementById('searchInput').value.toLowerCase();
  const decomp = document.getElementById('decompilerFilter').value;
  const variant = document.getElementById('variantFilter').value;
  const gapType = document.getElementById('gapFilter').value;
  
  currentFiltered = SCORES.filter(s => {
    const matchesQuery = s.function_name.toLowerCase().includes(query) || 
                       s.compiler_variant.toLowerCase().includes(query) ||
                       s.decompiler.toLowerCase().includes(query);
    const matchesDecomp = decomp === 'all' || s.decompiler === decomp;
    const matchesVariant = variant === 'all' || s.compiler_variant === variant;
    
    let matchesGap = true;
    if (gapType === 'fission-gap') {
      const key = s.function_name + '|' + s.compiler_variant;
      const group = scoresByGroup[key] || [];
      const fissionScore = group.find(x => x.decompiler === 'fission');
      const eligible = row => row.correctness_score !== null && row.correctness_score !== undefined;
      const othersOk = group.some(x => x.decompiler !== 'fission' && eligible(x) && x.correctness_score >= 0.3);
      matchesGap = fissionScore && eligible(fissionScore) && fissionScore.correctness_score < 0.3 && othersOk;
    } else if (gapType === 'hard') {
      const key = s.function_name + '|' + s.compiler_variant;
      const group = scoresByGroup[key] || [];
      const eligible = group.filter(x => x.correctness_score !== null && x.correctness_score !== undefined);
      matchesGap = eligible.length > 0 && eligible.every(x => x.correctness_score < 0.3);
    } else if (gapType === 'gotos') {
      matchesGap = s.decompiler === 'fission' && s.goto_count > 0;
    }
    
    return matchesQuery && matchesDecomp && matchesVariant && matchesGap;
  });
  
  currentPage = 1;
  renderTable();
}

// Event Listeners for Filters
document.getElementById('searchInput').addEventListener('input', filterScores);
document.getElementById('decompilerFilter').addEventListener('change', filterScores);
document.getElementById('variantFilter').addEventListener('change', filterScores);
document.getElementById('gapFilter').addEventListener('change', filterScores);

// Pagination Buttons
document.getElementById('prevBtn').addEventListener('click', () => {
  if (currentPage > 1) {
    currentPage--;
    renderTable();
  }
});
document.getElementById('nextBtn').addEventListener('click', () => {
  const totalPages = Math.ceil(currentFiltered.length / rowsPerPage);
  if (currentPage < totalPages) {
    currentPage++;
    renderTable();
  }
});

// Sorting columns
document.querySelectorAll('#resultsTable th').forEach(th => {
  th.addEventListener('click', () => {
    const key = th.dataset.key;
    if (!key) return;
    
    if (currentSort.key === key) {
      currentSort.asc = !currentSort.asc;
    } else {
      currentSort.key = key;
      currentSort.asc = true;
    }
    
    document.querySelectorAll('#resultsTable th').forEach(h => {
      h.classList.remove('sorted-asc', 'sorted-desc');
    });
    
    th.classList.add(currentSort.asc ? 'sorted-asc' : 'sorted-desc');
    renderTable();
  });
});

// Modal logic
function openModal(decompiler, funcName, variant, errorMsg) {
  document.getElementById('modalTitle').textContent = `Verification Error: ${decompiler} - ${funcName} (${variant})`;
  document.getElementById('modalErrorContent').textContent = errorMsg || 'No error details recorded.';
  document.getElementById('errorModal').style.display = 'flex';
}
function closeModal() {
  document.getElementById('errorModal').style.display = 'none';
}
window.addEventListener('click', (e) => {
  const modal = document.getElementById('errorModal');
  if (e.target === modal) closeModal();
  const parityModal = document.getElementById('parityModal');
  if (e.target === parityModal) closeParityModal();
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closeModal(); closeCodeModal(); closeParityModal(); }
});

// Initialize Mermaid.js
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  flowchart: { useMaxWidth: false, htmlLabels: true }
});

async function renderMermaidGraph(containerId, mermaidCode) {
  const container = document.getElementById(containerId);
  const uniqueId = "id_" + containerId + "_" + Math.floor(Math.random() * 1000000);
  try {
    const { svg } = await mermaid.render(uniqueId, mermaidCode);
    container.innerHTML = svg;
  } catch (err) {
    console.error("Mermaid error: ", err);
    container.innerHTML = `<pre style="color: #ef4444; font-family: monospace; font-size: 0.85rem; padding: 10px;">Mermaid Error:\n${escapeHtml(err.message || String(err))}\nCode:\n${escapeHtml(mermaidCode)}</pre>`;
    const badSvg = document.getElementById(uniqueId);
    if (badSvg) badSvg.remove();
  }
}

function formatInstruction(inst) {
  if (typeof inst === 'string') return inst;
  if (!inst) return '';
  const addr = inst.address || inst.addr || '';
  const bytes = inst.bytes || '';
  const mnemonic = inst.mnemonic || inst.op || '';
  const operands = inst.operands || (inst.inputs ? inst.inputs.join(', ') : '');
  let parts = [];
  if (addr) parts.push(addr + ':');
  if (mnemonic) parts.push(mnemonic);
  if (operands) parts.push(operands);
  if (bytes) parts.push('(' + bytes + ')');
  return parts.join(' ');
}

function isSameInstruction(inst1, inst2) {
  if (!inst1 || !inst2) return false;
  const m1 = (inst1.mnemonic || inst1.op || '').toLowerCase().trim();
  const m2 = (inst2.mnemonic || inst2.op || '').toLowerCase().trim();
  const b1 = (inst1.bytes || '').toLowerCase().trim();
  const b2 = (inst2.bytes || '').toLowerCase().trim();
  const ad1 = (inst1.address || inst1.addr || '').toLowerCase().trim();
  const ad2 = (inst2.address || inst2.addr || '').toLowerCase().trim();
  return m1 === m2 && b1 === b2 && ad1 === ad2;
}

function renderDisasmDiff(refContainer, candContainer, refDisasm, candDisasm) {
  const refLines = [];
  const candLines = [];
  const maxLength = Math.max(refDisasm.length, candDisasm.length);
  for (let i = 0; i < maxLength; i++) {
    const refInst = refDisasm[i];
    const candInst = candDisasm[i];
    const refText = refInst ? formatInstruction(refInst) : '';
    const candText = candInst ? formatInstruction(candInst) : '';
    let isMismatch = !refInst || !candInst || !isSameInstruction(refInst, candInst);
    const mismatchStyle = isMismatch ? 'style="background: #450a0a; color: #fca5a5;"' : '';
    refLines.push(`<div ${mismatchStyle} style="padding: 2px 5px; white-space: pre;">${escapeHtml(refText) || '&nbsp;'}</div>`);
    candLines.push(`<div ${mismatchStyle} style="padding: 2px 5px; white-space: pre;">${escapeHtml(candText) || '&nbsp;'}</div>`);
  }
  refContainer.innerHTML = refLines.join('');
  candContainer.innerHTML = candLines.join('');
}

function showParityDiff(row) {
  if (!row.has_parity_diff || !row.parity_diff_path) return;
  fetch(row.parity_diff_path)
    .then(response => {
      if (!response.ok) throw new Error("HTTP error " + response.status);
      return response.json();
    })
    .then(data => {
      document.getElementById('parityModalTitle').textContent = `Parity Diff: ${row.decompiler} vs Ghidra - ${row.function_name} (${row.compiler_variant})`;
      document.getElementById('candCFGTitle').textContent = `Candidate (${row.decompiler})`;
      document.getElementById('candASMTitle').textContent = `Candidate Disassembly (${row.decompiler})`;
      document.getElementById('mismatchInfoText').textContent = `Mismatch Info: ${data.mismatch_info || 'None'}`;
      
      const modal = document.getElementById('parityModal');
      modal.dataset.refCFG = JSON.stringify(data.reference_cfg || {});
      modal.dataset.candCFG = JSON.stringify(data.candidate_cfg || {});
      modal.dataset.refASM = JSON.stringify(data.reference_disasm || []);
      modal.dataset.candASM = JSON.stringify(data.candidate_disasm || []);
      modal.dataset.refMermaid = data.reference_mermaid || '';
      modal.dataset.candMermaid = data.candidate_mermaid || '';
      
      modal.style.display = 'flex';
      switchParityTab('cfg');
    })
    .catch(error => {
      console.error("Error loading parity diff:", error);
      alert("Failed to load parity diff: " + error.message);
    });
}

function switchParityTab(tab) {
  const modal = document.getElementById('parityModal');
  const cfgTab = document.getElementById('parityTabCFG');
  const asmTab = document.getElementById('parityTabASM');
  const cfgBtn = document.getElementById('cfgTabBtn');
  const asmBtn = document.getElementById('asmTabBtn');
  
  if (tab === 'cfg') {
    cfgTab.style.display = 'flex';
    asmTab.style.display = 'none';
    cfgBtn.classList.add('active');
    asmBtn.classList.remove('active');
    renderMermaidGraph('refCFGContainer', modal.dataset.refMermaid || 'graph TD\n    empty["Empty CFG"]');
    renderMermaidGraph('candCFGContainer', modal.dataset.candMermaid || 'graph TD\n    empty["Empty CFG"]');
  } else {
    cfgTab.style.display = 'none';
    asmTab.style.display = 'flex';
    cfgBtn.classList.remove('active');
    asmBtn.classList.add('active');
    const refDisasm = JSON.parse(modal.dataset.refASM || '[]');
    const candDisasm = JSON.parse(modal.dataset.candASM || '[]');
    renderDisasmDiff(
      document.getElementById('refASMContainer'),
      document.getElementById('candASMContainer'),
      refDisasm,
      candDisasm
    );
  }
}

function closeParityModal() {
  document.getElementById('parityModal').style.display = 'none';
}

renderTable();
</script>

<!-- Code Viewer Modal -->
<div id="codeModal" onclick="if(event.target===this)closeCodeModal()">
  <div class="code-modal-inner">
    <div class="code-modal-header">
      <h3 id="codeModalTitle">Decompiled Code</h3>
      <div style="display:flex;gap:0.5rem;align-items:center;">
        <button onclick="copyCodeToClipboard()" class="export-btn copy-btn" id="copyCodeBtn" style="font-size:0.78rem;">📋 Copy</button>
        <button onclick="downloadCode()" class="export-btn" style="font-size:0.78rem;">⬇ .c</button>
        <button onclick="closeCodeModal()" style="background:none;border:none;color:#9ca3af;font-size:1.4rem;cursor:pointer;line-height:1;padding:0 0.25rem;">&times;</button>
      </div>
    </div>
    <div class="code-modal-body">
      <pre id="codeModalPre"></pre>
    </div>
    <div class="code-modal-footer" style="justify-content:space-between;">
      <span style="color:#6b7280;font-size:0.78rem;">💡 Click outside or × to close &nbsp;|&nbsp; Syntax highlighting is approximate</span>
      <span id="codeLineCount" style="color:#6b7280;font-size:0.78rem;"></span>
    </div>
  </div>
</div>

<!-- Modal overlay -->
<div id="errorModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; justify-content: center; align-items: center;">
  <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; width: 80%; max-width: 800px; max-height: 80%; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5);">
    <div style="padding: 1.25rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: #1f2937;">
      <h3 style="font-weight: 600;" id="modalTitle">Verification Error Details</h3>
      <button onclick="closeModal()" style="background: none; border: none; color: var(--muted); font-size: 1.5rem; cursor: pointer; line-height: 1;">&times;</button>
    </div>
    <div style="padding: 1.5rem; overflow-y: auto; flex-grow: 1;">
      <pre style="background: #090d16; border: 1px solid var(--border); padding: 1rem; border-radius: 8px; font-family: monospace; font-size: 0.85rem; color: #ef4444; white-space: pre-wrap;" id="modalErrorContent"></pre>
    </div>
  </div>
</div>

<!-- Parity Diff Modal -->
<div id="parityModal" onclick="if(event.target===this)closeParityModal()" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1100; justify-content: center; align-items: center;">
  <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 12px; width: 95%; max-width: 1400px; height: 90%; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);">
    <div style="padding: 1.25rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: #1f2937;">
      <h3 style="font-weight: 600;" id="parityModalTitle">Visual Parity Diff</h3>
      <div style="display: flex; gap: 10px;">
        <button id="cfgTabBtn" class="tab-btn active" onclick="switchParityTab('cfg')">📊 Control Flow Graph</button>
        <button id="asmTabBtn" class="tab-btn" onclick="switchParityTab('asm')">💻 Assembly Comparison</button>
        <button onclick="closeParityModal()" style="background: none; border: none; color: var(--muted); font-size: 1.5rem; cursor: pointer; line-height: 1; margin-left: 10px;">&times;</button>
      </div>
    </div>
    <div style="padding: 1.5rem; overflow-y: auto; flex-grow: 1; display: flex; flex-direction: column; background: #090d16;">
      
      <!-- CFG Tab -->
      <div id="parityTabCFG" style="display: flex; flex-grow: 1; gap: 20px; height: 100%;">
        <div style="flex: 1; display: flex; flex-direction: column; border: 1px solid var(--border); border-radius: 8px; background: #0b0f17; overflow: hidden;">
          <div style="padding: 8px 12px; background: #1e293b; border-bottom: 1px solid var(--border); font-weight: 600; font-size: 0.85rem;">Reference (Ghidra)</div>
          <div style="flex-grow: 1; overflow: auto; padding: 15px; display: flex; justify-content: center; align-items: flex-start;" id="refCFGContainer"></div>
        </div>
        <div style="flex: 1; display: flex; flex-direction: column; border: 1px solid var(--border); border-radius: 8px; background: #0b0f17; overflow: hidden;">
          <div style="padding: 8px 12px; background: #1e293b; border-bottom: 1px solid var(--border); font-weight: 600; font-size: 0.85rem;" id="candCFGTitle">Candidate</div>
          <div style="flex-grow: 1; overflow: auto; padding: 15px; display: flex; justify-content: center; align-items: flex-start;" id="candCFGContainer"></div>
        </div>
      </div>
      
      <!-- Assembly Tab -->
      <div id="parityTabASM" style="display: none; flex-grow: 1; gap: 20px; height: 100%;">
        <div style="flex: 1; display: flex; flex-direction: column; border: 1px solid var(--border); border-radius: 8px; background: #0b0f17; overflow: hidden;">
          <div style="padding: 8px 12px; background: #1e293b; border-bottom: 1px solid var(--border); font-weight: 600; font-size: 0.85rem;">Reference Disassembly</div>
          <div style="flex-grow: 1; overflow: auto; padding: 10px; font-family: monospace; font-size: 0.85rem; line-height: 1.5;" id="refASMContainer"></div>
        </div>
        <div style="flex: 1; display: flex; flex-direction: column; border: 1px solid var(--border); border-radius: 8px; background: #0b0f17; overflow: hidden;">
          <div style="padding: 8px 12px; background: #1e293b; border-bottom: 1px solid var(--border); font-weight: 600; font-size: 0.85rem;" id="candASMTitle">Candidate Disassembly</div>
          <div style="flex-grow: 1; overflow: auto; padding: 10px; font-family: monospace; font-size: 0.85rem; line-height: 1.5;" id="candASMContainer"></div>
        </div>
      </div>

    </div>
    <div style="padding: 0.75rem 1.25rem; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: #111827; font-size: 0.8rem; color: var(--muted);">
      <div id="mismatchInfoText">Mismatch Info: </div>
      <button onclick="closeParityModal()" class="code-btn">Close</button>
    </div>
  </div>
</div>
</body>
</html>
"""

    # Build validity banner HTML from the verdict
    if legacy or "legacy_flat_list" in verdict.reasons or "legacy_source" in verdict.publish_reasons:
        banner_html = (
            '<div class="validity-banner legacy">'
            '<div style="display:flex;align-items:center;gap:0.5rem;font-size:1.1rem;">'
            '<span>⚠️</span><span>LEGACY / UNVERIFIED</span></div>'
            '<div style="font-size:0.95rem;color:#a1a1aa;">'
            'Provenance incomplete — this result predates the envelope format.<br>'
            'Do not use these numbers as an official comparison.</div></div>'
        )
    elif not verdict.valid:
        reasons_list = "".join(f"<li>{r}</li>" for r in verdict.reasons)
        banner_html = (
            '<div class="validity-banner invalid">'
            '<div style="display:flex;align-items:center;gap:0.5rem;font-size:1.1rem;">'
            '<span>⛔</span><span>INVALID MEASUREMENT</span></div>'
            f'<div style="font-size:0.95rem;color:#a1a1aa;">'
            f'Fission {verdict.fission.clean}/{verdict.fission.attempted} '
            f'({verdict.fission.ratio*100:.1f}%), '
            f'all-backend {verdict.overall.clean}/{verdict.overall.attempted} '
            f'({verdict.overall.ratio*100:.1f}%).<br>'
            'Results below are <strong>not publishable</strong>.</div>'
            f'<ul class="validity-reason-list">{reasons_list}</ul></div>'
        )
    elif not verdict.publishable:
        banner_html = (
            '<div class="validity-banner legacy">'
            '<div style="display:flex;align-items:center;gap:0.5rem;font-size:1.1rem;">'
            '<span>✅</span><span>VALID SMOKE MEASUREMENT</span></div>'
            '<div style="font-size:0.95rem;color:#a1a1aa;">'
            f'Fission {verdict.fission.clean}/{verdict.fission.attempted} '
            f'({verdict.fission.ratio*100:.1f}%), '
            f'all-backend {verdict.overall.clean}/{verdict.overall.attempted} '
            f'({verdict.overall.ratio*100:.1f}%).<br>'
            f'⚪ NOT PUBLISHABLE — {", ".join(verdict.publish_reasons)}</div></div>'
        )
    else:
        banner_html = (
            '<div class="validity-banner valid">'
            '<div style="display:flex;align-items:center;gap:0.5rem;font-size:1.1rem;">'
            '<span>✅</span><span>VALID RUN</span></div>'
            '<div style="font-size:0.95rem;color:#a1a1aa;">'
            f'Fission {verdict.fission.clean}/{verdict.fission.attempted} '
            f'({verdict.fission.ratio*100:.1f}%), '
            f'all-backend {verdict.overall.clean}/{verdict.overall.attempted} '
            f'({verdict.overall.ratio*100:.1f}%)</div></div>'
        )

    html = html_template.replace("__TS__", ts)
    html = html.replace("__CORPUS_SPLIT__", corpus_split)
    html = html.replace("__FUNCTIONS_COUNT__", str(len(fn_names)))
    html = html.replace("__SCORES_JSON__", scores_json)
    html = html.replace("__DECOMPILER_COLORS__", json.dumps(DECOMPILER_COLORS))
    html = html.replace("__RUN_META_JSON__", run_meta_json)
    html = html.replace("__VALIDITY_BANNER__", banner_html)

    return html

def generate_report(
    scores: list[FunctionScore],
    corpus_split: str = "dev",
    *,
    loaded_result: LoadedResult | None = None,
    verdict: RunValidity | None = None,
    measured_at: str | None = None,
    legacy: bool = False,
    results_dir: Path,
    docs_dir: Path,
) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    standard_summary = None
    if loaded_result and loaded_result.envelope:
        standard_summary = loaded_result.envelope.get("summary")

    # Markdown
    md = generate_markdown(
        scores,
        corpus_split,
        verdict=verdict,
        measured_at=measured_at,
        legacy=legacy,
        standard_summary=standard_summary,
    )
    (results_dir / "latest.md").write_text(md, encoding="utf-8")

    # HTML
    html = generate_html(
        scores,
        corpus_split,
        verdict=verdict,
        measured_at=measured_at,
        legacy=legacy,
        results_dir=results_dir,
    )
    (docs_dir / "index.html").write_text(html, encoding="utf-8")
