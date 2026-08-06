"""Benchmark runner to decompile and score binaries."""
import asyncio
import base64
from collections import Counter
import hashlib
import json
import os
import platform
import sys
import time
import uuid
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path
from typing import Any, List

import httpx
import typer

sys.path.insert(0, str(Path(__file__).parent))
from corpus import CORPUS_ROOT, Corpus
from scoring import (
    FunctionScore,
    assign_consensus_ranks,
    check_uses_intrinsics,
    extract_function_source,
    source_similarity,
    structural_score,
)
from semantic import verify_semantic_correctness_async
from differential_oracle import aggregate_oracle_evidence, verify_with_oracle
from readability import analyze_readability, ast_structure_similarity, summarize_readability_proxy_score
from output_diagnostics import analyze_output_diagnostics, invalid_output_reason
from run_validity import build_envelope
from test_wrappers import TEST_WRAPPERS
from bare_compile import try_bare_compile, classify_track, classify_isa_format
from type_match import calibrate_binary_shift, compute_type_match, ground_truth_for_binary
from ged import (
    compute_ged,
    extract_decompiled_cfgs,
    extract_source_cfgs,
    load_published_source_cfgs,
)
from preprocessed_tu import PREPROCESSED_TU_SCHEMA
from recompilation import measure_recompilation
from checkpoint import BenchmarkCheckpoint, CHECKPOINT_SCHEMA
from metric_cache import CACHE_SCHEMA
import subprocess

app = typer.Typer(help="Fission decompiler benchmark runner.")

# Source-level goto/nesting counts keyed by function name.
# Populated from corpus manifest or precomputed via scripts/precompute_source_metrics.py.
SOURCE_GOTO_COUNTS: dict[str, int] = {}
SOURCE_NESTING_DEPTHS: dict[str, int] = {}


def _subject_name(function: Any) -> str:
    return str(getattr(function, "subject_name", "") or function.name)


def _host_fingerprint() -> dict[str, Any]:
    """Stable-enough host context for non-ranking local performance evidence."""
    memory_bytes = 0
    processor = platform.processor()
    try:
        memory_bytes = int(os.sysconf("SC_PAGE_SIZE")) * int(
            os.sysconf("SC_PHYS_PAGES")
        )
    except (AttributeError, OSError, ValueError):
        pass
    if platform.system() == "Darwin":
        try:
            memory_bytes = int(
                subprocess.check_output(["sysctl", "-n", "hw.memsize"])
                .decode()
                .strip()
            )
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
        if not processor:
            for key in ("machdep.cpu.brand_string", "hw.model"):
                try:
                    processor = (
                        subprocess.check_output(["sysctl", "-n", key])
                        .decode()
                        .strip()
                    )
                except (OSError, subprocess.SubprocessError):
                    continue
                if processor:
                    break
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": processor,
        "cpu_count": os.cpu_count() or 0,
        "memory_bytes": memory_bytes,
    }


def filter_functions(functions: list, requested: str | None) -> list:
    """Select named functions while preserving corpus manifest order."""
    if not requested:
        return functions
    names = [name.strip() for name in requested.split(",") if name.strip()]
    if not names:
        raise ValueError("function filter is empty")
    requested_names = set(names)
    identities = {_subject_name(fn) for fn in functions}
    symbols: dict[str, list] = {}
    for fn in functions:
        symbols.setdefault(fn.name, []).append(fn)
    available_names = identities | set(symbols)
    missing = sorted(requested_names - available_names)
    if missing:
        raise ValueError(f"unknown function(s): {', '.join(missing)}")
    ambiguous = sorted(
        name
        for name in requested_names
        if name not in identities and len(symbols.get(name, [])) > 1
    )
    if ambiguous:
        raise ValueError(
            "ambiguous external symbol(s); use the namespaced subject id: "
            + ", ".join(ambiguous)
        )
    return [
        fn
        for fn in functions
        if _subject_name(fn) in requested_names or fn.name in requested_names
    ]


def format_semantic_score(score: float | None) -> str:
    """Format semantic evidence without treating an untestable row as failure."""
    return "n/a" if score is None else f"{score:.2f}"


def build_expected_cells(
    functions: list,
    decompiler_names: list[str],
    variant_limit: int | None,
) -> list[dict[str, str]]:
    """Build the exact matrix from the same function list passed to run_all."""
    cells = []
    for function in functions:
        variants = function.compiler_variants[:variant_limit] if variant_limit else function.compiler_variants
        for variant in variants:
            for decompiler in decompiler_names:
                cells.append({
                    "decompiler": decompiler,
                    "function_name": _subject_name(function),
                    "compiler_variant": f"{variant.compiler} {variant.opt}",
                })
    return cells


