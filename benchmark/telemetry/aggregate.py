"""Aggregate layered benchmark JSONL telemetry."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import typer

from benchmark.common.io import read_jsonl

app = typer.Typer(pretty_exceptions_enable=False)

STAGE_ORDER = (
    "assembly_parity",
    # decode_parity: retired stub stage — excluded from auto-discover to prevent
    # stale results/decode_parity/latest.jsonl from inflating total_rows.
    "pcode_parity",
    "cfg_parity",
    "function_discovery",
    "metadata_parity",
    "ir_invariants",
    "abi_parity",
    "type_parity",
    "callgraph_parity",
    "string_recovery",
    "dataflow_parity",
    "seh_parity",
    "strip_discovery",
    "strip_semantic_delta",
    "opt_cliff",
    "throughput",
    "golden_repros",
)

# Stages excluded from *headline* publishable quality rates.
# - decode: stub surface (disasm-derived)
# - ir_invariants: weak structural checks, not full IR equivalence
# - golden_repros: meta canaries (locks), not a quality rate
# - extension tracks (abi/types/callgraph/…): diagnostic until promoted
# function_discovery is primary when scored as ghidra_inventory (unified runner).
NON_PUBLISHABLE_STAGES = frozenset(
    {
        "decode_parity",
        "ir_invariants",
        "golden_repros",
        "abi_parity",
        "metadata_parity",
        "type_parity",
        "callgraph_parity",
        "string_recovery",
        "dataflow_parity",
        "seh_parity",
        "strip_discovery",
        "strip_semantic_delta",
        "opt_cliff",
        "throughput",
    }
)

# Stages that *are* primary layered quality (Ghidra reference vs candidate).
PRIMARY_QUALITY_STAGES = frozenset(
    {
        "assembly_parity",
        "pcode_parity",
        "cfg_parity",
        "function_discovery",
    }
)
_VERSION_RE = re.compile(r"^v?\d+\.\d+\.\d+$")


def _utc_iso(timestamp: float | None = None) -> str:
    value = datetime.fromtimestamp(
        timestamp if timestamp is not None else datetime.now().timestamp(),
        tz=timezone.utc,
    )
    return value.isoformat().replace("+00:00", "Z")


def build_provenance(paths: list[Path]) -> dict:
    """Describe exactly which stage snapshots produced a dashboard aggregate."""
    sources: list[dict] = []
    for path in paths:
        stat = path.stat()
        payload = path.read_bytes()
        row_count = sum(1 for line in payload.splitlines() if line.strip())
        sources.append(
            {
                "path": str(path),
                "stage": path.parent.name,
                "rows": row_count,
                "bytes": stat.st_size,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "modified_at": _utc_iso(stat.st_mtime),
            }
        )

    modified = [source["modified_at"] for source in sources]
    runner_commit = os.environ.get("GITHUB_SHA") or os.environ.get("BENCHMARK_COMMIT")
    if not runner_commit:
        try:
            runner_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            runner_commit = None

    return {
        "generated_at": _utc_iso(),
        "runner_commit": runner_commit,
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "corpus": os.environ.get("CORPUS_SPLIT"),
        "decompilers": os.environ.get("PARITY_DECOMPILERS"),
        "tool_versions": {
            "fission": os.environ.get("FISSION_VERSION"),
            "ghidra": os.environ.get("GHIDRA_VERSION"),
        },
        "oldest_source_at": min(modified) if modified else None,
        "newest_source_at": max(modified) if modified else None,
        "sources": sources,
    }


def archive_release_telemetry(summary: dict, history_dir: Path) -> str | None:
    """Archive parity telemetry only when it names a semantic Fission release."""
    version = str(
        (((summary.get("provenance") or {}).get("tool_versions") or {}).get("fission"))
        or ""
    )
    if not _VERSION_RE.fullmatch(version):
        return None
    history_dir.mkdir(parents=True, exist_ok=True)
    (history_dir / f"{version}.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    versions = {
        path.stem
        for path in history_dir.glob("v*.json")
        if path.stem != "index"
    }
    ordered = sorted(
        versions,
        key=lambda value: tuple(
            int(part) for part in value.removeprefix("v").split(".")
        ),
    )
    (history_dir / "index.json").write_text(
        json.dumps(ordered, indent=2) + "\n",
        encoding="utf-8",
    )
    return version


def aggregate_rows(rows: list[dict]) -> dict:
    by_stage: Counter[str] = Counter()
    by_status: Counter[str] = Counter()
    by_mismatch_kind: Counter[str] = Counter()
    by_variant: Counter[str] = Counter()
    # stage -> status -> count
    stage_status: dict[str, Counter[str]] = defaultdict(Counter)
    stage_mismatch: dict[str, Counter[str]] = defaultdict(Counter)
    pair_counts: Counter[str] = Counter()
    # Dual pcode metrics (when present on rows)
    pcode_opcode_agree = 0
    pcode_loose_full = 0
    pcode_strict_full = 0
    pcode_literal_full = 0
    pcode_metric_n = 0
    fd_presence_only = 0
    fd_n = 0
    fd_presence_recall_sum = 0.0
    fd_manifest_recall_sum = 0.0
    fd_metric_n = 0
    cfg_edge_j_sum = 0.0
    cfg_block_j_sum = 0.0
    cfg_metric_n = 0
    # opt_cliff: {candidate: {opt: [correctness, ...]}}
    opt_cliff_by_cand: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    # throughput: {candidate: [time_ms, ...]}
    throughput_by_cand: dict[str, list[float]] = defaultdict(list)

    for row in rows:
        subject = row.get("subject", {}) or {}
        stage = str(row.get("stage", "unknown"))
        status = str(row.get("status", "unknown"))
        mismatch_kind = row.get("mismatch_kind") or "none"
        variant = f"{subject.get('compiler', '?')} {subject.get('opt', '?')}"
        pair = f"{row.get('reference', '?')}→{row.get('candidate', '?')}"

        by_stage[stage] += 1
        by_status[status] += 1
        by_mismatch_kind[str(mismatch_kind)] += 1
        by_variant[variant] += 1
        stage_status[stage][status] += 1
        if status == "mismatch":
            stage_mismatch[stage][str(mismatch_kind)] += 1
        pair_counts[pair] += 1

        metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
        if stage == "pcode_parity" and status in {"match", "mismatch"} and metrics:
            if any(k in metrics for k in ("opcode_sequence_match", "loose_full_match", "strict_full_match")):
                pcode_metric_n += 1
                pcode_opcode_agree += int(metrics.get("opcode_sequence_match") or 0)
                pcode_loose_full += int(metrics.get("loose_full_match") or 0)
                pcode_strict_full += int(metrics.get("strict_full_match") or 0)
                pcode_literal_full += int(metrics.get("literal_full_match") or 0)
        if stage == "cfg_parity" and status in {"match", "mismatch"} and metrics:
            if "edge_pair_jaccard" in metrics or "block_start_jaccard" in metrics:
                cfg_metric_n += 1
                cfg_edge_j_sum += float(metrics.get("edge_pair_jaccard") or 0)
                cfg_block_j_sum += float(metrics.get("block_start_jaccard") or 0)
        if stage == "function_discovery":
            fd_n += 1
            scored = str(metrics.get("scored_as") or "")
            # Modern inventory rows always set scored_as + dual presence metrics.
            modern_tags = {
                "ghidra_inventory",
                "pe_symbol_inventory",
                "manifest_inventory",
            }
            if scored not in modern_tags:
                fd_presence_only += 1
            if status in {"match", "mismatch"} and metrics:
                fd_metric_n += 1
                if metrics.get("presence_recall") is not None:
                    fd_presence_recall_sum += float(metrics["presence_recall"])
                if metrics.get("manifest_recall") is not None:
                    fd_manifest_recall_sum += float(metrics["manifest_recall"])
        if stage == "opt_cliff" and metrics:
            cand = str(row.get("candidate") or "unknown")
            opt = str(metrics.get("opt") or subject.get("opt") or "?")
            correctness = metrics.get("correctness")
            if correctness is not None:
                opt_cliff_by_cand[cand][opt].append(float(correctness))
        if stage == "throughput" and metrics:
            cand = str(row.get("candidate") or "unknown")
            # Only aggregate rows (not per-binary rows) carry mean_ms
            if "mean_ms" in metrics and metrics.get("mean_ms") is not None:
                throughput_by_cand[cand].append(float(metrics["mean_ms"]))
            elif "time_ms" in metrics and metrics.get("time_ms") is not None:
                # per-binary rows also accepted if no aggregate present
                throughput_by_cand.setdefault(cand, [])  # ensure key exists

    stages_detail = {}
    for stage in sorted(set(list(STAGE_ORDER) + list(by_stage.keys())), key=lambda s: (STAGE_ORDER.index(s) if s in STAGE_ORDER else 99, s)):
        if stage not in by_stage:
            continue
        statuses = dict(stage_status[stage])
        total = by_stage[stage]
        match = statuses.get("match", 0)
        mismatch = statuses.get("mismatch", 0)
        skipped = statuses.get("skipped", 0)
        fetch_error = statuses.get("fetch_error", 0)
        both_empty = statuses.get("both_empty_invalid", 0)
        ref_empty = statuses.get("reference_empty", 0)
        cand_empty = statuses.get("candidate_empty", 0)
        # BUG-04 fix: errorish must reflect genuine infra failures only.
        # skipped = intentional exclusion (e.g. decode_surface_stub) — not an error.
        # both_empty/ref_empty/cand_empty are tracked separately and have their own
        # semantics. Only fetch_error and truly unknown statuses are infra failures.
        errorish = total - match - mismatch - skipped - both_empty - ref_empty - cand_empty
        comparable = match + mismatch
        # Reliability: coverage of attempts that produced a quality signal.
        usable_coverage = round(comparable / total, 4) if total else None
        # Does NOT drop infra failures — lower when adapters fail.
        match_rate_attempted = round(match / total, 4) if total else None
        detail = {
            "total": total,
            "match": match,
            "mismatch": mismatch,
            "skipped": skipped,
            "fetch_error": fetch_error,
            "both_empty_invalid": both_empty,
            "reference_empty": ref_empty,
            "candidate_empty": cand_empty,
            "error_or_other": errorish,
            # Historical name: among scored (match|mismatch) only.
            "match_rate": round(match / comparable, 4) if comparable else None,
            "mismatch_rate": round(mismatch / comparable, 4) if comparable else None,
            "match_rate_comparable": round(match / comparable, 4) if comparable else None,
            "match_rate_attempted": match_rate_attempted,
            "usable_coverage": usable_coverage,
            "primary_quality": stage in PRIMARY_QUALITY_STAGES,
            "by_status": dict(sorted(statuses.items())),
            "by_mismatch_kind": dict(sorted(stage_mismatch[stage].items())),
        }
        if stage == "pcode_parity" and pcode_metric_n:
            detail["dual"] = {
                "n": pcode_metric_n,
                "opcode_sequence_match_rate": round(pcode_opcode_agree / pcode_metric_n, 4),
                "loose_full_match_rate": round(pcode_loose_full / pcode_metric_n, 4),
                "strict_full_match_rate": round(pcode_strict_full / pcode_metric_n, 4),
                "literal_full_match_rate": round(pcode_literal_full / pcode_metric_n, 4),
                "space_id_policy": "selector_abstract_under_strict",
                "note": (
                    "strict (primary): abstract LOAD/STORE space-selector offsets; "
                    "literal: raw tool space-table ids; loose: stub selector entirely."
                ),
            }
        if stage == "cfg_parity" and cfg_metric_n:
            detail["dual"] = {
                "n": cfg_metric_n,
                "mean_block_start_jaccard": round(cfg_block_j_sum / cfg_metric_n, 4),
                "mean_edge_pair_jaccard": round(cfg_edge_j_sum / cfg_metric_n, 4),
                "note": (
                    "Jaccard on block starts and kind-agnostic (src,tgt) edges; "
                    "status match still requires full canonical equality."
                ),
            }
        if stage == "decode_parity":
            detail["reliability_note"] = (
                "RETIRED from active suite (stub disasm→decode). Re-enable only with "
                "real modrm/sib/disp/imm on both adapters."
            )
            detail["retired"] = True
        if stage == "function_discovery" and fd_n:
            detail["reliability_note"] = (
                "Primary scoring is Ghidra full inventory vs candidate (address set). "
                "Exact set equality is strict; use dual recall metrics for triage."
            )
            if fd_metric_n:
                detail["dual"] = {
                    "n": fd_metric_n,
                    "mean_presence_recall": round(
                        fd_presence_recall_sum / fd_metric_n, 4
                    ),
                    "mean_manifest_recall": round(
                        fd_manifest_recall_sum / fd_metric_n, 4
                    ),
                    "note": (
                        "presence_recall = |R∩C|/|R|; presence_precision = |R∩C|/|C|; "
                        "manifest_recall = corpus subject addresses found by candidate. "
                        "See runner/function_discovery_report.py for full matrix."
                    ),
                }
            if fd_presence_only:
                detail["legacy_presence_rows"] = fd_presence_only
                detail["reliability_note"] += (
                    f" Warning: {fd_presence_only} legacy presence-scored rows detected."
                )
        if stage == "ir_invariants":
            detail["reliability_note"] = (
                "Structural CFG checks only (empty blocks / edge sources); "
                "not full IR equivalence."
            )
        if stage == "opt_cliff" and opt_cliff_by_cand:
            detail["by_candidate"] = {
                cand: {
                    opt: {
                        "n": len(scores),
                        "mean_correctness": round(sum(scores) / len(scores), 4),
                    }
                    for opt, scores in by_opt.items()
                }
                for cand, by_opt in sorted(opt_cliff_by_cand.items())
            }
        if stage == "throughput" and throughput_by_cand:
            detail["throughput_by_candidate"] = {
                cand: {
                    "n": len(ms_list),
                    "mean_ms": round(sum(ms_list) / len(ms_list), 2) if ms_list else 0,
                }
                for cand, ms_list in sorted(throughput_by_cand.items())
                if ms_list
            }
        stages_detail[stage] = detail

    # Run-level reliability rollup (excludes skipped-only stages from quality).
    total_rows = len(rows)
    total_match = by_status.get("match", 0)
    total_mismatch = by_status.get("mismatch", 0)
    total_comparable = total_match + total_mismatch
    total_fetch = by_status.get("fetch_error", 0)
    reliability = {
        "usable_coverage": round(total_comparable / total_rows, 4) if total_rows else None,
        "match_rate_comparable": (
            round(total_match / total_comparable, 4) if total_comparable else None
        ),
        "match_rate_attempted": round(total_match / total_rows, 4) if total_rows else None,
        "fetch_error_rate": round(total_fetch / total_rows, 4) if total_rows else None,
        "skipped_rate": (
            round(by_status.get("skipped", 0) / total_rows, 4) if total_rows else None
        ),
    }

    # Headline publishable = primary quality stages only (asm / pcode / cfg).
    publishable_stages = {
        k: v for k, v in stages_detail.items() if k in PRIMARY_QUALITY_STAGES
    }
    pub_match = sum(int(v.get("match") or 0) for v in publishable_stages.values())
    pub_mismatch = sum(int(v.get("mismatch") or 0) for v in publishable_stages.values())
    pub_total = sum(int(v.get("total") or 0) for v in publishable_stages.values())
    pub_comparable = pub_match + pub_mismatch
    canonicalize_mode = (
        (os.environ.get("PARITY_CANONICALIZE_MODE") or "strict").strip().lower()
    )
    if canonicalize_mode not in {"loose", "strict"}:
        canonicalize_mode = "strict"

    reliability_critique = {
        "schema": "parity-reliability-critique-v1",
        "headline_stages": sorted(PRIMARY_QUALITY_STAGES),
        "demoted_stages": sorted(NON_PUBLISHABLE_STAGES),
        "warnings": [],
    }
    # Inflated overall rates if demoted high-match stages were included.
    if "function_discovery" in stages_detail:
        fd = stages_detail["function_discovery"]
        if fd.get("legacy_presence_rows"):
            reliability_critique["warnings"].append(
                "function_discovery contains legacy presence-scored rows; re-run parity."
            )
        elif (fd.get("match_rate") or 0) >= 0.99 and (fd.get("total") or 0) >= 5:
            reliability_critique["warnings"].append(
                "function_discovery near-100% inventory match — verify Ghidra/candidate "
                "are not under-discovering the same way."
            )
    if "ir_invariants" in stages_detail:
        ir = stages_detail["ir_invariants"]
        if (ir.get("match_rate") or 0) >= 0.9:
            reliability_critique["warnings"].append(
                "ir_invariants high match rate reflects weak structural checks only."
            )
    pcode_detail = stages_detail.get("pcode_parity") or {}
    dual = pcode_detail.get("dual") or {}
    if dual:
        if (dual.get("literal_full_match_rate") or 0) + 0.3 < (
            dual.get("strict_full_match_rate") or 0
        ):
            reliability_critique["warnings"].append(
                "pcode literal_full << strict_full: remaining gap is space-table id "
                "encoding (documented selector_abstract_under_strict policy)."
            )
        if (dual.get("opcode_sequence_match_rate") or 0) > (
            dual.get("strict_full_match_rate") or 0
        ) + 0.3:
            reliability_critique["warnings"].append(
                "pcode opcode sequences agree more than strict full varnodes — "
                "inspect dual metrics for residual semantic gaps."
            )

    return {
        "schema": "parity-telemetry-v3",
        "total_rows": total_rows,
        "by_stage": dict(sorted(by_stage.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_mismatch_kind": dict(sorted(by_mismatch_kind.items())),
        "by_variant": dict(sorted(by_variant.items())),
        "by_pair": dict(sorted(pair_counts.items())),
        "stages": stages_detail,
        "reliability": reliability,
        "reliability_critique": reliability_critique,
        "reliability_policy": "conservative",
        "canonicalize_mode": canonicalize_mode,
        "non_publishable_stages": sorted(NON_PUBLISHABLE_STAGES),
        "primary_quality_stages": sorted(PRIMARY_QUALITY_STAGES),
        "publishable": {
            "stages": publishable_stages,
            "total_rows": pub_total,
            "match": pub_match,
            "mismatch": pub_mismatch,
            "match_rate_comparable": (
                round(pub_match / pub_comparable, 4) if pub_comparable else None
            ),
            "usable_coverage": (
                round(pub_comparable / pub_total, 4) if pub_total else None
            ),
            "definition": (
                "Headline quality = assembly + pcode + cfg + function_discovery "
                "(Ghidra inventory). Decode/IR/golden are diagnostic or meta."
            ),
            "pcode_dual": dual or None,
        },
    }


@app.command()
def main(
    inputs: list[Path] = typer.Argument(None, help="Input JSONL result files"),
    output: Path = typer.Option(Path("results/telemetry/latest.json")),
    dashboard_copy: Path = typer.Option(
        Path("public/parity-telemetry.json"),
        help="Optional Next.js static copy for the parity dashboard panel",
    ),
    history_dir: Path = typer.Option(
        Path("public/parity-history"),
        help="Version-keyed parity telemetry history",
    ),
    auto_discover: bool = typer.Option(
        True,
        help="If no inputs, discover results/*_parity/latest.jsonl and golden_repros",
    ),
):
    paths = list(inputs or [])
    if not paths and auto_discover:
        root = Path("results")
        for stage in STAGE_ORDER:
            candidate = root / stage / "latest.jsonl"
            if candidate.is_file():
                paths.append(candidate)

    rows: list[dict] = []
    for path in paths:
        rows.extend(read_jsonl(path))

    summary = aggregate_rows(rows)
    summary["sources"] = [str(p) for p in paths]
    summary["provenance"] = build_provenance(paths)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    output.write_text(payload, encoding="utf-8")
    if dashboard_copy:
        dashboard_copy.parent.mkdir(parents=True, exist_ok=True)
        dashboard_copy.write_text(payload, encoding="utf-8")
    archived = archive_release_telemetry(summary, history_dir) if history_dir else None
    typer.echo(f"Wrote telemetry summary for {len(rows)} rows to {output}")
    if dashboard_copy:
        typer.echo(f"Dashboard copy: {dashboard_copy}")
    if archived:
        typer.echo(f"Release parity history: {archived}")
    else:
        typer.echo("Release parity history skipped: no semantic Fission version")


if __name__ == "__main__":
    app()
