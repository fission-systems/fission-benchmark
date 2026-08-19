"""Bare-compile diagnostic: can decompiled C compile with minimal harness?

This is intentionally **not** a ranking axis. Semantic correctness uses the
original_binary oracle (full harness + cases). Bare-compile measures whether
the emitted function is close to stand-alone C for the host gcc.

Uses ``gcc -c`` (compile only, no link) so a function body without ``main`` is OK.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping

# Minimal stdint-only surface — no full decompiler typedef soup, no test wrappers.
BARE_HEADER = """\
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
typedef unsigned char uchar;
typedef unsigned short ushort;
typedef unsigned int uint;
typedef unsigned long ulong;
typedef unsigned long long ulonglong;
typedef long long longlong;
typedef int8_t undefined1;
typedef int16_t undefined2;
typedef int32_t undefined4;
typedef int64_t undefined8;
typedef int32_t undefined;
typedef uint8_t byte;
typedef uint16_t word;
typedef uint32_t dword;
typedef uint64_t qword;
"""

# Common SLEIGH intrinsics as weak no-ops so bare compile focuses on C shape.
BARE_INTRINSICS = """\
static inline int __carry(long long a, long long b) { (void)a; (void)b; return 0; }
static inline int __scarry(long long a, long long b) { (void)a; (void)b; return 0; }
static inline int __sborrow(long long a, long long b) { (void)a; (void)b; return 0; }
static inline int __borrow(long long a, long long b) { (void)a; (void)b; return 0; }
static inline int __popcount(unsigned int x) { return __builtin_popcount(x); }
"""


def _strip_leading_includes(code: str) -> str:
    lines = []
    for line in code.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#include"):
            continue
        lines.append(line)
    return "\n".join(lines)


def build_bare_tu(decompiled_code: str) -> str:
    body = _strip_leading_includes(decompiled_code or "")
    return "\n".join([BARE_HEADER, BARE_INTRINSICS, body, ""])


def try_bare_compile(decompiled_code: str, *, timeout_s: float = 5.0) -> dict[str, Any]:
    """Return diagnostic dict: ok, category, error excerpt."""
    if not (decompiled_code or "").strip():
        return {
            "ok": False,
            "category": "empty",
            "error": "empty decompilation",
            "compiler": "gcc",
            "mode": "gcc -c -w -O0",
        }

    source = build_bare_tu(decompiled_code)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "bare.c"
        obj = Path(tmp) / "bare.o"
        src.write_text(source, encoding="utf-8")
        try:
            proc = subprocess.run(
                ["gcc", "-c", "-w", "-O0", "-std=c11", str(src), "-o", str(obj)],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "category": "timeout",
                "error": "bare compile timeout",
                "compiler": "gcc",
                "mode": "gcc -c -w -O0",
            }
        except FileNotFoundError:
            return {
                "ok": False,
                "category": "toolchain_missing",
                "error": "gcc not found",
                "compiler": "gcc",
                "mode": "gcc -c -w -O0",
            }

        if proc.returncode == 0:
            return {
                "ok": True,
                "category": "ok",
                "error": None,
                "compiler": "gcc",
                "mode": "gcc -c -w -O0",
            }

        err = (proc.stderr or proc.stdout or "").strip()
        # Collapse whitespace for storage.
        err = re.sub(r"\s+", " ", err)[:400]

        # BARE_HEADER only covers what someone thought to list. When it does
        # not, fall back to the diagnostic-driven repair, which injects exactly
        # what gcc says is missing. Measured on the 432 committed rows: 18
        # functions compile this way that scored 0 before, 17 of them Ghidra's
        # (`Kv`, `Pair`, `ConfigNode`, `in_RCX` -- names the header never had),
        # and 0 regressed. A header tuned to one decompiler's output is a
        # measurement tilted toward it.
        try:
            from .fixup import compile_with_fixup  # type: ignore[import-not-found]
        except ImportError:  # pragma: no cover - direct-script import path
            from fixup import compile_with_fixup  # type: ignore[no-redef]
        try:
            fix = compile_with_fixup(decompiled_code, "bare")
        except Exception:  # a repair failure must not lose the real diagnosis
            fix = None
        if fix is not None and fix.obj_path is not None:
            try:
                fix.obj_path.unlink()
            except OSError:
                pass
            return {
                "ok": True,
                "category": "ok_after_fixup",
                "error": None,
                "compiler": "gcc",
                "mode": "gcc -c (diagnostic-driven fixup)",
                "fixup_iterations": fix.iterations,
                "fixup_injected": len(fix.injected),
            }

        return {
            "ok": False,
            "category": "compile_error",
            "error": err or "bare compile failed",
            "compiler": "gcc",
            "mode": "gcc -c -w -O0",
        }


def classify_track(
    *,
    binary: str | None = None,
    function_name: str | None = None,
    corpus: str | None = None,
    language: str | None = None,
    fmt: str | None = None,
) -> str:
    """Coarse track label for extension pivots (not ranking)."""
    blob = " ".join(
        part for part in (binary or "", function_name or "", corpus or "") if part
    ).lower()
    if "adversarial" in blob or "cff_" in blob:
        return "adversarial"
    if "realworld" in blob or function_name in {
        "util_hash",
        "util_clamp",
        "util_count_bits",
        "app_process",
    }:
        return "realworld"
    if (
        "multi_isa" in blob
        or blob.endswith("hello_elf_x86_64")
        or "/elf" in blob
        or "gcc-elf" in blob
        or "gcc-aarch64" in blob
        or "aarch64" in blob
        or (fmt or "").lower() == "elf"
    ):
        return "multi_isa"
    lang = (language or "").lower()
    if lang in {"cpp", "c++"}:
        return "lang_cpp"
    if lang == "rust":
        return "lang_rust"
    if lang == "go":
        return "lang_go"
    if "holdout" in blob or (corpus or "") == "holdout":
        return "holdout"
    return "dev"


def classify_isa_format(
    binary: str | None,
    *,
    isa: str | None = None,
    fmt: str | None = None,
) -> dict[str, str]:
    """ISA/format tag: prefer explicit variant fields, else path heuristics."""
    if isa and fmt:
        return {"isa": isa, "format": fmt}
    name = (binary or "").lower()
    if fmt:
        resolved_fmt = fmt
    elif name.endswith(".exe") or name.endswith(".dll"):
        resolved_fmt = "pe"
    elif "elf" in name or "gcc-elf" in name or "aarch64" in name:
        resolved_fmt = "elf"
    elif name and not name.endswith((".exe", ".dll", ".o")):
        # Bare path under binaries/c/... without .exe often means ELF.
        resolved_fmt = "elf" if "binaries/" in name.replace("\\", "/") else "unknown"
    else:
        resolved_fmt = "unknown"

    if isa:
        resolved_isa = isa
    elif "m32" in name or "i686" in name or "x86_32" in name:
        resolved_isa = "x86_32"
    elif "arm64" in name or "aarch64" in name:
        resolved_isa = "aarch64"
    elif "x86_64" in name or "x64" in name or name.endswith(".exe"):
        resolved_isa = "x86_64"
    else:
        resolved_isa = "unknown"
    return {"isa": resolved_isa, "format": resolved_fmt}


def aggregate_bare_compile(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Per-decompiler bare-compile rates (diagnostic only)."""
    by_tool: dict[str, dict[str, int]] = {}
    for row in rows:
        tool = str(row.get("decompiler") or "unknown")
        slot = by_tool.setdefault(
            tool, {"attempted": 0, "ok": 0, "fail": 0, "skipped": 0}
        )
        bare = row.get("bare_compile") or {}
        if not bare:
            # Legacy rows without the field.
            if row.get("error") or not (row.get("decompiled_code") or "").strip():
                slot["skipped"] += 1
            else:
                slot["attempted"] += 1
                slot["fail"] += 1
            continue
        if bare.get("category") in {"empty", "toolchain_missing"}:
            slot["skipped"] += 1
            continue
        slot["attempted"] += 1
        if bare.get("ok"):
            slot["ok"] += 1
        else:
            slot["fail"] += 1

    out: dict[str, Any] = {}
    for tool, counts in sorted(by_tool.items()):
        attempted = counts["attempted"]
        out[tool] = {
            **counts,
            "ok_rate": round(counts["ok"] / attempted, 4) if attempted else None,
        }
    return {
        "ranking": False,
        "note": "Bare-compile is a form-quality diagnostic; not used for semantic ranking.",
        "by_decompiler": out,
    }