def fission_toolchain_metadata() -> dict[str, str]:
    """Return local/release Fission provenance exported by the adapter setup."""
    git_sha = os.environ.get("FISSION_GIT_SHA", "")
    version = (
        os.environ.get("FISSION_VERSION")
        or os.environ.get("FISSION_RELEASE_VERSION")
        or (f"local-{git_sha}" if git_sha else "unknown")
    )
    return {
        "fission_version": version,
        "fission_git_sha": git_sha,
        "fission_source": os.environ.get("FISSION_SOURCE", "unknown"),
        "fission_source_fingerprint": os.environ.get(
            "FISSION_SOURCE_FINGERPRINT", ""
        ),
    }


def _load_source_metrics() -> None:
    """Load precomputed source-level structural metrics if available."""
    metrics_path = Path(__file__).parent.parent / "corpus" / "source_metrics.json"
    if metrics_path.exists():
        data = json.loads(metrics_path.read_text())
        SOURCE_GOTO_COUNTS.update(data.get("goto_counts", {}))
        SOURCE_NESTING_DEPTHS.update(data.get("nesting_depths", {}))


# Module-level flag to ensure .env is only parsed once per process.
_ENV_LOADED = False


def configured_decompilers() -> dict[str, str]:
    """Get configured decompiler HTTP endpoints from environment.

    Each decompiler's endpoint can be overridden with the ``{NAME}_ENDPOINT``
    environment variable (e.g. ``GHIDRA_ENDPOINT=http://host:9001``).
    Setting any endpoint to ``skip`` (case-insensitive) excludes that
    decompiler from the run without requiring changes to ``--decompilers``.
    """
    global _ENV_LOADED
    if not _ENV_LOADED:
        # Load .env once if it exists in the workspace root.
        env_path = Path(__file__).resolve().parents[1] / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    val_str = val.strip().strip(chr(39) + chr(34))
                    os.environ.setdefault(key.strip(), val_str)
        _ENV_LOADED = True

    # Default local dev ports mapped in docker-compose.yml.
    # Each entry can be overridden by {NAME}_ENDPOINT environment variable.
    defaults = {
        "fission":   os.environ.get("FISSION_ENDPOINT",   "http://localhost:8000"),
        "ghidra":    os.environ.get("GHIDRA_ENDPOINT",    "http://localhost:8001"),
        "boomerang": os.environ.get("BOOMERANG_ENDPOINT", "http://localhost:8002"),
        "radare2":   os.environ.get("RADARE2_ENDPOINT",   "http://localhost:8003"),
        "angr":      os.environ.get("ANGR_ENDPOINT",      "http://localhost:8004"),
        "snowman":   os.environ.get("SNOWMAN_ENDPOINT",   "http://localhost:8005"),
        "revng":     os.environ.get("REVNG_ENDPOINT",     "http://localhost:8006"),
        "reko":      os.environ.get("REKO_ENDPOINT",      "http://localhost:8008"),
        "retdec":    os.environ.get("RETDEC_ENDPOINT",    "http://localhost:8009"),
    }
    # Exclude any endpoint explicitly set to "skip".
    return {k: v for k, v in defaults.items() if v.lower() != "skip"}


