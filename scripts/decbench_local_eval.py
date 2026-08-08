#!/usr/bin/env python3
"""Score Fission (and optionally other decompilers) against real C corpora
using DecBench's REAL GED/type_match/byte_match metric code, as a second,
independently-implemented cross-check against `runner/ged.py`'s own (adapted)
reimplementation.

Buckets:
  x86 O0 / x86 O2 / x86 O2-noinline / ARM O0
      This repo's own 8-file `corpus/dev/source/c` set, cross-compiled with
      musl-cross toolchains -- mirrors DecBench's own `OptimizationLevel`
      axis and multi-ISA track (`decbench/models/project.py`,
      `corpus/multi_isa/README.md`).
  large
      A slice of `corpus/scale` (materialize first: see below) -- REAL
      upstream open-source binaries from noelo-lab/decbench-dataset (bash,
      base-passwd, ...), not synthetic test files. GED uses this repo's own
      published (topology-preserving, source-redacted) CFGs via
      `runner.ged.load_published_source_cfgs`, bridged into decbench's real
      `GEDMetric`; type_match/byte_match read DWARF and original bytes
      straight off the (unstripped) materialized binaries, same as decbench's
      own binary-based extraction needs no bridging at all.

Compiles each bucket's binaries ONCE and evaluates them under every requested
decompiler (`--decompilers fission,ghidra,angr`), so a head-to-head
comparison never recompiles per decompiler. Each decompiler's own N reflects
only the functions IT reported (a decompiler that fails a function silently
shrinks its own denominator rather than counting as a miss against a shared
one -- this matches how DecBench's own scoreboard aggregates).

Reports PERFECT COUNTS per bucket (GED==0, type_match==1.0, byte_match==1.0,
and their union -- perfect on at least one axis), not just means: a mean can
look fine while hiding that almost nothing is fully correct on any single
axis, which is the number that actually matters for "how many functions did
DecBench call a full match."

This is a manual, local-only tool -- NOT wired into CI (Joern's ~1.8GB
first-import download, cross toolchains, and a JVM for Ghidra are real,
ongoing costs not worth paying on every commit for a cross-check metric).
Rerun by hand after structuring/normalize changes you want a second opinion
on, or to spot-check Fission against Ghidra/angr on the same inputs.

Prerequisites (one-time setup):

1. A `decbench` checkout, installed editable into its own venv:
       git clone <decbench repo> ~/somewhere/decbench
       python3 -m venv ~/.venvs/decbench-eval
       ~/.venvs/decbench-eval/bin/pip install -e ~/somewhere/decbench
   First run also downloads Joern's ~1.8GB JVM binaries into that venv's own
   pyjoern site-packages (one-time).

2. A Fission release build: export FISSION_CLI=/path/to/fission_cli

3. x86-64 AND aarch64 Linux ELF cross toolchains (`brew install musl-cross`
   on macOS gives both). byte_match recompiles with a compiler name resolved
   off $PATH by *detected binary arch* (`gcc` for x86-64,
   `aarch64-linux-gnu-gcc` for aarch64) -- shim both onto PATH:
       mkdir -p /tmp/decbench-fakebin
       ln -sf "$(which x86_64-linux-musl-gcc)"  /tmp/decbench-fakebin/gcc
       ln -sf "$(which aarch64-linux-musl-gcc)" /tmp/decbench-fakebin/aarch64-linux-gnu-gcc
       export PATH="/tmp/decbench-fakebin:$PATH"

4. For `--decompilers ...,ghidra,...`: `pip install pyghidra` into the same
   decbench venv, a JDK on PATH, and `export GHIDRA_INSTALL_DIR=/path/to/ghidra`.
   For `...,angr,...`: `pip install angr` into the same venv (works standalone,
   no extra setup; a harmless "unicorn support disabled" warning is normal on
   macOS).

5. For the `large` bucket: materialize a small scale-corpus slice first
   (see `docs` in this repo's `corpus/scale/README.md` for the full-scale
   version -- this only needs a handful of binaries):
       python scripts/materialize_scale_corpus.py --config unoptimized --max-binaries 3

6. decbench content-addresses metric results and caches them on disk --
   it cannot see your PATH's `gcc` change meaning between runs. Set
   `DECBENCH_NO_CACHE=1` while iterating on the toolchain, or if numbers
   look stale/suspiciously uniform.

Usage:
    PYTHONPATH=~/.venvs/decbench-eval/lib/python3.*/site-packages \\
        ~/.venvs/decbench-eval/bin/python3 scripts/decbench_local_eval.py \\
        [--decompilers fission,ghidra,angr]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "corpus" / "dev" / "source" / "c"
SCALE_DIR = REPO_ROOT / "corpus" / "scale"
WORK = REPO_ROOT / ".cache" / "decbench-local-eval"

METRIC_NAMES = ["ged", "type_match", "byte_match"]
PERFECT_VALUES = {"ged": 0.0, "type_match": 1.0, "byte_match": 1.0}


@dataclass(frozen=True)
class Profile:
    label: str
    cross_gcc_candidates: tuple[str, ...]
    flags: tuple[str, ...]


PROFILES: tuple[Profile, ...] = (
    Profile("x86 O0", ("x86_64-linux-musl-gcc", "x86_64-linux-gnu-gcc"), ("-O0",)),
    Profile("x86 O2", ("x86_64-linux-musl-gcc", "x86_64-linux-gnu-gcc"), ("-O2",)),
    Profile(
        "x86 O2-noinline",
        ("x86_64-linux-musl-gcc", "x86_64-linux-gnu-gcc"),
        ("-O2", "-fno-inline"),
    ),
    Profile("ARM O0", ("aarch64-linux-musl-gcc", "aarch64-linux-gnu-gcc"), ("-O0",)),
)

# Held-out real-project buckets: corpus/scale materialized from
# noelo-lab/decbench-dataset's real upstream open-source projects (bash,
# coreutils, zlib, ... plus embedded-firmware ones for architecture spread:
# betaflight/chibios/freertos/nuttx/riot-os/u-boot are all 32-bit ARM, not
# aarch64 -- decbench-dataset has no 64-bit ARM track, so this is real ARM
# diversity but not literally "ARM64"). Unlike `corpus/dev`'s 8 files, none
# of these have ever been used to guide a Fission bug fix -- they are a
# genuinely held-out signal, not a training-set replay.
#
# Sampled per-project (not just the first N alphabetically): candidates are
# ranked by published-CFG size (nodes+edges) and taken at even spacing
# across that ranking, so a project contributes a small/medium/large spread
# instead of e.g. all-trivial one-liners.
HELDOUT_OPTS: tuple[str, ...] = ("O0", "O2-noinline")
HELDOUT_MAX_PROJECTS = 25
HELDOUT_FUNCS_PER_PROJECT = 6

# Pinned crash-regression targets: found via held-out testing (a Fission
# stack overflow in lower_varnode_inner's cross-site cycle-detection
# redirect -- fixed in 2652c2219), NOT reachable from `corpus/dev`'s 8-file
# synthetic corpus, and NOT guaranteed to keep landing in HELDOUT_*'s
# size-based random sample if its parameters change later. Checked as a
# decompile-only smoke test (no metric scoring) via `--regression-check`,
# separate from the main sweep since the whole-binary entries are slow
# (cleanflight/crazyflie have thousands of functions -- the exact crashing
# one was never pinned down, only that the binary no longer crashes).
# `func` narrows to one address-verified function when known (fast); `None`
# means "run --all on the whole binary" (slow, ~15-70 min each).
REGRESSION_TARGETS: tuple[tuple[str, str, str | None], ...] = (
    ("binaries/O0/coreutils/cksum", "algorithm_from_tag", "algorithm_from_tag"),
    ("binaries/O0/cleanflight/cleanflight_DALRCF405.elf", "cleanflight (whole binary)", None),
    ("binaries/O0/crazyflie/cf2.elf", "crazyflie cf2 (whole binary)", None),
)


@dataclass
class CompiledUnit:
    stem: str
    elf: Path
    source_cfgs: dict
    # The REAL target function set -- DWARF `DW_TAG_subprogram`s with actual
    # code (core profiles) or the curated published-CFG keys (large bucket).
    # Deliberately NOT `source_cfgs.keys()`: Joern parses the whole
    # preprocessed translation unit, so for a core-profile `.i` file that
    # includes musl's headers, `source_cfgs` also contains ~200 `static
    # inline` libc helpers (`abort`, `bsearch`, `atoi`, ...) that never exist
    # as their own compiled function -- counting those as "targets" a
    # decompiler must produce turned the fixed denominator into ~5x its real
    # size. DWARF has no entry for a fully-inlined function, so it's already
    # the correct restriction.
    target_names: set[str]


@dataclass
class BucketStats:
    label: str
    n: int = 0
    produced: int = 0
    errors: int = 0
    perfect: dict[str, int] = field(default_factory=lambda: {m: 0 for m in METRIC_NAMES})
    finite: dict[str, int] = field(default_factory=lambda: {m: 0 for m in METRIC_NAMES})
    union_perfect: int = 0


def _find_cross_gcc(profile: Profile) -> str | None:
    for candidate in profile.cross_gcc_candidates:
        found = shutil.which(candidate)
        if found:
            return found
    return None


def _unit_target_ids(unit: CompiledUnit) -> set[str]:
    """Ground-truth function names this unit SHOULD produce a result for --
    fixed by the source, independent of what any decompiler actually managed.
    """
    return unit.target_names


def _collect_unit(
    unit: CompiledUnit,
    decompiler_id: str,
    decompile_binary,
    evaluate_decompilation,
) -> dict[str, dict[str, float | None]]:
    """``{function_name: {metric_name: value}}`` for this unit's target
    functions only. A target function absent from the returned dict means
    the decompiler never produced ANY output for it (crash, timeout, missed
    discovery, ...) -- that absence is itself the signal a shared-N miss
    count needs; it must not be silently dropped by the caller.
    """
    dec_result = decompile_binary(unit.elf, decompiler_id, WORK / "out" / decompiler_id)
    eval_result = evaluate_decompilation(dec_result, unit.source_cfgs, METRIC_NAMES)
    targets = _unit_target_ids(unit)
    per_function: dict[str, dict[str, float | None]] = {}
    for metric_name, result in eval_result.items():
        for fn_name, v in result.function_results.items():
            if fn_name not in targets:
                continue
            per_function.setdefault(fn_name, {})[metric_name] = v.value
    return per_function


def _compile_core_profile(
    profile: Profile, cross_gcc: str, extract_cfgs_from_source, extract_ground_truth_types
) -> list[CompiledUnit]:
    profile_work = WORK / profile.label.replace(" ", "_")
    profile_work.mkdir(parents=True, exist_ok=True)
    units: list[CompiledUnit] = []

    for src in sorted(SRC_DIR.glob("*.c")):
        stem = src.stem
        elf = profile_work / f"{stem}.elf"
        i_file = profile_work / f"{stem}.i"
        try:
            subprocess.run(
                [cross_gcc, *profile.flags, "-g", "-static", "-o", str(elf), str(src)],
                check=True, capture_output=True, text=True,
            )
            subprocess.run(
                [cross_gcc, "-E", str(src), "-o", str(i_file)],
                check=True, capture_output=True, text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"  [{profile.label}] {stem}: compile failed: {e.stderr[-300:]}", file=sys.stderr)
            continue
        source_cfgs = extract_cfgs_from_source(i_file) or {}
        target_names = set(extract_ground_truth_types(elf).keys()) | {"main"}
        units.append(CompiledUnit(stem=stem, elf=elf, source_cfgs=source_cfgs, target_names=target_names))

    return units


def _manifests_by_project(opt: str) -> dict[str, list[dict]]:
    """project -> parsed manifest payloads materialized for this opt config.

    Each manifest file is one (opt, project, binary); the project name comes
    from the payload's own `functions[0]["project"]`, not the filename (the
    filename's readable prefix is sanitized/truncated and not reliably
    parseable back into a project name that can itself contain underscores).
    """
    import json as _json

    manifests_dir = SCALE_DIR / "manifests"
    by_project: dict[str, list[dict]] = {}
    for path in sorted(manifests_dir.glob(f"{opt}__*.json")):
        try:
            payload = _json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        functions = payload.get("functions") or []
        if not functions:
            continue
        project = functions[0].get("project")
        if not project:
            continue
        by_project.setdefault(project, []).append(payload)
    return by_project


def _sample_heldout_units(
    opt: str, max_projects: int, per_project: int, load_published_source_cfgs
) -> list[CompiledUnit]:
    by_project = _manifests_by_project(opt)
    if not by_project:
        print(
            f"skipping held-out {opt}: no manifests materialized "
            f"(run: python scripts/materialize_scale_corpus.py "
            f"--config {'unoptimized' if opt == 'O0' else 'optimized'} --max-binaries N)",
            file=sys.stderr,
        )
        return []

    units: list[CompiledUnit] = []
    for project in sorted(by_project)[:max_projects]:
        # (binary_rel, function_name, cfg_size) across every binary this
        # project contributed manifests for, so the per-project sample can
        # draw from all of them, not just the first binary encountered.
        candidates: list[tuple[str, str, int]] = []
        cfg_cache: dict[str, dict] = {}
        for payload in by_project[project]:
            for func in payload.get("functions", []):
                variants = func.get("compiler_variants") or []
                if not variants:
                    continue
                variant = variants[0]
                binary_rel = variant.get("binary")
                cfg_rel = variant.get("source_cfg")
                name = func.get("name")
                if not binary_rel or not cfg_rel or not name:
                    continue
                if binary_rel not in cfg_cache:
                    cfg_path = SCALE_DIR / cfg_rel
                    if not cfg_path.is_file():
                        cfg_cache[binary_rel] = {}
                    else:
                        cfg_cache[binary_rel] = load_published_source_cfgs(str(cfg_path))
                graph = cfg_cache[binary_rel].get(name)
                if graph is None:
                    continue
                size = graph.number_of_nodes() + graph.number_of_edges()
                candidates.append((binary_rel, name, size))

        if not candidates:
            continue
        candidates.sort(key=lambda c: c[2])
        k = min(per_project, len(candidates))
        if k >= len(candidates):
            picked = candidates
        elif k == 1:
            picked = [candidates[len(candidates) // 2]]
        else:
            picked = [
                candidates[round(i * (len(candidates) - 1) / (k - 1))] for i in range(k)
            ]
        seen: set[tuple[str, str]] = set()
        by_binary: dict[str, list[str]] = {}
        for binary_rel, name, _size in picked:
            key = (binary_rel, name)
            if key in seen:
                continue
            seen.add(key)
            by_binary.setdefault(binary_rel, []).append(name)

        for binary_rel, names in by_binary.items():
            elf = SCALE_DIR / binary_rel
            if not elf.is_file():
                continue
            units.append(
                CompiledUnit(
                    stem=f"{project}/{Path(binary_rel).name}",
                    elf=elf,
                    source_cfgs=cfg_cache[binary_rel],
                    target_names=set(names),
                )
            )

    return units


def _stats_for_ids(
    label: str,
    ids: set[str],
    per_dec_results: dict[str, float | None],
    errors: int = 0,
) -> BucketStats:
    """`ids` is the fixed denominator (same set for every decompiler this is
    called with) -- an id in `ids` but absent from `per_dec_results` counts
    toward N but not toward `produced`/perfect/finite (a real miss), matching
    how DecBench's own scoreboard treats an undecompiled function."""
    stats = BucketStats(label=label, n=len(ids), errors=errors)
    for fid in ids:
        values = per_dec_results.get(fid)
        if values is None:
            continue
        stats.produced += 1
        any_perfect = False
        for metric_name in METRIC_NAMES:
            v = values.get(metric_name)
            if v is None or v == float("inf"):
                continue
            stats.finite[metric_name] += 1
            if v == PERFECT_VALUES[metric_name]:
                stats.perfect[metric_name] += 1
                any_perfect = True
        if any_perfect:
            stats.union_perfect += 1
    return stats


