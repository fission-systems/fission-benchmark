"""Score one binary: strip -> decompile with Fission -> grade with DecBench metrics.

Mirrors DecBench's compile -> decompile -> evaluate pipeline, but the
"compile" step is already done (the published DecBench dataset ships the
binaries, their DWARF, and the source CFGs), and only Fission is run.

Honesty rules (same as the DecBench leaderboard):

* Fission only ever sees a *stripped* copy. Decompiling the original would hand
  it the DWARF answer key. Names/types are taken from the original afterwards,
  by address, purely for grading.
* The denominator is fixed by the source: every function that has both a symbol
  in the original and a published source CFG. A function Fission fails to
  produce counts as a miss, never silently dropped.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

METRICS = ("ged", "type_match", "byte_match")
# A function is "perfect" on a metric when it reaches this value.
PERFECT = {"ged": 0.0, "type_match": 1.0, "byte_match": 1.0}
SCHEMA_VERSION = 1

_DECLARATOR = re.compile(r"([A-Za-z_]\w*)\s*\([^()]*\)\s*$")


@dataclass(frozen=True)
class Job:
    opt: str
    project: str
    binary: str
    path: str  # original (unstripped) binary
    cfg_path: str  # published source CFG json
    out_path: str  # per-binary result json
    fission_cli: str
    layer: str = "nir"
    metrics: tuple[str, ...] = METRICS
    binary_timeout_s: int = 3600
    function_timeout_ms: int = 45000

    @property
    def key(self) -> str:
        return f"{self.opt}/{self.project}/{self.binary}"


def find_fission_cli(explicit: str | None = None) -> str | None:
    for cand in (
        explicit,
        os.environ.get("FISSION_CLI"),
        str(Path.home() / "Fission" / "target" / "release" / "fission_cli"),
        shutil.which("fission_cli"),
    ):
        if cand and Path(cand).is_file():
            return cand
    return None


def fission_version(cli: str) -> str:
    try:
        p = subprocess.run([cli, "--version"], capture_output=True, text=True, timeout=30)
        m = re.search(r"\d+\.\d+\.\d+\S*", p.stdout + p.stderr)
        return m.group(0) if m else "unknown"
    except Exception:  # noqa: BLE001
        return "unknown"


def symbol_table(binary: Path) -> dict[int, str]:
    """``{address: name}`` for defined text symbols of the *original* binary."""
    nm = shutil.which("llvm-nm") or shutil.which("nm")
    if not nm:
        raise RuntimeError("llvm-nm/nm not found")
    out = subprocess.run(
        [nm, "--defined-only", str(binary)], capture_output=True, text=True
    ).stdout
    table: dict[int, str] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[1] in ("t", "T"):
            try:
                table.setdefault(int(parts[0], 16), parts[2])
            except ValueError:
                continue
    return table


def strip_copy(binary: Path, dest_dir: Path) -> Path:
    stripper = shutil.which("llvm-strip") or shutil.which("strip")
    if not stripper:
        raise RuntimeError("llvm-strip/strip not found")
    dst = dest_dir / binary.name
    shutil.copy2(binary, dst)
    proc = subprocess.run([stripper, "--strip-all", str(dst)], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"strip failed: {proc.stderr.strip()[:200]}")
    return dst


def declared_name(code: str) -> str | None:
    """Name on the line right before the function body's lone ``{``."""
    lines = code.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "{" and i > 0:
            m = _DECLARATOR.search(lines[i - 1].strip())
            return m.group(1) if m else None
    return None


def run_fission(job: Job, stripped: Path) -> list[dict[str, Any]]:
    cmd = [
        job.fission_cli, "decomp", str(stripped), "--all", "--layer", job.layer,
        "--json", "--no-header", "--no-warnings",
        "--timeout-ms", str(job.function_timeout_ms),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=job.binary_timeout_s)
    out = (proc.stdout or "").strip()
    if not out:
        tail = (proc.stderr or "").strip().splitlines()[-3:]
        raise RuntimeError(f"empty output (exit {proc.returncode}): {' | '.join(tail)}")
    payload = json.loads(out[out.index("[") :] if "[" in out else out)
    return payload if isinstance(payload, list) else [payload]


def _finite(v: float | None) -> float | None:
    return v if v is not None and math.isfinite(v) else None