async def decompile_batch_and_score(
    client: httpx.AsyncClient,
    dname: str,
    url: str,
    binary_path: Path,
    targets: List[tuple],  # fn, variant, function source, GED TU path, GED basis
    sem: asyncio.Semaphore,
    oracle_endpoint: str | None,
    corpus_split: str = "dev",
    checkpoint: BenchmarkCheckpoint | None = None,
) -> List[FunctionScore]:
    addresses = [t[1].addr for t in targets]
    try:
        binary_rel = str(binary_path.relative_to(CORPUS_ROOT / corpus_split))
    except ValueError:
        binary_rel = str(binary_path)

    def _ged_provenance(target: tuple) -> dict[str, Any]:
        source_path = target[3]
        try:
            source_rel = str(source_path.relative_to(CORPUS_ROOT / corpus_split))
        except ValueError:
            source_rel = str(source_path)
        return {
            "source_basis": target[4],
            "source_path": source_rel,
            "source_contract": (
                "decbench-published-source-cfg-v1"
                if target[4] == "published_source_cfg"
                else PREPROCESSED_TU_SCHEMA
            ),
        }

    def _failure_score(
        target: tuple, message: str, category: str = "adapter_error"
    ) -> FunctionScore:
        fn, variant = target[0], target[1]
        return FunctionScore(
            decompiler=dname,
            function_name=_subject_name(fn),
            compiler_variant=f"{variant.compiler} {variant.opt}",
            source_similarity=0.0,
            goto_count=0,
            nesting_depth=0,
            time_ms=0,
            error=message,
            semantic_error=message,
            fail_category=category,
            ged_metadata=_ged_provenance(target),
            binary=binary_rel,
            corpus=corpus_split,
            language=getattr(fn, "language", None) or "c",
            function_symbol=fn.name,
            project=getattr(fn, "project", "") or "",
        )

    try:
        binary_b64 = base64.b64encode(binary_path.read_bytes()).decode()
    except Exception as e:
        return [
            _failure_score(t, f"Failed to read binary: {e}") for t in targets
        ]

    # Post to batch endpoint under semaphore
    async with sem:
        try:
            timeout_key = (
                "BENCHMARK_"
                + dname.upper().replace("-", "_").replace(".", "_")
                + "_TIMEOUT_S"
            )
            default_timeout = 1800.0 if corpus_split == "scale" else 300.0
            timeout_s = float(
                os.environ.get(timeout_key)
                or os.environ.get("BENCHMARK_DECOMPILE_TIMEOUT_S")
                or default_timeout
            )
            resp = await client.post(
                f"{url}/decompile_batch",
                json={
                    "binary_b64": binary_b64,
                    "addresses": addresses,
                },
                timeout=timeout_s,
            )
            if resp.status_code != 200:
                raise RuntimeError(
                    f"HTTP status {resp.status_code}: {resp.text[:500]}"
                )
            data = resp.json()
            batch_results = data.get("results", [])
        except Exception as e:
            detail = f"{type(e).__name__}: {e}".strip()
            if detail in ("", ":", "Exception:", "Exception: "):
                detail = repr(e)
            err_msg = f"Batch decompile error: {detail}"
            return [
                _failure_score(t, err_msg) for t in targets
            ]

    # Map batch results back (normalize hex forms so 0x1400… vs 0X1400… match).
    def _addr_key(addr: object) -> str:
        text = str(addr or "").strip().lower()
        if not text:
            return ""
        try:
            return f"0x{int(text, 16):x}"
        except ValueError:
            return text

    results_by_addr = {_addr_key(item.get("addr")): item for item in batch_results}
    code_counts = Counter((item.get("code") or "").strip() for item in batch_results if (item.get("code") or "").strip())
    fn_scores = []

    # Ground-truth-based metrics (type_match, ged) both need every function's
    # decompiled text up front for this (binary, decompiler) batch: type_match
    # to calibrate one offset shift across the batch, ged to batch all
    # functions into a single Joern invocation (mirrors decbench's own
    # per-binary batching) instead of one parse call per function.
    decompiled_by_function: dict[str, str] = {}
    for fn, variant, _, _ged_src, _ged_basis in targets:
        item = results_by_addr.get(_addr_key(variant.addr))
        if not item:
            continue
        code = item.get("code", "") or ""
        code_nir = item.get("code_nir") or code or ""
        decompiled_by_function[fn.name] = code_nir

    # Type-match ground truth (DWARF) is per-binary, not per-function -- cached
    # across the whole run since many decompilers/batches share one binary.
    gt_types = ground_truth_for_binary(str(binary_path))
    type_match_shift: int | None = None
    if gt_types:
        type_match_shift = calibrate_binary_shift(gt_types, decompiled_by_function)

    # GED: one Joern parse for every function decompiled in this batch.
    decompiled_cfgs = extract_decompiled_cfgs(decompiled_by_function)

    for fn, variant, function_source, ged_source_path, ged_source_basis in targets:
        variant_label = f"{variant.compiler} {variant.opt}"
        item = results_by_addr.get(_addr_key(variant.addr))

        if not item:
            missing_score = _failure_score(
                (fn, variant, function_source, ged_source_path, ged_source_basis),
                "Address missing from batch result",
            )
            fn_scores.append(missing_score)
            if checkpoint is not None:
                checkpoint.append([missing_score])
            continue

        code = item.get("code", "") or ""
        # Dual layers (Fission): semantic on NIR; readability prefers HIR.
        code_nir = (item.get("code_nir") or code or "")
        code_hir = (item.get("code_hir") or "")
        # Semantic / diagnostics always use NIR-faithful primary.
        semantic_code = code_nir or code
        # Readability surface: HIR when present and non-empty, else primary.
        readability_code = code_hir or semantic_code
        adapter_error = item.get("error")
        output_diagnostics = (
            analyze_output_diagnostics(fn.name, dname, semantic_code, expected_addr=variant.addr)
            if semantic_code
            else {}
        )
        output_error = invalid_output_reason(
            output_diagnostics,
            semantic_code,
            duplicate_count=code_counts.get((code or "").strip(), 0),
        ) if semantic_code else None
        error = adapter_error or output_error
        sim = (
            source_similarity(function_source, semantic_code)
            if function_source and not error
            else 0.0
        )
        gotos, depth = structural_score(semantic_code) if not error else (0, 0)
        uses_intrin = check_uses_intrinsics(semantic_code) if semantic_code else False
        # Type correctness vs DWARF ground truth (None = no debug info / no GT
        # vars for this function, not a 0 score -- distinct from a real miss).
        type_match_metadata: dict[str, Any] = {}
        type_match_score: float | None = None
        gt_vars = gt_types.get(fn.name) if gt_types else None
        if gt_vars and semantic_code and not error:
            type_match_metadata = compute_type_match(
                gt_vars, semantic_code, fn.name, type_match_shift
            )
            type_match_score = type_match_metadata.get("accuracy")
        # Structural correctness: source CFG vs decompiled CFG edit distance
        # (lower is better; None = no CFG on one side, not a real 0 miss).
        try:
            ged_source_rel = str(
                ged_source_path.relative_to(CORPUS_ROOT / corpus_split)
            )
        except ValueError:
            ged_source_rel = str(ged_source_path)
        ged_metadata: dict[str, Any] = {
            "source_basis": ged_source_basis,
            "source_path": ged_source_rel,
            "source_contract": (
                "decbench-published-source-cfg-v1"
                if ged_source_basis == "published_source_cfg"
                else PREPROCESSED_TU_SCHEMA
            ),
        }
        ged_score: float | None = None
        if semantic_code and not error:
            source_cfgs = (
                load_published_source_cfgs(str(ged_source_path))
                if ged_source_basis == "published_source_cfg"
                else extract_source_cfgs(str(ged_source_path))
            )
            source_cfg = source_cfgs.get(fn.name)
            decompiled_cfg = decompiled_cfgs.get(fn.name)
            ged_metadata["source_cfg_available"] = source_cfg is not None
            ged_metadata["decompiled_cfg_available"] = decompiled_cfg is not None
            if source_cfg is not None and decompiled_cfg is not None:
                ged_metadata.update(compute_ged(source_cfg, decompiled_cfg))
                ged_score = ged_metadata.get("ged")
            elif source_cfg is None and decompiled_cfg is None:
                ged_metadata["error"] = "missing source and decompiled CFG"
            elif source_cfg is None:
                ged_metadata["error"] = "missing source CFG"
            else:
                ged_metadata["error"] = "missing decompiled CFG"
        else:
            ged_metadata["source_cfg_available"] = False
            ged_metadata["decompiled_cfg_available"] = False
        # Primary readability metrics: prefer HIR for Fission dual printers.
        readability_metrics = (
            analyze_readability(readability_code, dname)
            if readability_code and not error
            else {}
        )
        readability_score = summarize_readability_proxy_score(readability_metrics)
        readability_metrics_hir = {}
        readability_score_hir = None
        if (
            not error
            and code_hir
            and code_nir
            and code_hir.strip() != code_nir.strip()
        ):
            # Explicit HIR pass when dual surfaces differ (evidence only; not ranking).
            readability_metrics_hir = analyze_readability(code_hir, dname)
            readability_score_hir = summarize_readability_proxy_score(readability_metrics_hir)
        ast_similarity = (
            ast_structure_similarity(function_source, semantic_code)
            if function_source and semantic_code and not error
            else {}
        )

        oracle_evidence = {}
        lang = getattr(fn, "language", None) or "c"
        var_fmt = getattr(variant, "format", None) or ""
        var_isa = getattr(variant, "isa", None) or ""
        var_abi = getattr(variant, "abi_profile", None) or ""
        harness_blockers = output_diagnostics.get("harness_blockers") or []
        if harness_blockers:
            # Known-unrunnable output (e.g. Ghidra "Unknown calling convention"
            # dumps that declare named params but read raw `in_RCX`-style
            # register pseudo-locals in the body instead): naively compiling
            # and executing this as C reads uninitialized memory through
            # whatever garbage lands in those locals, which crashes the
            # oracle harness (a real wine page fault, not a semantic mismatch)
            # and poisons the whole envelope's oracle.valid aggregate. Skip
            # the compile-and-run attempt entirely; reuse the same
            # oracle_error + empty-evidence shape that
            # `_row_is_oracle_infra_failure_without_evidence` already
            # excludes from that aggregate.
            sem_score, sem_err, fail_cat, cases_passed, cases_total = (
                0.0,
                f"Skipped: decompiled output has harness blockers: {', '.join(harness_blockers)}",
                "oracle_error",
                0,
                0,
            )
        elif (getattr(fn, "semantic", None) or {}).get("mode") == "none":
            sem_score, sem_err, fail_cat, cases_passed, cases_total = (
                None,
                "External scale corpus has no executable semantic oracle",
                "no_wrapper",
                0,
                0,
            )
        elif not error and oracle_endpoint and fn.name in TEST_WRAPPERS:
            binary_bytes = binary_path.read_bytes()
            differential = await verify_with_oracle(
                client,
                oracle_endpoint,
                function_name=fn.name,
                reference_code=function_source,
                candidate_code=semantic_code,
                cases=TEST_WRAPPERS[fn.name],
                compiler_variant=variant_label,
                reference_binary_sha256=hashlib.sha256(binary_bytes).hexdigest(),
                # Bind oracle evidence to the corpus binary under test (PE or ELF).
                reference_binary_b64=base64.b64encode(binary_bytes).decode("ascii"),
                function_addr=variant.addr,
                target_abi=var_abi or None,
                binary_format=var_fmt or None,
            )
            sem_score = differential.score
            sem_err = differential.error
            fail_cat = differential.category
            cases_passed = differential.cases_passed
            cases_total = differential.cases_total
            oracle_evidence = differential.evidence or {}
        elif not error:
            sem_score, sem_err, fail_cat, cases_passed, cases_total = await verify_semantic_correctness_async(
                fn.name, semantic_code
            )
        else:
            sem_score, sem_err, fail_cat, cases_passed, cases_total = 0.0, error, "adapter_error", 0, 0

        # C-2: prefer per-item timing from adapter if provided, fall back to apportioned batch time.
        item_time_ms = item.get("time_ms")
        if item_time_ms is not None:
            fn_time_ms = int(item_time_ms)
        else:
            fn_time_ms = data.get("time_ms", 0) // max(len(targets), 1)

        bare = (
            try_bare_compile(semantic_code)
            if semantic_code and not error
            else {"ok": False, "category": "empty", "error": error or "no code"}
        )
        if error:
            recompilation_score, recompilation = measure_recompilation(
                "",
                function_name=fn.name,
                binary_path=binary_path,
                function_address=variant.addr,
                compiler_variant=variant_label,
            )
            if recompilation_score is not None:
                recompilation["category"] = "decompilation_error"
                recompilation["error"] = str(error)[:400]
        else:
            recompilation_score, recompilation = measure_recompilation(
                semantic_code,
                function_name=fn.name,
                binary_path=binary_path,
                function_address=variant.addr,
                compiler_variant=variant_label,
            )
        isa_fmt = classify_isa_format(
            binary_rel, isa=var_isa or None, fmt=var_fmt or None
        )
        track = classify_track(
            binary=binary_rel,
            function_name=_subject_name(fn),
            corpus=corpus_split,
            language=lang,
            fmt=isa_fmt.get("format"),
        )

        completed_score = FunctionScore(
            decompiler=dname,
            function_name=_subject_name(fn),
            compiler_variant=variant_label,
            source_similarity=sim,
            goto_count=gotos,
            nesting_depth=depth,
            time_ms=fn_time_ms,
            error=error,
            semantic_score=sem_score,
            semantic_error=sem_err,
            fail_category=fail_cat,
            cases_passed=cases_passed,
            cases_total=cases_total,
            uses_intrinsics=uses_intrin,
            decompiled_code=semantic_code[:8000] if semantic_code else "",
            decompiled_code_nir=code_nir[:8000] if code_nir else "",
            decompiled_code_hir=code_hir[:8000] if code_hir else "",
            pseudocode_layer=str(item.get("layer") or ""),
            readability_metrics=readability_metrics,
            readability_proxy_score=readability_score,
            readability_metrics_hir=readability_metrics_hir,
            readability_proxy_score_hir=readability_score_hir,
            ast_similarity=ast_similarity,
            type_match_score=type_match_score,
            type_match_metadata=type_match_metadata,
            ged_score=ged_score,
            ged_metadata=ged_metadata,
            recompilation_score=recompilation_score,
            recompilation=recompilation,
            output_diagnostics=output_diagnostics,
            oracle_evidence=oracle_evidence,
            bare_compile=bare,
            track=track,
            language=lang,
            isa_format=isa_fmt,
            binary=binary_rel,
            corpus=corpus_split,
        )
        fn_scores.append(completed_score)
        # Persist at function granularity, not merely when the whole binary
        # batch returns, so an interruption loses at most the active function.
        if checkpoint is not None:
            checkpoint.append([completed_score])

        # Direct feedback output
        status = "✓" if not error else "✗"
        cat_tag = f" [{fail_cat}]" if fail_cat else ""
        sem_text = format_semantic_score(sem_score)
        typer.echo(
            f"  {status} {dname:10s} {_subject_name(fn):15s} [{variant_label}] "
            f"sim={sim:.3f} sem={sem_text} ({cases_passed}/{cases_total} cases){cat_tag} gotos={gotos}"
        )

    return fn_scores