def _print_table(title: str, rows: list[tuple[str, str, BucketStats]]) -> None:
    """`rows` is (decompiler_id, bucket_label, stats), grouped by bucket (blank
    line between groups) so decompilers on the same denominator sit together."""
    print(f"\n=== {title} ===")
    header = (
        f"{'profile':<16} {'tool':<10} {'targets':>7} {'produced':>8} "
        f"{'GED0':>6} {'Type1':>6} {'Byte1':>6} {'Union':>6} {'errors':>6}"
    )
    print(header)
    print("-" * len(header))
    last_bucket = None
    for dec_id, bucket_label, b in rows:
        if last_bucket is not None and bucket_label != last_bucket:
            print()
        shown_label = bucket_label if bucket_label != last_bucket else ""
        print(
            f"{shown_label:<16} {dec_id:<10} {b.n:>7} {b.produced:>8} {b.perfect['ged']:>6} "
            f"{b.perfect['type_match']:>6} {b.perfect['byte_match']:>6} {b.union_perfect:>6} "
            f"{b.errors:>6}"
        )
        last_bucket = bucket_label


def _run_regression_check(decompiler_ids: list[str], decompile_binary) -> bool:
    """Decompile-only crash smoke test for REGRESSION_TARGETS. No metric
    scoring -- this only asks "did it crash," not "was it correct." Returns
    True iff every target decompiled without raising, for every decompiler."""
    all_ok = True
    for dec_id in decompiler_ids:
        print(f"\n### regression check: {dec_id} ###", file=sys.stderr)
        for binary_rel, label, func_name in REGRESSION_TARGETS:
            elf = SCALE_DIR / binary_rel
            if not elf.is_file():
                print(f"  [{dec_id}] {label}: SKIPPED (not materialized: {binary_rel})")
                continue
            functions = [(func_name, 0)] if func_name else None
            start = time.time()
            try:
                result = decompile_binary(elf, dec_id, None, functions=functions)
                elapsed = time.time() - start
                if functions is not None and not result.functions:
                    all_ok = False
                    print(f"  [{dec_id}] {label}: FAILED -- target function not produced")
                else:
                    print(f"  [{dec_id}] {label}: OK ({elapsed:.1f}s, {len(result.functions)} functions)")
            except Exception as e:  # noqa: BLE001
                all_ok = False
                elapsed = time.time() - start
                print(f"  [{dec_id}] {label}: FAILED after {elapsed:.1f}s -- {e}")
    return all_ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--decompilers", default="fission",
        help="comma-separated decbench decompiler ids, e.g. fission,ghidra,angr",
    )
    parser.add_argument(
        "--skip-core", action="store_true",
        help="skip the corpus/dev 8-file synthetic profiles (x86 O0/O2/O2-noinline, ARM O0) "
        "and only run the held-out real-project buckets. Those 8 files have shaped Fission's "
        "own development (fission-benchmark's own long-running CI corpus), so a score against "
        "them is a training-set replay, not a held-out signal -- use this flag when that's what "
        "you actually want to measure.",
    )
    parser.add_argument(
        "--skip-heldout", action="store_true",
        help="skip the corpus/scale held-out real-project buckets",
    )
    parser.add_argument(
        "--regression-check", action="store_true",
        help="run ONLY the pinned REGRESSION_TARGETS decompile-only smoke test (no metric "
        "scoring, no core/held-out buckets) and exit. Fast for the single-function targets; "
        "the whole-binary ones (cleanflight, crazyflie) take ~15-70 min each -- this is for "
        "occasional confirmation a known crash hasn't come back, not routine use.",
    )
    args = parser.parse_args()
    decompiler_ids = [d.strip() for d in args.decompilers.split(",") if d.strip()]

    try:
        import decbench.decompilers  # noqa: F401  (registers in-tree backends)
    except ImportError:
        print(
            "decbench is not importable -- see this script's module docstring "
            "for one-time setup (a separate venv with `pip install -e <decbench checkout>`).",
            file=sys.stderr,
        )
        return 1

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import decbench_fission_backend  # noqa: F401  (registers "fission")

    from decbench.decompilers.registry import DecompilerRegistry
    from decbench.pipeline.decompile import decompile_binary
    from decbench.pipeline.evaluate import evaluate_decompilation
    from decbench.metrics.type_match import extract_ground_truth_types
    from decbench.utils.cfg import extract_cfgs_from_source

    for dec_id in decompiler_ids:
        try:
            dec = DecompilerRegistry.get(dec_id)
            if not dec.is_available():
                print(f"WARNING: decompiler '{dec_id}' is registered but not available", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"WARNING: decompiler '{dec_id}' could not be resolved: {e}", file=sys.stderr)

    if args.regression_check:
        ok = _run_regression_check(decompiler_ids, decompile_binary)
        print("\nregression check:", "PASS" if ok else "FAIL")
        return 0 if ok else 1

    WORK.mkdir(parents=True, exist_ok=True)

    print("### compiling corpora (once, shared across decompilers) ###", file=sys.stderr)
    bucket_units: list[tuple[str, list[CompiledUnit]]] = []
    if args.skip_core:
        print("  skipping core synthetic profiles (--skip-core)", file=sys.stderr)
    else:
        for profile in PROFILES:
            cross_gcc = _find_cross_gcc(profile)
            if cross_gcc is None:
                print(
                    f"skipping {profile.label}: no cross compiler found "
                    f"({' / '.join(profile.cross_gcc_candidates)})",
                    file=sys.stderr,
                )
                continue
            print(f"  compiling {profile.label} ({cross_gcc})", file=sys.stderr)
            units = _compile_core_profile(
                profile, cross_gcc, extract_cfgs_from_source, extract_ground_truth_types
            )
            bucket_units.append((profile.label, units))

    sys.path.insert(0, str(REPO_ROOT))
    if args.skip_heldout:
        print("  skipping held-out real-project buckets (--skip-heldout)", file=sys.stderr)
    try:
        from runner.ged import load_published_source_cfgs

        for opt in ([] if args.skip_heldout else HELDOUT_OPTS):
            label = f"held-out {opt}"
            print(f"  sampling {label} (held-out real projects)", file=sys.stderr)
            units = _sample_heldout_units(
                opt, HELDOUT_MAX_PROJECTS, HELDOUT_FUNCS_PER_PROJECT, load_published_source_cfgs
            )
            if units:
                n_projects = len({u.stem.split("/", 1)[0] for u in units})
                n_targets = sum(len(u.target_names) for u in units)
                print(
                    f"  {label}: {n_projects} projects, {len(units)} binaries, "
                    f"{n_targets} target functions",
                    file=sys.stderr,
                )
                bucket_units.append((label, units))
    except ImportError as e:
        print(f"skipping held-out buckets: cannot import runner.ged: {e}", file=sys.stderr)

    # target_ids[bucket] -- fixed by the source, identical for every decompiler.
    # raw_results[dec_id][bucket][(stem, fn_name)] -- absent means that
    # decompiler never produced ANY output for that target function.
    target_ids: dict[str, set[tuple[str, str]]] = {}
    raw_results: dict[str, dict[str, dict[tuple[str, str], dict[str, float | None]]]] = {
        dec_id: {} for dec_id in decompiler_ids
    }

    for label, units in bucket_units:
        target_ids[label] = {(unit.stem, name) for unit in units for name in _unit_target_ids(unit)}

    # error_counts[dec_id][label] -- number of units (whole-binary decompile
    # calls) that raised, as opposed to a target function the decompiler ran
    # but simply didn't emit (that's a `produced`-side miss, not an error).
    error_counts: dict[str, dict[str, int]] = {dec_id: {} for dec_id in decompiler_ids}

    for dec_id in decompiler_ids:
        print(f"\n### evaluating decompiler: {dec_id} ###", file=sys.stderr)
        for label, units in bucket_units:
            bucket_map: dict[tuple[str, str], dict[str, float | None]] = {}
            unit_errors = 0
            for unit in units:
                try:
                    per_fn = _collect_unit(unit, dec_id, decompile_binary, evaluate_decompilation)
                except Exception as e:  # noqa: BLE001
                    unit_errors += 1
                    print(f"  [{dec_id}/{label}] {unit.stem}: {e}", file=sys.stderr)
                    continue
                for fn_name, values in per_fn.items():
                    bucket_map[(unit.stem, fn_name)] = values
            raw_results[dec_id][label] = bucket_map
            error_counts[dec_id][label] = unit_errors
            stats = _stats_for_ids(label, target_ids[label], bucket_map, errors=unit_errors)
            print(
                f"  [{dec_id}] {label}: n={stats.n} produced={stats.produced} errors={unit_errors} "
                f"finite={stats.finite} perfect={stats.perfect} union={stats.union_perfect}",
                file=sys.stderr,
            )

    bucket_labels = [label for label, _ in bucket_units]

    fixed_rows: list[tuple[str, str, BucketStats]] = []
    for label in bucket_labels:
        for dec_id in decompiler_ids:
            stats = _stats_for_ids(
                label, target_ids[label], raw_results[dec_id][label],
                errors=error_counts[dec_id][label],
            )
            fixed_rows.append((dec_id, label, stats))
    _print_table(
        "FULL TARGET SET (same N per profile for every tool; a tool's own "
        "miss/crash/timeout counts against it -- included in GED0/Type1/Byte1/"
        "Union as a non-perfect, not silently dropped from the denominator)",
        fixed_rows,
    )

    intersection_rows: list[tuple[str, str, BucketStats]] = []
    for label in bucket_labels:
        common = None
        for dec_id in decompiler_ids:
            keys = set(raw_results[dec_id][label].keys())
            common = keys if common is None else (common & keys)
        common = common or set()
        for dec_id in decompiler_ids:
            stats = _stats_for_ids(
                label, common, raw_results[dec_id][label], errors=error_counts[dec_id][label]
            )
            intersection_rows.append((dec_id, label, stats))
    _print_table(
        "INTERSECTION (only functions ALL requested tools decompiled -- the "
        "fairest apples-to-apples decompilation-QUALITY denominator, but N "
        "shrinks to the hardest-common-denominator subset; the FULL TARGET "
        "SET table above is the one that also captures robustness/coverage)",
        intersection_rows,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
