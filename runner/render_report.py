"""Render benchmark report artifacts from a saved JSON result file.

This script is NON-DESTRUCTIVE by default: it never modifies the input file.
Use --write-normalized to write a normalised copy, or --update-latest to copy
the normalised result to results/latest.json.

Measured-at timestamp
---------------------
If the input is in envelope format (schema_version >= 2), the ``run.finished_at``
field is extracted and shown in the report header as "Measured at".
For legacy flat-list files the timestamp is shown as "unknown (legacy)".
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict
from dataclasses import fields
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from report import generate_report
from output_diagnostics import analyze_output_diagnostics, invalid_output_reason
from readability import (
    analyze_readability,
    compare_readability_layers,
    summarize_readability_proxy_score,
)
from semantic import verify_semantic_correctness
from test_wrappers import TEST_WRAPPERS
from scoring import FunctionScore, assign_consensus_ranks, check_uses_intrinsics, compute_correctness_score
from run_validity import load_result_file, build_envelope, evaluate_run, LoadedResult, validity_dict
from standard_summary import attach_summary_to_envelope
from artifact_integrity import write_artifact_manifest, verify_artifact_manifest


def _normalise_scores(data: list[dict], recompute_derived: bool = False, rerun_semantic: bool = False) -> list[FunctionScore]:
    """Convert raw row dicts to FunctionScore objects with optional re-scoring."""
    
    # 1. Pre-process dicts for migration before instantiating FunctionScore
    migrated_data = []
    for row in data:
        migrated = dict(row)
        stored_correctness = migrated.get("correctness_score")
        # Detect corrupted 0.0: a row that has non-zero semantic or similarity but
        # stores correctness_score=0.0 is a legacy corruption from the P0.6.1 bug.
        corrupted_zero = (
            stored_correctness == 0.0
            and (migrated.get("semantic_score", 0.0) > 0 or migrated.get("source_similarity", 0.0) > 0)
            and migrated.get("error") is None
        )
        if "correctness_score" not in migrated or corrupted_zero:
            if "composite_score" in migrated and not corrupted_zero:
                migrated["correctness_score"] = migrated["composite_score"]
            else:
                migrated["correctness_score"] = compute_correctness_score(
                    migrated.get("semantic_score", 0.0),
                    migrated.get("source_similarity", 0.0),
                    migrated.get("structural_penalty", 0.0),
                )
        if "correctness_rank" not in migrated and "consensus_rank" in migrated:
            migrated["correctness_rank"] = migrated["consensus_rank"]
        migrated_data.append(migrated)

    score_fields = {field.name for field in fields(FunctionScore)}
    scores = [
        FunctionScore(**{k: v for k, v in row.items() if k in score_fields})
        for row in migrated_data
    ]
            
    if not (recompute_derived or rerun_semantic):
        return scores

    code_counts = Counter(
        score.decompiled_code.strip()
        for score in scores
        if score.decompiled_code.strip()
    )
    for score in scores:
        if recompute_derived:
            if score.decompiled_code_nir and not score.readability_metrics_nir:
                score.readability_metrics_nir = analyze_readability(
                    score.decompiled_code_nir, score.decompiler
                )
            if score.readability_metrics_nir and score.readability_proxy_score_nir is None:
                score.readability_proxy_score_nir = summarize_readability_proxy_score(
                    score.readability_metrics_nir
                )
            if score.decompiled_code_hir and not score.readability_metrics_hir:
                score.readability_metrics_hir = analyze_readability(
                    score.decompiled_code_hir, score.decompiler
                )
            if score.readability_metrics_hir and score.readability_proxy_score_hir is None:
                score.readability_proxy_score_hir = summarize_readability_proxy_score(
                    score.readability_metrics_hir
                )
            if (
                score.decompiled_code_nir
                and score.decompiled_code_hir
                and not score.dual_layer_delta
            ):
                score.dual_layer_delta = compare_readability_layers(
                    score.decompiled_code_nir,
                    score.decompiled_code_hir,
                    score.readability_metrics_nir,
                    score.readability_metrics_hir,
                )
            if score.readability_metrics and score.readability_proxy_score is None:
                score.readability_proxy_score = summarize_readability_proxy_score(
                    score.readability_metrics
                )
            if score.decompiled_code and not score.output_diagnostics:
                score.output_diagnostics = analyze_output_diagnostics(
                    score.function_name,
                    score.decompiler,
                    score.decompiled_code,
                )
            if score.decompiled_code and not score.error:
                reason = invalid_output_reason(
                    score.output_diagnostics,
                    score.decompiled_code,
                    duplicate_count=code_counts.get(score.decompiled_code.strip(), 0),
                )
                if reason:
                    score.error = reason
                    score.semantic_error = reason
                    score.fail_category = "adapter_error"
                    score.readability_metrics = {}
                    score.readability_proxy_score = None
                    score.ast_similarity = {}
            if score.decompiled_code and not score.uses_intrinsics:
                score.uses_intrinsics = check_uses_intrinsics(score.decompiled_code)

        if score.error:
            score.semantic_error = score.semantic_error or score.error
            score.fail_category = score.fail_category or "adapter_error"
            score.source_similarity = 0.0
            score.goto_count = 0
            score.nesting_depth = 0
            score.semantic_score = 0.0
            score.cases_passed = 0
            score.cases_total = 0
            score.correctness_score = 0.0
            score.composite_score = 0.0
            score.correctness_rank = None
            score.consensus_rank = None
            
        if rerun_semantic:
            if score.fail_category == "no_wrapper" and score.function_name in TEST_WRAPPERS:
                (
                    score.semantic_score,
                    score.semantic_error,
                    score.fail_category,
                    score.cases_passed,
                    score.cases_total,
                ) = verify_semantic_correctness(score.function_name, score.decompiled_code)

    if recompute_derived:
        metrics_path = Path(__file__).parent.parent / "corpus" / "source_metrics.json"
        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            return assign_consensus_ranks(
                scores,
                source_goto_counts=metrics.get("goto_counts", {}),
                source_nesting_depths=metrics.get("nesting_depths", {}),
            )
        return assign_consensus_ranks(scores)
        
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render benchmark dashboard from saved results (NON-DESTRUCTIVE by default)"
    )
    parser.add_argument("--input", required=True, type=Path, help="Input JSON results file")
    parser.add_argument("--corpus", required=True, help="Corpus label to show in the report")
    parser.add_argument(
        "--update-latest",
        action="store_true",
        help="Copy the normalised JSON to results/latest.json and regenerate latest.md / docs/index.html",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Isolated output root containing results/ and docs/ (required unless --update-latest)",
    )
    parser.add_argument(
        "--publication-verdict",
        type=Path,
        help="Final evidence verdict required when promoting --update-latest",
    )
    parser.add_argument(
        "--write-normalized",
        type=Path,
        default=None,
        help="Write the normalised (re-scored) rows to this path without touching --input",
    )
    parser.add_argument("--recompute-derived", action="store_true", help="Recompute derived metrics (readability, output diagnostics, ranks)")
    parser.add_argument("--rerun-semantic", action="store_true", help="Explicitly re-run semantic verification where applicable")
    parser.add_argument(
        "--update-summary",
        action="store_true",
        help="Write a compact results/latest-summary.json for the Next.js dashboard (no decompiled code, <100KB).",
    )
    args = parser.parse_args()

    if args.update_latest and args.output_dir:
        parser.error("--output-dir and --update-latest are mutually exclusive")
    if not args.update_latest and args.output_dir is None:
        parser.error("--output-dir is required unless --update-latest is used")
    if args.update_latest and args.publication_verdict is None:
        parser.error("--publication-verdict is required with --update-latest")
    output_root = Path(__file__).parent.parent if args.update_latest else args.output_dir.resolve()
    results_dir = output_root / "results"
    docs_dir = output_root / "docs"
    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    # ── Load without modifying the input file ─────────────────────────────────
    loaded = load_result_file(args.input)
    source_envelope_sha256 = hashlib.sha256(args.input.read_bytes()).hexdigest()
    publication_verdict = None
    if args.publication_verdict:
        publication_verdict = json.loads(args.publication_verdict.read_text(encoding="utf-8"))
        if publication_verdict.get("publishable") is not True:
            parser.error("publication verdict is not publishable")
        if publication_verdict.get("dev", {}).get("envelope_sha256") != source_envelope_sha256:
            parser.error("publication verdict does not link to --input")
    rows = loaded.rows
    is_legacy = loaded.legacy
    envelope = loaded.envelope

    # Extract provenance from envelope when available
    measured_at: str | None = None
    if not is_legacy and envelope:
        run_meta = envelope.get("run", {})
        measured_at = run_meta.get("finished_at") or run_meta.get("started_at")

    if is_legacy:
        measured_at_label = "unknown (legacy)"
    else:
        measured_at_label = measured_at or "not recorded"

    # ── Normalise / re-score ───────────────────────────────────────────────────
    scores = _normalise_scores(rows, recompute_derived=args.recompute_derived, rerun_semantic=args.rerun_semantic)

    serialized_rows = [asdict(score) for score in scores]
    if not is_legacy and envelope:
        out_envelope = copy.deepcopy(envelope)
        out_envelope["rows"] = serialized_rows
        if not out_envelope.get("run", {}).get("run_id"):
            run_meta = out_envelope.setdefault("run", {})
            run_meta["run_id"] = f"unprovenanced-{source_envelope_sha256[:12]}"
            run_meta["official"] = False
            run_meta["provenance_repair"] = "missing_run_id"
        if args.recompute_derived or args.rerun_semantic:
            run_meta = out_envelope.get("run", {})
            parent_run_id = run_meta.get("run_id", "original-unknown")
            derivations = []
            if args.recompute_derived:
                derivations.append("derived-recompute")
            if args.rerun_semantic:
                derivations.append("semantic-recompute")
            run_meta["parent_run_id"] = parent_run_id
            run_meta["run_id"] = f"derived-{parent_run_id}"
            run_meta["derivation"] = ",".join(derivations)
            run_meta["official"] = False
            out_envelope["run"] = run_meta
    else:
        out_envelope = build_envelope(
            serialized_rows,
            run_meta={
                "run_id": f"legacy-{source_envelope_sha256[:12]}",
                "official": False,
                "legacy_source": True,
                "corpus": args.corpus,
            },
        )

    # Always rebuild standard-set summary from the (possibly re-scored) rows so
    # MD/dashboard denominators match the envelope contract.
    attach_summary_to_envelope(out_envelope)
    serialized_rows = out_envelope["rows"]

    loaded = LoadedResult(rows=serialized_rows, envelope=out_envelope, legacy=False)
    verdict = evaluate_run(loaded)
    final_validity = validity_dict(verdict)
    if publication_verdict is not None:
        final_validity["publishable"] = True
        final_validity["holdout_valid"] = True
        final_validity["publish_reasons"] = []
        verdict = replace(
            verdict,
            publishable=True,
            holdout_valid=True,
            publish_reasons=(),
        )
    out_envelope["validity"] = final_validity
    artifact = {
        "run_id": out_envelope.get("run", {}).get("run_id"),
        "source_envelope_sha256": source_envelope_sha256,
        "generated_from": str(args.input),
    }
    out_envelope["artifact"] = artifact
    if publication_verdict is not None:
        out_envelope["publication"] = publication_verdict
    serialized = json.dumps(out_envelope, indent=2) + "\n"

    if args.write_normalized:
        args.write_normalized.parent.mkdir(parents=True, exist_ok=True)
        args.write_normalized.write_text(serialized, encoding="utf-8")
        print(f"Normalised rows written to {args.write_normalized}")

    (results_dir / "latest.json").write_text(serialized, encoding="utf-8")
    generate_report(
        scores,
        corpus_split=args.corpus,
        measured_at=measured_at_label,
        legacy=is_legacy,
        loaded_result=loaded,
        verdict=verdict,
        results_dir=results_dir,
        docs_dir=docs_dir,
    )

    marker = f"run_id={artifact['run_id']} source_envelope_sha256={source_envelope_sha256}"
    md_path = results_dir / "latest.md"
    md_path.write_text(f"<!-- {marker} -->\n" + md_path.read_text(encoding="utf-8"), encoding="utf-8")
    html_path = docs_dir / "index.html"
    html_path.write_text(f"<!-- {marker} -->\n" + html_path.read_text(encoding="utf-8"), encoding="utf-8")

    # A compact dashboard envelope is always emitted so all publication files
    # share one run and source linkage contract.
    strip_fields = {
        "decompiled_code", "decompiled_code_nir", "decompiled_code_hir",
        "readability_metrics", "readability_metrics_hir",
        "ast_similarity", "output_diagnostics", "semantic_error",
    }
    summary_rows = [
        {key: value for key, value in row.items() if key not in strip_fields}
        for row in serialized_rows
    ]

    from collections import defaultdict
    agg: dict = defaultdict(lambda: {
        "attempted": 0, "clean": 0, "error": 0,
        "correctness_sum": 0.0, "correctness_tested": 0,
        "similarity_sum": 0.0, "semantic_pass": 0, "semantic_tested": 0,
    })
    for row in summary_rows:
        stats = agg[row.get("decompiler", "unknown")]
        stats["attempted"] += 1
        if row.get("error"):
            stats["error"] += 1
            continue
        stats["clean"] += 1
        if row.get("correctness_score") is not None:
            stats["correctness_sum"] += row["correctness_score"]
            stats["correctness_tested"] += 1
        stats["similarity_sum"] += row.get("source_similarity") or 0.0
        if row.get("semantic_score") is not None:
            stats["semantic_tested"] += 1
            if row["semantic_score"] >= 1.0:
                stats["semantic_pass"] += 1

    agg_list = []
    for decompiler, stats in agg.items():
        tested = stats["semantic_tested"]
        clean = stats["clean"]
        correctness_tested = stats["correctness_tested"]
        agg_list.append({
            "decompiler": decompiler,
            "attempted": stats["attempted"],
            "clean": clean,
            "error": stats["error"],
            "avg_correctness": round(stats["correctness_sum"] / correctness_tested, 4) if correctness_tested else None,
            "avg_similarity": round(stats["similarity_sum"] / clean, 4) if clean else 0.0,
            "semantic_coverage_pct": round(tested / clean * 100, 2) if clean else 0.0,
            "semantic_pass_pct": round(stats["semantic_pass"] / tested * 100, 2) if tested else None,
        })

    summary_envelope = {
        "schema_version": 2,
        "run": loaded.envelope.get("run", {}),
        "validity": loaded.envelope.get("validity", {}),
        "matrix": {key: value for key, value in (loaded.envelope.get("matrix") or {}).items() if key != "expected_cells"},
        "artifact": artifact,
        "summary": agg_list,
        "rows": summary_rows,
    }
    summary_path = results_dir / "latest-summary.json"
    summary_path.write_text(json.dumps(summary_envelope, indent=2), encoding="utf-8")
    print(f"results/latest-summary.json updated ({len(summary_rows)} rows, {summary_path.stat().st_size // 1024}KB)")

    write_artifact_manifest(
        output_root,
        run_id=artifact["run_id"],
        source_envelope_sha256=source_envelope_sha256,
        generated_from=str(args.input),
    )
    verify_artifact_manifest(output_root)

    print(
        f"Rendered {len(scores)} rows from {args.input} as corpus {args.corpus!r} "
        f"(measured_at={measured_at_label!r}, legacy={is_legacy})"
    )


if __name__ == "__main__":
    main()