def load_function_source_text(source_path: Path) -> str:
    """Read corpus source text for similarity scoring.

    Manifests normally point at a single file (e.g. ``source/c/foo.c``).
    Multi-file language packages (Go CGO module dir with ``main.go``) may
    point at a directory — resolve to a readable text blob instead of
    raising ``IsADirectoryError``.
    """
    if not source_path.exists():
        return ""
    if source_path.is_file():
        return source_path.read_text(errors="replace")
    if not source_path.is_dir():
        return ""

    # Prefer conventional entry files, then concatenate remaining sources.
    preferred_names = (
        "main.go",
        "main.c",
        "main.cpp",
        "lib.rs",
        "mod.rs",
        "main.rs",
    )
    for name in preferred_names:
        candidate = source_path / name
        if candidate.is_file():
            return candidate.read_text(errors="replace")

    chunks: list[str] = []
    for path in sorted(source_path.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".c", ".cc", ".cpp", ".h", ".hpp", ".go", ".rs", ".s"}:
            continue
        try:
            chunks.append(path.read_text(errors="replace"))
        except OSError:
            continue
    return "\n\n".join(chunks)


async def run_all(
    functions: list,
    decompilers: dict[str, str],
    corpus_split: str,
    limit: int | None,
    variant_limit: int | None,
    oracle_endpoint: str | None,
    checkpoint: BenchmarkCheckpoint | None = None,
) -> list[FunctionScore]:
    fn_list = functions  # [:limit] already applied by caller — do not slice again
    all_scores: list[FunctionScore] = (
        checkpoint.recovered_rows if checkpoint is not None else []
    )

    # 1. Group decompile requests by (decompiler, binary_path)
    groups = {}
    for fn in fn_list:
        source_path = CORPUS_ROOT / corpus_split / fn.source
        source_code = load_function_source_text(source_path)
        function_source = extract_function_source(source_code, fn.name) or source_code

        variants = fn.compiler_variants[:variant_limit] if variant_limit else fn.compiler_variants
        for variant in variants:
            binary_path = CORPUS_ROOT / corpus_split / variant.binary
            published_source_cfg = str(getattr(variant, "source_cfg", "") or "")
            preprocessed_source = str(
                getattr(variant, "preprocessed_source", "") or ""
            )
            candidate_ged_source = (
                CORPUS_ROOT / corpus_split / preprocessed_source
                if preprocessed_source
                else source_path
            )
            if published_source_cfg:
                ged_source_path = CORPUS_ROOT / corpus_split / published_source_cfg
                ged_source_basis = "published_source_cfg"
            elif preprocessed_source and candidate_ged_source.is_file():
                ged_source_path = candidate_ged_source
                ged_source_basis = "preprocessed_tu"
            else:
                ged_source_path = source_path
                ged_source_basis = "authored_source_fallback"
            if not binary_path.exists():
                missing_rows = []
                for dname in decompilers:
                    key = (dname, _subject_name(fn), f"{variant.compiler} {variant.opt}")
                    if checkpoint is not None and checkpoint.contains(key):
                        continue
                    missing_rows.append(FunctionScore(
                        decompiler=dname,
                        function_name=_subject_name(fn),
                        compiler_variant=f"{variant.compiler} {variant.opt}",
                        source_similarity=0.0,
                        goto_count=0,
                        nesting_depth=0,
                        time_ms=0,
                        error=f"Missing binary: {variant.binary}",
                        semantic_error=f"Missing binary: {variant.binary}",
                        fail_category="fixture_error",
                        function_symbol=fn.name,
                        project=getattr(fn, "project", "") or "",
                    ))
                all_scores.extend(missing_rows)
                if checkpoint is not None:
                    checkpoint.append(missing_rows)
                continue

            for dname, url in decompilers.items():
                key = (dname, _subject_name(fn), f"{variant.compiler} {variant.opt}")
                if checkpoint is not None and checkpoint.contains(key):
                    continue
                key = (dname, url, binary_path)
                if key not in groups:
                    groups[key] = []
                groups[key].append(
                    (
                        fn,
                        variant,
                        function_source,
                        ged_source_path,
                        ged_source_basis,
                    )
                )

    # HTTP decompile batches are I/O-bound (work runs in containers). Prefer an
    # explicit BENCHMARK_HTTP_CONCURRENCY override in CI; otherwise scale past
    # cpu_count so multiple adapters can be in-flight on small runners.
    env_conc = os.environ.get("BENCHMARK_HTTP_CONCURRENCY", "").strip()
    if env_conc.isdigit() and int(env_conc) > 0:
        concurrency = int(env_conc)
    else:
        concurrency = max((os.cpu_count() or 4) * 2, 8)
    sem = asyncio.Semaphore(concurrency)
    typer.echo(f"Starting batch benchmark run with concurrency limit of {concurrency} workers.")

    async with httpx.AsyncClient() as client:
        tasks = []
        for (dname, url, binary_path), targets in groups.items():
            tasks.append(
                decompile_batch_and_score(
                    client,
                    dname,
                    url,
                    binary_path,
                    targets,
                    sem,
                    oracle_endpoint,
                    corpus_split=corpus_split,
                    checkpoint=checkpoint,
                )
            )

        for task in asyncio.as_completed(tasks):
            rows = await task
            all_scores.extend(rows)
            if checkpoint is not None:
                checkpoint.append(rows)

    return assign_consensus_ranks(
        all_scores,
        source_goto_counts=SOURCE_GOTO_COUNTS,
        source_nesting_depths=SOURCE_NESTING_DEPTHS,
    )