def aggregate_readability_axis(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate goto / temp / flag-soup style proxies (non-ranking)."""
    by_tool: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        tool = str(row.get("decompiler") or "unknown")
        metrics = row.get("readability_metrics") or {}
        if not metrics and not row.get("goto_count"):
            continue
        slot = by_tool.setdefault(
            tool,
            {
                "goto": [],
                "temp_loc_ratio": [],
                "flag_soup": [],
                "proxy": [],
                "nesting": [],
            },
        )
        goto = row.get("goto_count")
        if isinstance(goto, (int, float)):
            slot["goto"].append(float(goto))
        nesting = row.get("nesting_depth")
        if isinstance(nesting, (int, float)):
            slot["nesting"].append(float(nesting))
        scf = (metrics.get("structured_control_flow") or {}).get("raw") or {}
        if isinstance(scf.get("goto_count"), (int, float)):
            slot["goto"].append(float(scf["goto_count"]))
        expr = (metrics.get("expression_complexity") or {}).get("raw") or {}
        if isinstance(expr.get("temporary_identifier_loc_ratio"), (int, float)):
            slot["temp_loc_ratio"].append(float(expr["temporary_identifier_loc_ratio"]))
        # Flag soup: count of common condition-flag identifiers in decompiled text.
        code = row.get("decompiled_code") or ""
        if code:
            flags = len(re.findall(r"\b(?:zf|sf|cf|of|pf|af)\b", code, flags=re.I))
            loc = max(code.count("\n") + 1, 1)
            slot["flag_soup"].append(flags / loc)
        proxy = row.get("readability_proxy_score")
        if isinstance(proxy, (int, float)):
            slot["proxy"].append(float(proxy))

    def _mean(xs: list[float]) -> float | None:
        return round(sum(xs) / len(xs), 4) if xs else None

    by_decompiler: dict[str, Any] = {}
    for tool, series in sorted(by_tool.items()):
        by_decompiler[tool] = {
            "rows": max(len(v) for v in series.values()) if series else 0,
            "mean_goto_count": _mean(series["goto"]),
            "mean_temp_loc_ratio": _mean(series["temp_loc_ratio"]),
            "mean_flag_soup_per_loc": _mean(series["flag_soup"]),
            "mean_nesting_depth": _mean(series["nesting"]),
            "mean_readability_proxy": _mean(series["proxy"]),
        }
    return {
        "ranking": False,
        "note": (
            "Readability proxies (goto, temp density, flag soup) are diagnostics only. "
            "No composite readability rank is published."
        ),
        "by_decompiler": by_decompiler,
    }


def aggregate_track_taxonomy(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Semantic pass + fail taxonomy pivoted by track / language / isa / format / opt."""
    from collections import defaultdict

    try:
        from .standard_summary import normalize_fail_taxonomy
    except ImportError:
        from standard_summary import normalize_fail_taxonomy

    track_rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    lang_rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    isa_rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    fmt_rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    opt_rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)

    for row in rows:
        lang = str(row.get("language") or "c")
        isa_fmt = row.get("isa_format") or classify_isa_format(str(row.get("binary") or ""))
        track = str(
            row.get("track")
            or classify_track(
                binary=str(row.get("binary") or ""),
                function_name=str(row.get("function_name") or ""),
                corpus=str(row.get("corpus") or ""),
                language=lang,
                fmt=str(isa_fmt.get("format") or ""),
            )
        )
        track_rows[track].append(row)
        lang_rows[lang].append(row)
        isa_rows[str(isa_fmt.get("isa") or "unknown")].append(row)
        fmt_rows[str(isa_fmt.get("format") or "unknown")].append(row)
        # compiler_variant is typically "gcc -O2" or "go noopt"
        variant = str(row.get("compiler_variant") or "").strip()
        opt = variant.split()[-1] if variant else "unknown"
        opt_rows[opt].append(row)

    def _pivot(groups: dict[str, list[Mapping[str, Any]]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name, group in sorted(groups.items()):
            taxonomy: dict[str, int] = defaultdict(int)
            scores: list[float] = []
            timeouts = 0
            for row in group:
                bucket = row.get("fail_taxonomy") or normalize_fail_taxonomy(row)
                taxonomy[str(bucket)] += 1
                if bucket == "timeout" or row.get("fail_category") == "timeout":
                    timeouts += 1
                sem = row.get("semantic_score")
                if sem is not None and row.get("fail_category") != "no_wrapper":
                    scores.append(float(sem))
            tested = len(scores)
            out[name] = {
                "rows": len(group),
                "semantic_tested": tested,
                "mean_pass_rate": round(sum(scores) / tested, 4) if tested else None,
                "perfect_rows": sum(1 for s in scores if s >= 1.0),
                "timeout_rows": timeouts,
                "fail_taxonomy": dict(sorted(taxonomy.items())),
            }
        return out

    return {
        "ranking": False,
        "note": (
            "Track/language/ISA/opt pivots are extension diagnostics. Official ranking "
            "remains semantic pass rate on the core C PE cohort."
        ),
        "by_track": _pivot(track_rows),
        "by_language": _pivot(lang_rows),
        "by_isa": _pivot(isa_rows),
        "by_format": _pivot(fmt_rows),
        "by_opt": _pivot(opt_rows),
    }
