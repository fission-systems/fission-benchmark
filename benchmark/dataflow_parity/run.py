"""Data-flow sink parity — RETURN/STORE sink sets vs Ghidra."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Optional

import typer

from benchmark.common.http_stage import run_http_pair_stage
from benchmark.common.schema import BenchmarkResult, BenchmarkSubject
from benchmark.common.set_compare import as_str_set, compare_payload_sets, jaccard

app = typer.Typer(pretty_exceptions_enable=False)
STAGE = "dataflow_parity"
_VARNODE_KEY = r"[a-z0-9_.-]+\+0x[0-9a-f]+:[0-9]+"
_SINK_KEY_RE = re.compile(rf"^(?:void|{_VARNODE_KEY}(?:<-{_VARNODE_KEY})?)$", re.IGNORECASE)


def _sinks(payload: object) -> set[str]:
    if not isinstance(payload, dict):
        return set()
    tokens = list(payload.get("return_sinks") or []) + list(payload.get("store_sinks") or [])
    return as_str_set(tokens)


def _invalid_sink_tokens(payload: object) -> set[str]:
    return {token for token in _sinks(payload) if not _SINK_KEY_RE.fullmatch(token)}


def compare_dataflow(
    subject: BenchmarkSubject,
    reference_name: str,
    candidate_name: str,
    expected: object,
    actual: object,
) -> BenchmarkResult:
    invalid_reference = _invalid_sink_tokens(expected)
    invalid_candidate = _invalid_sink_tokens(actual)
    if invalid_reference or invalid_candidate:
        side = (
            "both"
            if invalid_reference and invalid_candidate
            else "reference"
            if invalid_reference
            else "candidate"
        )
        return BenchmarkResult(
            subject=subject,
            stage=STAGE,
            status="error",
            reference=reference_name,
            candidate=candidate_name,
            mismatch_kind="sink_contract_invalid",
            expected=expected,
            actual=actual,
            metrics={
                "invalid_reference_tokens": len(invalid_reference),
                "invalid_candidate_tokens": len(invalid_candidate),
                "reliability": "not_scored",
            },
            error=f"Malformed typed dataflow sink token on {side} side",
        )
    row = compare_payload_sets(
        subject,
        STAGE,
        reference_name,
        candidate_name,
        expected,
        actual,
        extract=_sinks,
        mismatch_kind="sink_set",
    )
    # Dual: return-only Jaccard for canary triage
    exp_ret = as_str_set((expected or {}).get("return_sinks") or []) if isinstance(expected, dict) else set()
    act_ret = as_str_set((actual or {}).get("return_sinks") or []) if isinstance(actual, dict) else set()
    metrics = dict(row.metrics or {})
    metrics["return_jaccard"] = jaccard(exp_ret, act_ret)
    return BenchmarkResult(
        subject=row.subject,
        stage=row.stage,
        status=row.status,
        reference=row.reference,
        candidate=row.candidate,
        mismatch_kind=row.mismatch_kind,
        expected=row.expected,
        actual=row.actual,
        metrics=metrics,
        error=row.error,
    )


@app.command()
def main(
    reference_http: str = typer.Option("ghidra"),
    candidate_http: str = typer.Option("fission"),
    corpus: str = typer.Option("dev"),
    output: Path = typer.Option(Path("results/dataflow_parity/latest.jsonl")),
    limit: Optional[int] = typer.Option(None),
    timeout: float = typer.Option(90.0),
):
    run_http_pair_stage(
        stage=STAGE,
        compare=compare_dataflow,
        reference_http=reference_http,
        candidate_http=candidate_http,
        corpus=corpus,
        output=output,
        limit=limit,
        timeout=timeout,
    )


if __name__ == "__main__":
    app()
