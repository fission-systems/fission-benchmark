"""Whole-program metadata parity against Ghidra's program database."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import typer

from benchmark.common.http_providers import fetch_parity_json
from benchmark.common.io import write_jsonl
from benchmark.common.schema import BenchmarkResult, BenchmarkSubject
from benchmark.common.set_compare import jaccard
from benchmark.common.subjects import load_subjects

app = typer.Typer(pretty_exceptions_enable=False)
STAGE = "metadata_parity"


def _as_int(value: object) -> int:
    if isinstance(value, int):
        return value
    text = str(value or "0").strip().lower()
    try:
        return int(text, 16) if text.startswith("0x") else int(text, 10)
    except ValueError:
        return 0


def _rows(payload: object, name: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    rows = payload.get(name)
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _block_keys(payload: object) -> set[tuple[int, int, bool, bool, bool]]:
    out = set()
    for row in _rows(payload, "memory_blocks"):
        permissions = row.get("permissions") or {}
        out.add(
            (
                _as_int(row.get("start")),
                _as_int(row.get("size")),
                bool(permissions.get("read")),
                bool(permissions.get("write")),
                bool(permissions.get("execute")),
            )
        )
    return out


def _block_start_keys(payload: object) -> set[tuple[int, bool, bool, bool]]:
    return {
        (start, read, write, execute)
        for start, _size, read, write, execute in _block_keys(payload)
    }


def _address_keys(payload: object, table: str, field: str) -> set[int]:
    return {_as_int(row.get(field)) for row in _rows(payload, table)}


def _symbol_source(row: dict[str, Any]) -> str:
    source = row.get("source")
    if source is None and isinstance(row.get("provenance"), dict):
        source = row["provenance"].get("source")
    return str(source or "").strip().lower()


def _loader_symbol_address_keys(payload: object) -> set[int]:
    rows = _rows(payload, "symbols")
    sources = {_symbol_source(row) for row in rows}
    if not any(sources):
        # Compatibility for providers predating symbol provenance.
        return {_as_int(row.get("address")) for row in rows}

    ghidra_sources = {"imported"}
    fission_sources = {
        "symbol_table",
        "import_table",
        "export_table",
        "debug_info",
    }
    comparable_sources = ghidra_sources | fission_sources
    return {
        _as_int(row.get("address"))
        for row in rows
        if _symbol_source(row) in comparable_sources
    }


def _generated_symbol_address_keys(payload: object) -> set[int]:
    return {
        _as_int(row.get("address"))
        for row in _rows(payload, "symbols")
        if _symbol_source(row) in {"default", "analysis"}
    }


def _relocation_address_keys(payload: object) -> set[int]:
    return {
        _as_int(row.get("address"))
        for row in _rows(payload, "relocations")
        if _as_int(row.get("relocation_type")) != 0
    }


def _binary_identity(payload: object) -> tuple[int, int, str]:
    binary = payload.get("binary") if isinstance(payload, dict) else {}
    binary = binary if isinstance(binary, dict) else {}
    return (
        _as_int(binary.get("bitness")),
        _as_int(binary.get("image_base")),
        str(binary.get("language_id") or "").lower(),
    )


def _error(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return "metadata payload is not an object"
    if payload.get("status") == "error" or payload.get("error"):
        return str(payload.get("error") or "metadata endpoint error")
    if not payload.get("schema"):
        return "metadata payload has no schema"
    return None


def compare_metadata(
    subject: BenchmarkSubject,
    reference_name: str,
    candidate_name: str,
    expected: object,
    actual: object,
) -> BenchmarkResult:
    reference_error = _error(expected)
    candidate_error = _error(actual)
    if reference_error or candidate_error:
        status = "reference_empty" if reference_error else "candidate_empty"
        return BenchmarkResult(
            subject=subject,
            stage=STAGE,  # type: ignore[arg-type]
            status=status,  # type: ignore[arg-type]
            reference=reference_name,
            candidate=candidate_name,
            expected=expected,
            actual=actual,
            error=reference_error or candidate_error,
        )

    ref_identity = _binary_identity(expected)
    cand_identity = _binary_identity(actual)
    ref_blocks = _block_keys(expected)
    cand_blocks = _block_keys(actual)
    ref_block_starts = _block_start_keys(expected)
    cand_block_starts = _block_start_keys(actual)
    ref_functions = _address_keys(expected, "functions", "entry")
    cand_functions = _address_keys(actual, "functions", "entry")
    ref_raw_symbols = _address_keys(expected, "symbols", "address")
    cand_raw_symbols = _address_keys(actual, "symbols", "address")
    ref_symbols = _loader_symbol_address_keys(expected)
    cand_symbols = _loader_symbol_address_keys(actual)
    ref_generated_symbols = _generated_symbol_address_keys(expected)
    ref_relocations = _relocation_address_keys(expected)
    cand_relocations = _relocation_address_keys(actual)
    shared_functions = len(ref_functions & cand_functions)
    shared_symbols = len(ref_symbols & cand_symbols)
    shared_relocations = len(ref_relocations & cand_relocations)
    core_metadata_match = (
        ref_identity == cand_identity
        and ref_blocks == cand_blocks
        and ref_functions == cand_functions
        and ref_relocations == cand_relocations
    )

    comparisons = (
        ("binary_identity", ref_identity == cand_identity),
        ("memory_blocks", ref_blocks == cand_blocks),
        ("function_entries", ref_functions == cand_functions),
        ("symbol_addresses", ref_symbols == cand_symbols),
        ("relocation_addresses", ref_relocations == cand_relocations),
    )
    mismatch_kind = next((name for name, matches in comparisons if not matches), None)
    status = "match" if mismatch_kind is None else "mismatch"

    return BenchmarkResult(
        subject=subject,
        stage=STAGE,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        reference=reference_name,
        candidate=candidate_name,
        mismatch_kind=mismatch_kind,
        expected=expected,
        actual=actual,
        metrics={
            "core_metadata_match": int(core_metadata_match),
            "binary_identity_match": int(ref_identity == cand_identity),
            "memory_block_jaccard": jaccard(ref_blocks, cand_blocks),
            "memory_block_start_permission_jaccard": jaccard(
                ref_block_starts, cand_block_starts
            ),
            "function_entry_jaccard": jaccard(ref_functions, cand_functions),
            "function_reference_recall": round(
                shared_functions / len(ref_functions), 4
            )
            if ref_functions
            else 1.0,
            "function_candidate_precision": round(
                shared_functions / len(cand_functions), 4
            )
            if cand_functions
            else 1.0,
            "symbol_address_jaccard": jaccard(ref_symbols, cand_symbols),
            "raw_symbol_address_jaccard": jaccard(
                ref_raw_symbols, cand_raw_symbols
            ),
            "symbol_reference_recall": round(shared_symbols / len(ref_symbols), 4)
            if ref_symbols
            else 1.0,
            "symbol_candidate_precision": round(
                shared_symbols / len(cand_symbols), 4
            )
            if cand_symbols
            else 1.0,
            "relocation_address_jaccard": jaccard(ref_relocations, cand_relocations),
            "relocation_reference_recall": round(
                shared_relocations / len(ref_relocations), 4
            )
            if ref_relocations
            else 1.0,
            "ref_memory_blocks": len(ref_blocks),
            "cand_memory_blocks": len(cand_blocks),
            "ref_functions": len(ref_functions),
            "cand_functions": len(cand_functions),
            "ref_symbols": len(ref_symbols),
            "cand_symbols": len(cand_symbols),
            "ref_raw_symbols": len(ref_raw_symbols),
            "cand_raw_symbols": len(cand_raw_symbols),
            "ref_generated_symbols": len(ref_generated_symbols),
            "ref_relocations": len(ref_relocations),
            "cand_relocations": len(cand_relocations),
        },
    )


def _binary_subjects(corpus: str, limit: int | None) -> list[BenchmarkSubject]:
    seen: set[str] = set()
    rows: list[BenchmarkSubject] = []
    for subject in load_subjects(corpus):
        if subject.binary in seen:
            continue
        seen.add(subject.binary)
        rows.append(
            BenchmarkSubject(
                binary=subject.binary,
                function="(metadata)",
                addr="0x0",
                arch=subject.arch,
                compiler=subject.compiler,
                opt=subject.opt,
                corpus_split=subject.corpus_split,
            )
        )
        if limit is not None and len(rows) >= limit:
            break
    return rows


@app.command()
def main(
    reference_http: str = typer.Option("ghidra"),
    candidate_http: str = typer.Option("fission"),
    corpus: str = typer.Option("dev"),
    output: Path = typer.Option(Path("results/metadata_parity/latest.jsonl")),
    limit: Optional[int] = typer.Option(None),
    timeout: float = typer.Option(240.0),
):
    results: list[BenchmarkResult] = []
    for subject in _binary_subjects(corpus, limit):
        try:
            expected = fetch_parity_json(reference_http, STAGE, subject, timeout=timeout)
        except Exception as exc:
            expected = {"status": "error", "error": str(exc)}
        try:
            actual = fetch_parity_json(candidate_http, STAGE, subject, timeout=timeout)
        except Exception as exc:
            actual = {"status": "error", "error": str(exc)}
        results.append(
            compare_metadata(subject, reference_http, candidate_http, expected, actual)
        )
    write_jsonl(output, results)
    matches = sum(row.status == "match" for row in results)
    typer.echo(f"Wrote {len(results)} metadata rows (match={matches}) to {output}")


if __name__ == "__main__":
    app()