@app.command()
def run(
    corpus: str = typer.Option(
        "dev", "--corpus", help="Which corpus split to evaluate (e.g. dev, holdout)"
    ),
    limit: int | None = typer.Option(
        None, help="Limit number of functions evaluated (for testing)"
    ),
    variant_limit: int | None = typer.Option(
        None, help="Limit compiler variants evaluated per function (for testing)"
    ),
    function: str | None = typer.Option(
        None, help="Evaluate only a specific function by name"
    ),
    decompilers: str | None = typer.Option(
        None, help="Comma-separated list of decompilers to run"
    ),
    output: str | None = typer.Option(
        None, help="Path to save JSON output (defaults to results/TIMESTAMP.json)"
    ),
    run_mode: str = typer.Option(
        "smoke", help="Execution mode: smoke, local, or official"
    ),
    profile: str | None = typer.Option(
        None,
        "--profile",
        help="Corpus matrix profile from corpus/matrix/profiles.yaml "
        "(or set BENCHMARK_PROFILE). Filters language/opt/isa/function slices.",
    ),
    checkpoint_file: str | None = typer.Option(
        None,
        "--checkpoint",
        help="Append-only row checkpoint path (content-addressed default under .cache)",
    ),
    resume: bool = typer.Option(
        True,
        "--resume/--no-resume",
        help="Reuse rows from a matching checkpoint, or start the checkpoint anew",
    ),
) -> None:
    """Run benchmark evaluation pipeline."""
    started_at = datetime.now(timezone.utc)
    start_monotonic = time.monotonic()
    _load_source_metrics()

    if run_mode == "official" and any((limit, variant_limit, function)):
        raise typer.BadParameter(
            "official runs cannot use --limit, --variant-limit, or --function"
        )

    from matrix_profile import (
        get_profile,
        resolve_profile_name,
        validate_release_contract,
    )

    profile_name = resolve_profile_name(profile)
    profile_cfg = None
    if profile_name:
        try:
            profile_cfg = get_profile(profile_name)
        except KeyError as exc:
            raise typer.BadParameter(str(exc), param_hint="--profile") from exc

    # Select decompilers
    all_dec = configured_decompilers()
    if decompilers:
        selected = [d.strip() for d in decompilers.split(",")]
        dec_map = {}
        for d in selected:
            if d not in all_dec:
                raise typer.BadParameter(f"Requested decompiler '{d}' is not configured or is skipped.")
            dec_map[d] = all_dec[d]
    else:
        if profile_cfg and profile_cfg.get("decompilers_default"):
            selected = [
                d.strip()
                for d in str(profile_cfg["decompilers_default"]).split(",")
                if d.strip()
            ]
            dec_map = {d: all_dec[d] for d in selected if d in all_dec}
            if not dec_map:
                dec_map = all_dec
        else:
            dec_map = all_dec

    typer.echo(f"Using decompilers: {list(dec_map.keys())}")
    if profile_name:
        typer.echo(f"Corpus profile: {profile_name}")

    # Load corpus using load_all, then apply matrix profile filters.
    c = Corpus.load_all(corpus)
    if profile_name:
        c = c.apply_profile(profile_name)
    try:
        selected_functions = filter_functions(c.functions, function)
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--function") from exc
    typer.echo(f"Loading corpus: {corpus}")
    typer.echo(f"  {len(c.functions)} functions after profile filter")
    if function:
        typer.echo(
            "  focused functions: "
            + ", ".join(_subject_name(fn) for fn in selected_functions)
        )
    if limit:
        typer.echo(f"  function limit: {limit}")
    if variant_limit:
        typer.echo(f"  variant limit per function: {variant_limit}")

    fn_list = selected_functions[:limit] if limit else selected_functions
    expected_functions = len(fn_list)

    release_contract = None
    if run_mode == "official":
        if not profile_cfg:
            raise typer.BadParameter(
                "official runs require a matrix profile with a release_contract",
                param_hint="--profile",
            )
        try:
            release_contract = validate_release_contract(
                profile_name,
                profile_cfg,
                fn_list,
                list(dec_map),
            )
        except ValueError as exc:
            raise typer.BadParameter(str(exc), param_hint="--profile") from exc
        if release_contract is None:
            raise typer.BadParameter(
                f"profile {profile_name!r} has no release_contract",
                param_hint="--profile",
            )
        typer.echo(
            "Release contract: "
            f"{release_contract['id']} "
            f"({release_contract['subject_count']} subjects / "
            f"{release_contract['row_count']} rows)"
        )

    # Build exact expected_cells list (per function x variant x decompiler)
    # Avoids Cartesian product assumptions when functions have different variants.
    expected_cells = build_expected_cells(fn_list, list(dec_map), variant_limit)

    expected_rows = len(expected_cells)

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        commit = "unknown"
    manifest_hash = hashlib.sha256()
    manifest_paths = sorted((CORPUS_ROOT / corpus / "manifests").glob("*.json"))
    for manifest_path in manifest_paths:
        manifest_hash.update(manifest_path.name.encode("utf-8"))
        manifest_hash.update(manifest_path.read_bytes())
    runner_source_hash = hashlib.sha256()
    for source_file in sorted(Path(__file__).parent.glob("*.py")):
        runner_source_hash.update(source_file.name.encode("utf-8"))
        runner_source_hash.update(source_file.read_bytes())
    external_dataset = None
    if corpus == "scale":
        inventory_path = CORPUS_ROOT / corpus / "inventory.json"
        try:
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise typer.BadParameter(
                "scale corpus inventory is missing or invalid; run "
                "scripts/materialize_scale_corpus.py first",
                param_hint="--corpus",
            ) from exc
        external_dataset = {
            "schema": str(inventory.get("schema") or ""),
            "name": str(inventory.get("dataset") or ""),
            "repository": str(inventory.get("repository") or ""),
            "revision": str(inventory.get("revision") or ""),
            "license": str(inventory.get("license") or ""),
            "config": str(inventory.get("config") or ""),
            "selected_binaries": int(inventory.get("selected_binaries") or 0),
            "requested_functions": int(inventory.get("requested_functions") or 0),
            "resolved_functions": int(inventory.get("resolved_functions") or 0),
            "source_cfg_functions": int(inventory.get("source_cfg_functions") or 0),
            "source_cfg_coverage": float(inventory.get("source_cfg_coverage") or 0),
            "malware_included": bool(inventory.get("malware_included")),
        }
    checkpoint_contract = {
        "schema": CHECKPOINT_SCHEMA,
        "corpus": corpus,
        "corpus_manifest_sha256": manifest_hash.hexdigest(),
        "runner_commit": commit,
        "runner_source_sha256": runner_source_hash.hexdigest(),
        "toolchain": fission_toolchain_metadata(),
        "run_mode": run_mode,
        "matrix_profile": profile_name,
        "release_contract_id": (release_contract or {}).get("id"),
        "expected_cells": expected_cells,
    }
    checkpoint_digest = hashlib.sha256(
        json.dumps(
            checkpoint_contract, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    checkpoint_path = (
        Path(checkpoint_file)
        if checkpoint_file
        else Path(__file__).resolve().parents[1]
        / ".cache"
        / "benchmark-checkpoints"
        / f"{checkpoint_digest}.jsonl"
    )
    try:
        checkpoint_store = BenchmarkCheckpoint(
            checkpoint_path,
            contract=checkpoint_contract,
            reset=not resume,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="--checkpoint") from exc
    recovered_rows = len(checkpoint_store.recovered_rows)
    if recovered_rows:
        typer.echo(f"Resuming {recovered_rows}/{expected_rows} completed rows")

    # Run event loop
    oracle_endpoint = os.environ.get("ORACLE_ENDPOINT")
    if run_mode == "official" and not oracle_endpoint:
        raise typer.BadParameter("official runs require ORACLE_ENDPOINT")
    scores = asyncio.run(
        run_all(
            fn_list,
            dec_map,
            corpus,
            limit,
            variant_limit,
            oracle_endpoint,
            checkpoint_store,
        )
    )

    elapsed = time.monotonic() - start_monotonic
    finished_at = datetime.now(timezone.utc)

    # Save JSON and generate report
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    # Save definitive run results
    if output:
        json_path = Path(output)
    else:
        json_path = results_dir / f"{timestamp}.json"
    serialized = [asdict(s) for s in scores]
    
    oracle = aggregate_oracle_evidence(serialized)

    envelope = build_envelope(
        serialized,
        run_meta={
            "run_id": str(uuid.uuid4()),
            "started_at": started_at.isoformat().replace("+00:00", "Z"),
            "finished_at": finished_at.isoformat().replace("+00:00", "Z"),
            "duration_ms": round(elapsed * 1000),
            "runner_commit": commit,
            "corpus": corpus,
            "corpus_manifest_sha256": manifest_hash.hexdigest(),
            "official": run_mode == "official",
            "requested_run_mode": run_mode,
            # Official publication requires profile=realistic with no focus limits.
            "profile": "realistic" if run_mode == "official" else "diagnostic",
            "matrix_profile": profile_name,
            "release_contract": release_contract,
            "measurement_contracts": {
                "source_cfg": (
                    "decbench-published-source-cfg-v1"
                    if corpus == "scale"
                    else PREPROCESSED_TU_SCHEMA
                ),
                "checkpoint": CHECKPOINT_SCHEMA,
                "metric_cache": CACHE_SCHEMA,
                "ged_cache_version": "v2-preprocessed-tu",
                "recompilation_cache_version": "v1",
                "dashboard_health": "measurement-health-v1",
            },
            "checkpoint": {
                "schema": CHECKPOINT_SCHEMA,
                "contract_sha256": checkpoint_store.contract_sha256,
                "recovered_rows": recovered_rows,
            },
            **(
                {"external_dataset": external_dataset}
                if external_dataset is not None
                else {}
            ),
            "limits": {
                "limit": limit,
                "variant_limit": variant_limit,
                "function": function,
                "matrix_profile": profile_name,
            }
        },
        toolchain={
            **fission_toolchain_metadata(),
            "runner_commit": commit,
            "runner_os": sys.platform,
            "python_version": sys.version.split()[0],
            "ci": os.environ.get("CI", "false"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "github_actor": os.environ.get("GITHUB_ACTOR", ""),
            "host": _host_fingerprint(),
        },
        matrix={
            "expected_decompilers": list(dec_map.keys()),
            "expected_functions": expected_functions,
            "expected_rows": expected_rows,
            "expected_cells": expected_cells,
            "observed_rows": len(serialized),
        },
        oracle=oracle,
    )

    json_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")

    typer.echo(f"\n✅ Results saved to {json_path} ({elapsed:.1f}s)")
    typer.echo("Candidate result saved; publication requires runner/publication_gate.py.")


if __name__ == "__main__":
    app()