def score_binary(job: Job) -> dict[str, Any]:
    """Run one binary end to end and write ``job.out_path``. Never raises."""
    t0 = time.time()
    result: dict[str, Any] = {
        "schema": SCHEMA_VERSION, "opt": job.opt, "project": job.project,
        "binary": job.binary, "layer": job.layer, "status": "ok", "error": None,
        "targets": 0, "produced": 0, "functions": {},
    }
    try:
        _score(job, result)
    except subprocess.TimeoutExpired:
        result.update(status="timeout", error=f"fission timed out after {job.binary_timeout_s}s")
    except Exception as exc:  # noqa: BLE001
        result.update(status="error", error=f"{type(exc).__name__}: {exc}"[:500])
    result["seconds"] = round(time.time() - t0, 2)
    out = Path(job.out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(result), encoding="utf-8")
    tmp.replace(out)
    return result


def _score(job: Job, result: dict[str, Any]) -> None:
    # Imported lazily: heavy, and only needed inside worker processes.
    from decbench.models.decompilation import (
        DecompilationResult, DecompilerMetadata, FunctionDecompilation,
    )
    from decbench.pipeline.evaluate import evaluate_decompilation
    from decbench.publish.cfg_export import rebuild_cfg

    original = Path(job.path)
    cfg_payload = json.loads(Path(job.cfg_path).read_text(encoding="utf-8"))
    source_cfgs = {n: rebuild_cfg(fc) for n, fc in (cfg_payload.get("functions") or {}).items()}
    syms = symbol_table(original)
    names = set(syms.values())
    targets = {n for n in source_cfgs if n in names}
    result["targets"] = len(targets)
    result["functions"] = {n: {} for n in sorted(targets)}
    if not targets:
        result.update(status="no_targets", error="no function has both a symbol and a source CFG")
        return

    with tempfile.TemporaryDirectory(prefix="fbench-") as tmp:
        stripped = strip_copy(original, Path(tmp))
        start = time.time()
        records = run_fission(job, stripped)
        decomp_s = time.time() - start

    funcs: dict[str, FunctionDecompilation] = {}
    for rec in records:
        code = rec.get("code") or ""
        try:
            addr = int(str(rec.get("address")), 0)
        except (TypeError, ValueError):
            continue
        real = syms.get(addr)
        if not code or real not in targets or real in funcs:
            continue
        emitted = declared_name(code)
        if emitted and emitted != real:
            code = re.sub(rf"\b{re.escape(emitted)}\b", real, code)
        funcs[real] = FunctionDecompilation(
            name=real, address=addr, decompiled_code=code, line_count=code.count("\n") + 1,
            variables=_variables(rec),
        )
    result["produced"] = len(funcs)
    for n in funcs:
        result["functions"][n]["produced"] = True
    result["decompile_seconds"] = round(decomp_s, 2)
    if not funcs:
        result.update(status="no_output", error="fission produced none of the target functions")
        return

    dec = DecompilationResult(
        binary_path=original, binary_name=original.stem,
        decompiler=DecompilerMetadata(
            decompiler_name="fission", decompiler_version=fission_version(job.fission_cli),
            total_time_seconds=decomp_s, timeout_occurred=False, failed_functions=[],
            extra={"layer": job.layer},
        ),
        functions=funcs,
    )
    evaluated = evaluate_decompilation(dec, source_cfgs, list(job.metrics))
    metric_errors: dict[str, str] = {}
    for metric, mres in evaluated.items():
        if mres.errors and not mres.function_results:
            metric_errors[metric] = "; ".join(mres.errors)[:300]
        for name, mv in mres.function_results.items():
            if name in result["functions"]:
                result["functions"][name][metric] = _finite(mv.value)
    if metric_errors:
        result["metric_errors"] = metric_errors


def _variables(rec: dict[str, Any]) -> list[Any]:
    from decbench.models.decompilation import VariableInfo

    out = []
    for e in rec.get("variables") or ():
        if isinstance(e, dict):
            out.append(VariableInfo(
                name=str(e.get("name") or ""), type=str(e.get("type") or ""),
                stack_offset=e.get("stack_offset"), size=e.get("size"),
                kind=e.get("kind") or "stack", arg_index=e.get("arg_index"),
            ))
    return out
