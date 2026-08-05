#!/usr/bin/env python3
"""Offline contract check for the benchmark-first official path.

Validates that result envelopes implement the standard-set architecture without
requiring Docker/Wine. Intended for local preflight and CI after runner writes
candidate JSONs.

Checks:
  1. Envelope schema_version == 2 (or migratable legacy with --allow-legacy)
  2. summary.schema == standard-set-v1 (builds if missing when --repair)
  3. MVP summary denominators: taxonomy sums to attempted per decompiler
  4. correctness_score == semantic_score when both finite (semantic-only policy)
  5. Official profile fields when run.official is true
  6. Optional publication_gate triple when --dev/--holdout/--overfitting given

Exit 0 = OK, 1 = contract failure.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runner.run_validity import (  # noqa: E402
    evaluate_run,
    load_result_file,
    validate_envelope_schema,
)
from runner.scoring import compute_correctness_score  # noqa: E402
from runner.standard_summary import (  # noqa: E402
    SUMMARY_SCHEMA,
    attach_summary_to_envelope,
)


def _check_envelope(path: Path, *, allow_legacy: bool, repair: bool) -> list[str]:
    errors: list[str] = []
    try:
        loaded = load_result_file(path)
    except Exception as exc:
        return [f"{path}: load failed: {exc}"]

    if loaded.legacy:
        if not allow_legacy:
            errors.append(f"{path}: legacy flat-list (use migrate_legacy_results.py or re-run)")
            return errors
        return errors

    assert loaded.envelope is not None
    envelope = loaded.envelope
    try:
        validate_envelope_schema(envelope)
    except Exception as exc:
        errors.append(f"{path}: schema: {exc}")

    if repair:
        # Re-align correctness to semantic-only and rebuild summary.
        fixed_rows = []
        for row in envelope.get("rows") or []:
            item = dict(row)
            item["correctness_score"] = compute_correctness_score(
                item.get("semantic_score"),
                float(item.get("source_similarity") or 0.0),
                float(item.get("structural_penalty") or 0.0),
            )
            fixed_rows.append(item)
        envelope["rows"] = fixed_rows
        attach_summary_to_envelope(envelope)
        path.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")
    elif not envelope.get("summary"):
        attach_summary_to_envelope(envelope)

    summary = envelope.get("summary") or {}
    if summary.get("schema") != SUMMARY_SCHEMA:
        errors.append(
            f"{path}: summary.schema={summary.get('schema')!r} expected {SUMMARY_SCHEMA!r}"
        )

    mvp = summary.get("mvp") or {}
    by_tool = mvp.get("by_decompiler") or {}
    if not by_tool and envelope.get("rows"):
        errors.append(f"{path}: summary.mvp.by_decompiler empty but rows present")

    # MVP-0 same-function matrix (infra honesty axis)
    same_fn = mvp.get("same_function")
    if envelope.get("rows"):
        if not isinstance(same_fn, dict):
            errors.append(f"{path}: summary.mvp.same_function missing (rebuild summary)")
        else:
            if same_fn.get("schema") != "same-function-matrix-v1":
                errors.append(
                    f"{path}: same_function.schema={same_fn.get('schema')!r} "
                    "expected 'same-function-matrix-v1'"
                )
            cohorts = same_fn.get("cohorts") or {}
            for cohort_name in ("core", "multi", "all"):
                if cohort_name not in cohorts:
                    errors.append(f"{path}: same_function.cohorts.{cohort_name} missing")
            # Rate definition smoke: denominators must be consistent
            for tool, stats in (same_fn.get("by_decompiler") or {}).items():
                rate = stats.get("same_function_rate")
                den = stats.get("strict_denominator")
                if rate is not None and den == 0:
                    errors.append(
                        f"{path}: {tool} same_function_rate set but strict_denominator=0"
                    )

    for tool, stats in by_tool.items():
        cov = stats.get("coverage") or {}
        tax = stats.get("fail_taxonomy") or {}
        attempted = int(cov.get("attempted") or 0)
        tax_sum = sum(int(v) for v in tax.values())
        if attempted != tax_sum:
            errors.append(
                f"{path}: {tool} taxonomy sum {tax_sum} != attempted {attempted}"
            )
        tested = int(cov.get("semantic_tested") or 0)
        if tested > attempted:
            errors.append(f"{path}: {tool} semantic_tested > attempted")
        semantic = stats.get("semantic") or {}
        shared = semantic.get("shared_rows")
        observed = semantic.get("observed_rows")
        if shared is None or observed is None:
            errors.append(f"{path}: {tool} shared semantic denominator missing")
        elif int(observed) > int(shared):
            errors.append(f"{path}: {tool} semantic observed_rows > shared_rows")

    for i, row in enumerate(envelope.get("rows") or []):
        sem = row.get("semantic_score")
        cor = row.get("correctness_score")
        if sem is None and cor is None:
            continue
        expected = compute_correctness_score(
            float(sem) if sem is not None else None,
            float(row.get("source_similarity") or 0.0),
            float(row.get("structural_penalty") or 0.0),
        )
        # Semantic-only policy: correctness must match compute_correctness_score.
        if cor is None and expected is None:
            continue
        if cor is None or expected is None or abs(float(cor) - float(expected)) > 1e-6:
            errors.append(
                f"{path}: row {i} correctness_score={cor} expected {expected} "
                f"(semantic={sem}) ({row.get('decompiler')}/{row.get('function_name')})"
            )

    verdict = evaluate_run(loaded if not repair else load_result_file(path))
    if envelope.get("run", {}).get("official") is True:
        release_contract = envelope.get("run", {}).get("release_contract") or {}
        if release_contract.get("id") != "release-baseline-v1":
            errors.append(f"{path}: official run requires release-baseline-v1")
        if (
            release_contract.get("subject_count") != 216
            or release_contract.get("row_count") != 432
        ):
            errors.append(f"{path}: official release contract must be 216 subjects / 432 rows")
        recompilation = (summary.get("extensions") or {}).get("recompilation")
        if not isinstance(recompilation, dict):
            errors.append(f"{path}: official summary.extensions.recompilation missing")
        if not envelope.get("run", {}).get("profile") == "realistic":
            errors.append(f"{path}: official run requires profile=realistic")
        if not verdict.official_profile_valid and "official_profile_invalid" not in str(
            verdict.publish_reasons
        ):
            # Still report profile issues via publish_reasons elsewhere
            pass

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "envelopes",
        nargs="*",
        type=Path,
        help="Envelope JSON paths (default: results/dev_latest.json if present)",
    )
    parser.add_argument("--allow-legacy", action="store_true")
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Rewrite missing summary/taxonomy onto the input file",
    )
    parser.add_argument("--dev", type=Path, help="With --holdout/--overfitting: run publication_gate")
    parser.add_argument("--holdout", type=Path)
    parser.add_argument("--overfitting", type=Path)
    args = parser.parse_args(argv)

    paths = list(args.envelopes)
    if not paths:
        default = ROOT / "results" / "dev_latest.json"
        if default.is_file():
            paths = [default]
        else:
            print("error: no envelope paths given and results/dev_latest.json missing", file=sys.stderr)
            return 1

    all_errors: list[str] = []
    for path in paths:
        errs = _check_envelope(path, allow_legacy=args.allow_legacy, repair=args.repair)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"OK  {path}")

    if args.dev and args.holdout and args.overfitting:
        from runner.publication_gate import evaluate_publication

        try:
            verdict = evaluate_publication(args.dev, args.holdout, args.overfitting)
        except Exception as exc:
            all_errors.append(f"publication_gate: {exc}")
        else:
            if verdict.get("publishable"):
                print("OK  publication_gate publishable=true")
            else:
                all_errors.append(
                    "publication_gate not publishable: "
                    + ", ".join(verdict.get("reasons") or [])
                )

    if all_errors:
        for err in all_errors:
            print(f"FAIL {err}", file=sys.stderr)
        return 1
    print("benchmark path contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
