#!/usr/bin/env python3
"""Before/after diff for two runner.py result envelopes.

Matches rows across two ``runner.py --output ...`` JSON files by
``(decompiler, function_name, compiler_variant)`` and reports:

  - aggregate metric deltas (type_match, ged, semantic, source_similarity)
    per decompiler
  - fail_category distribution shift
  - per-row transitions (rows whose fail_category changed), sorted with
    regressions (better -> worse) first

This is a **local dev-loop diagnostic**, not the official ranking oracle —
do not promote its output to results/latest.json or GitHub Pages.

Usage:
  python scripts/compare_runs.py --before before.json --after after.json
  python scripts/compare_runs.py --before before.json --after after.json --decompiler fission
  python scripts/compare_runs.py --before before.json --after after.json --show-transitions 20
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean

# Rows with a fail_category in this set count as "ok" (no differential
# failure) for the purpose of ranking transitions best -> worst.
OK_CATEGORIES = {None, "", "ok"}

METRICS = ("type_match_score", "ged_score", "semantic_score", "source_similarity")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _row_key(row: dict) -> tuple[str, str, str]:
    return (
        row.get("decompiler", ""),
        row.get("function_name", ""),
        row.get("compiler_variant", ""),
    )


def _index_rows(envelope: dict, decompiler: str | None) -> dict[tuple[str, str, str], dict]:
    rows = envelope.get("rows", [])
    if decompiler:
        rows = [r for r in rows if r.get("decompiler") == decompiler]
    return {_row_key(r): r for r in rows}


def _mean_metric(rows: list[dict], metric: str) -> tuple[float | None, int]:
    vals = [r[metric] for r in rows if r.get(metric) is not None]
    if not vals:
        return None, 0
    return mean(vals), len(vals)


def _fail_category_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        cat = r.get("fail_category") or "ok"
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _fmt_delta(before: float | None, after: float | None) -> str:
    if before is None or after is None:
        return "n/a"
    delta = after - before
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.4f}"


def _fmt_val(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.4f}"


def print_aggregate_diff(
    before_by_decompiler: dict[str, list[dict]],
    after_by_decompiler: dict[str, list[dict]],
) -> None:
    decompilers = sorted(set(before_by_decompiler) | set(after_by_decompiler))
    for dec in decompilers:
        b_rows = before_by_decompiler.get(dec, [])
        a_rows = after_by_decompiler.get(dec, [])
        print(f"\n=== {dec} ===")
        print(f"  rows: before={len(b_rows)} after={len(a_rows)}")
        print(f"  {'metric':<20}{'before':<12}{'after':<12}{'delta':<12}{'n (b/a)':<12}")
        for metric in METRICS:
            b_val, b_n = _mean_metric(b_rows, metric)
            a_val, a_n = _mean_metric(a_rows, metric)
            print(
                f"  {metric:<20}{_fmt_val(b_val):<12}{_fmt_val(a_val):<12}"
                f"{_fmt_delta(b_val, a_val):<12}{f'{b_n}/{a_n}':<12}"
            )

        b_cats = _fail_category_counts(b_rows)
        a_cats = _fail_category_counts(a_rows)
        all_cats = sorted(set(b_cats) | set(a_cats))
        if all_cats:
            print(f"  {'fail_category':<20}{'before':<12}{'after':<12}{'delta':<12}")
            for cat in all_cats:
                b_n = b_cats.get(cat, 0)
                a_n = a_cats.get(cat, 0)
                d = a_n - b_n
                sign = "+" if d >= 0 else ""
                print(f"  {cat:<20}{b_n:<12}{a_n:<12}{sign}{d:<12}")


def print_transitions(
    before_idx: dict[tuple[str, str, str], dict],
    after_idx: dict[tuple[str, str, str], dict],
    limit: int,
) -> None:
    transitions = []
    for key in sorted(set(before_idx) & set(after_idx)):
        b_row, a_row = before_idx[key], after_idx[key]
        b_cat = b_row.get("fail_category") or "ok"
        a_cat = a_row.get("fail_category") or "ok"
        if b_cat == a_cat:
            continue
        b_ok = b_cat in OK_CATEGORIES or b_cat == "ok"
        a_ok = a_cat in OK_CATEGORIES or a_cat == "ok"
        if a_ok and not b_ok:
            direction = "FIXED"
        elif b_ok and not a_ok:
            direction = "REGRESSED"
        else:
            direction = "CHANGED"
        transitions.append((direction, key, b_cat, a_cat))

    added = sorted(set(after_idx) - set(before_idx))
    removed = sorted(set(before_idx) - set(after_idx))

    order = {"REGRESSED": 0, "CHANGED": 1, "FIXED": 2}
    transitions.sort(key=lambda t: order[t[0]])

    if not transitions and not added and not removed:
        print("\nNo fail_category transitions between before/after.")
        return

    print("\n=== Row transitions (fail_category changed) ===")
    for direction, (dec, fn, variant), b_cat, a_cat in transitions[:limit]:
        print(f"  [{direction:<9}] {dec:<10} {fn:<24} [{variant:<14}] {b_cat} -> {a_cat}")
    if len(transitions) > limit:
        print(f"  ... {len(transitions) - limit} more (raise --show-transitions to see all)")

    if added:
        print(f"\n  {len(added)} row(s) only in AFTER (new corpus entries or newly attempted)")
    if removed:
        print(f"\n  {len(removed)} row(s) only in BEFORE (dropped from corpus or no longer attempted)")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--before", type=Path, required=True, help="Earlier runner.py --output JSON")
    p.add_argument("--after", type=Path, required=True, help="Later runner.py --output JSON")
    p.add_argument(
        "--decompiler",
        default=None,
        help="Restrict to one decompiler (default: all decompilers present in either file)",
    )
    p.add_argument(
        "--show-transitions",
        type=int,
        default=15,
        metavar="N",
        help="Max fail_category transition rows to print (default: 15)",
    )
    args = p.parse_args(argv)

    before = _load(args.before)
    after = _load(args.after)

    before_idx = _index_rows(before, args.decompiler)
    after_idx = _index_rows(after, args.decompiler)

    before_by_dec: dict[str, list[dict]] = {}
    for row in before_idx.values():
        before_by_dec.setdefault(row.get("decompiler", ""), []).append(row)
    after_by_dec: dict[str, list[dict]] = {}
    for row in after_idx.values():
        after_by_dec.setdefault(row.get("decompiler", ""), []).append(row)

    print(f"before: {args.before} (run_id={before.get('run', {}).get('run_id', '?')})")
    print(f"after:  {args.after} (run_id={after.get('run', {}).get('run_id', '?')})")

    print_aggregate_diff(before_by_dec, after_by_dec)
    print_transitions(before_idx, after_idx, args.show_transitions)

    return 0


if __name__ == "__main__":
    sys.exit(main())
