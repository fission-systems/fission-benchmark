"""fbench command line: list / run / report / serve.

    python -m fbench run --opt O0 --limit 50 -j 4
    python -m fbench report          # runs/ -> docs/data/*.json
    python -m fbench serve           # preview docs/ locally
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from .score import METRICS, PERFECT, Job, find_fission_cli, fission_version, score_binary
from .provenance import environment, make_manifest, result_matches

ROOT = Path(__file__).resolve().parents[1]
DATA_DEFAULT = ROOT / "decbench-data"
RESULTS_DEFAULT = ROOT / "runs"
DOCS = ROOT / "docs"


def discover(data: Path, opts: set[str] | None, projects: set[str] | None) -> list[tuple[str, str, str, Path, Path]]:
    """Every dataset binary that has a published source CFG."""
    found = []
    base = data / "binaries"
    for opt_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        if opts and opt_dir.name not in opts:
            continue
        for proj_dir in sorted(p for p in opt_dir.iterdir() if p.is_dir()):
            if projects and proj_dir.name not in projects:
                continue
            for b in sorted(p for p in proj_dir.iterdir() if p.is_file()):
                cfg = data / "pipeline_data" / "source_cfgs" / opt_dir.name / proj_dir.name / f"{b.name}.json"
                if not cfg.is_file():
                    cfg = cfg.with_name(f"{b.stem}.json")
                if cfg.is_file():
                    found.append((opt_dir.name, proj_dir.name, b.name, b, cfg))
    return found


def _select(args) -> list[tuple[str, str, str, Path, Path]]:
    items = discover(
        Path(args.data), set(args.opt) or None, set(args.project) or None
    )
    if args.match:
        items = [i for i in items if args.match in f"{i[0]}/{i[1]}/{i[2]}"]
    if args.limit:
        # Even spread across the sorted list so a small --limit still covers many projects.
        step = max(1, len(items) // args.limit)
        items = items[::step][: args.limit]
    return items


def cmd_list(args) -> int:
    items = _select(args)
    by = defaultdict(int)
    for opt, proj, *_ in items:
        by[(opt, proj)] += 1
    for (opt, proj), n in sorted(by.items()):
        print(f"{opt:12s} {proj:24s} {n}")
    print(f"\n{len(items)} binaries, {len({p for _, p in by})} projects", file=sys.stderr)
    return 0


def cmd_audit(args) -> int:
    """Inventory every selected binary, including ones without source CFGs."""
    base = Path(args.data) / "binaries"
    if not base.is_dir():
        print(f"dataset binaries directory not found: {base}", file=sys.stderr)
        return 2
    rows = []
    for opt in sorted(p for p in base.iterdir() if p.is_dir()):
        if args.opt and opt.name not in args.opt:
            continue
        for project in sorted(p for p in opt.iterdir() if p.is_dir()):
            if args.project and project.name not in args.project:
                continue
            for binary in sorted(p for p in project.iterdir() if p.is_file()):
                key = f"{opt.name}/{project.name}/{binary.name}"
                if args.match and args.match not in key:
                    continue
                cfg_root = Path(args.data) / "pipeline_data" / "source_cfgs" / opt.name / project.name
                exact = cfg_root / f"{binary.name}.json"
                stem = cfg_root / f"{binary.stem}.json"
                cfg = exact if exact.is_file() else stem if stem.is_file() else None
                rows.append({"opt": opt.name, "project": project.name, "binary": binary.name,
                             "source_cfg": str(cfg) if cfg else None,
                             "match": "exact" if cfg == exact else "stem" if cfg else "missing"})
    if args.limit:
        step = max(1, len(rows) // args.limit)
        rows = rows[::step][:args.limit]
    counts = {status: sum(row["match"] == status for row in rows)
              for status in ("exact", "stem", "missing")}
    print(json.dumps({"schema": 1, "data_root": str(Path(args.data).resolve()),
                      "counts": counts, "binaries": rows}, indent=2))
    return 0


def cmd_run(args) -> int:
    cli = find_fission_cli(args.fission_cli)
    if not cli:
        print("fission_cli not found: pass --fission-cli, set $FISSION_CLI, or add to PATH", file=sys.stderr)
        return 2
    unknown = [m for m in args.metrics if m not in METRICS]
    if unknown:
        print(f"unknown metric(s): {unknown}; choose from {METRICS}", file=sys.stderr)
        return 2
    if args.jobs < 1 or args.binary_timeout < 1 or (args.limit is not None and args.limit < 1):
        print("jobs, binary timeout and limit must be positive", file=sys.stderr)
        return 2
    items = _select(args)
    if not items:
        print("no matching dataset binaries", file=sys.stderr)
        return 2
    try:
        env = environment(cli, args.layer, args.metrics, args.binary_timeout)
        env["fission"]["version"] = fission_version(cli)
        manifest = make_manifest(items, env)
    except (OSError, RuntimeError) as exc:
        print(f"cannot identify run inputs: {exc}", file=sys.stderr)
        return 2
    results = Path(args.results)
    run_root = results / "runs" / manifest["run_id"]
    run_dir = run_root / "binaries"
    run_root.mkdir(parents=True, exist_ok=True)
    manifest_path = run_root / "manifest.json"
    if manifest_path.exists():
        try:
            if json.loads(manifest_path.read_text()) != manifest:
                raise ValueError("manifest does not match its run identity")
        except (OSError, ValueError) as exc:
            print(f"invalid run manifest: {exc}", file=sys.stderr)
            return 2
    else:
        tmp = manifest_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(manifest, indent=2))
        tmp.replace(manifest_path)
    latest = results / "latest.json"
    latest_tmp = latest.with_suffix(".tmp")
    latest_tmp.write_text(json.dumps({"run_id": manifest["run_id"]}))
    latest_tmp.replace(latest)
    jobs = []
    for (opt, proj, name, path, cfg), entry in zip(items, manifest["inputs"], strict=True):
        out = run_dir / opt / proj / f"{name}.{args.layer}.json"
        if out.exists() and not args.force:
            try:
                if result_matches(json.loads(out.read_text()), manifest, entry):
                    continue
            except (OSError, ValueError):
                pass
        jobs.append(Job(opt, proj, name, str(path), str(cfg), str(out), cli,
                        layer=args.layer, metrics=tuple(env["metrics"]),
                        binary_timeout_s=args.binary_timeout, run_id=manifest["run_id"],
                        binary_sha256=entry["binary_sha256"], cfg_sha256=entry["cfg_sha256"],
                        cli_sha256=env["fission"]["sha256"]))
    print(f"fission {fission_version(cli)} ({args.layer}) | {len(items)} selected, "
          f"{len(items) - len(jobs)} already scored, {len(jobs)} to run, -j {args.jobs}", flush=True)
    if not jobs:
        return 0
    print(f"run {manifest['run_id']}", flush=True)

    t0 = time.time()
    done = 0
    failures = 0
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futs = {pool.submit(score_binary, j): j for j in jobs}
        for fut in as_completed(futs):
            j = futs[fut]
            done += 1
            try:
                r = fut.result()
                note = f"{r['status']:9s} {r['produced']}/{r['targets']} fns {r['seconds']}s"
                if r.get("error"):
                    note += f"  ! {r['error'][:80]}"
                if r['status'] != 'ok':
                    failures += 1
            except Exception as exc:  # worker crash (OOM etc.)
                note = f"crashed   {type(exc).__name__}: {exc}"
                failures += 1
            print(f"[{done}/{len(jobs)}] {j.key}  {note}", flush=True)
    print(f"done in {time.time() - t0:.0f}s. Next: python -m fbench report", flush=True)
    return 1 if failures else 0


# ---------------------------------------------------------------- report

def _blank() -> dict:
    d = {"binaries": 0, "ok": 0, "targets": 0, "produced": 0, "union_perfect": 0}
    for m in METRICS:
        d[m] = {"scored": 0, "perfect": 0, "sum": 0.0}
    return d


def _add(agg: dict, rec: dict) -> None:
    agg["binaries"] += 1
    agg["ok"] += rec["status"] == "ok"
    agg["targets"] += rec["targets"]
    agg["produced"] += rec["produced"]
    for fn in rec["functions"].values():
        perfect_any = False
        for m in METRICS:
            v = fn.get(m)
            if v is None:
                continue
            agg[m]["scored"] += 1
            agg[m]["sum"] += v
            if v == PERFECT[m]:
                agg[m]["perfect"] += 1
                perfect_any = True
        agg["union_perfect"] += perfect_any


def _finish(agg: dict) -> dict:
    t = agg["targets"] or 1
    out = {
        "binaries": agg["binaries"], "ok": agg["ok"], "functions": agg["targets"],
        "produced": agg["produced"], "coverage": round(100 * agg["produced"] / t, 2),
        # Perfect rates are over ALL target functions: a miss or crash counts against Fission.
        "union": round(100 * agg["union_perfect"] / t, 2),
    }
    for m in METRICS:
        a = agg[m]
        out[m] = {
            "scored": a["scored"],
            "perfect": a["perfect"],
            # None = the metric abstained everywhere (e.g. no recompile toolchain).
            "perfect_pct": round(100 * a["perfect"] / t, 2) if a["scored"] else None,
            "mean": round(a["sum"] / a["scored"], 4) if a["scored"] else None,
        }
    return out


def cmd_report(args) -> int:
    results = Path(args.results)
    try:
        run_id = args.run_id or json.loads((results / "latest.json").read_text())["run_id"]
        if not isinstance(run_id, str) or len(run_id) != 64 or any(c not in "0123456789abcdef" for c in run_id):
            raise ValueError("invalid run ID")
        run_root = results / "runs" / run_id
        manifest = json.loads((run_root / "manifest.json").read_text())
        from .provenance import canonical_hash
        if manifest.get("run_id") != run_id or canonical_hash({k: v for k, v in manifest.items() if k != "run_id"}) != run_id:
            raise ValueError("manifest identity mismatch")
        if manifest["environment"]["layer"] != args.layer:
            raise ValueError("requested layer does not match manifest")
        records = []
        for item in manifest["inputs"]:
            path = run_root / "binaries" / item["opt"] / item["project"] / f"{item['binary']}.{args.layer}.json"
            rec = json.loads(path.read_text())
            if not result_matches(rec, manifest, item, success=False):
                raise ValueError(f"result provenance mismatch: {path}")
            if rec.get("status") not in ("ok", "no_output", "no_targets") and not rec.get("targets"):
                raise ValueError(f"target population unavailable: {path}")
            records.append(rec)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"cannot report incomplete or invalid run: {exc}", file=sys.stderr)
        return 2
    total, by_opt, by_proj, bins = _blank(), defaultdict(_blank), defaultdict(_blank), []
    for rec in records:
        _add(total, rec)
        _add(by_opt[rec["opt"]], rec)
        _add(by_proj[(rec["opt"], rec["project"])], rec)
        one = _blank()
        _add(one, rec)
        row = _finish(one)
        row.update(opt=rec["opt"], project=rec["project"], binary=rec["binary"],
                   status=rec["status"], seconds=rec.get("seconds"), error=rec.get("error"))
        bins.append(row)
    if not any(total[m]["scored"] for m in manifest["environment"]["metrics"]):
        print("cannot report: no selected metric has any scores", file=sys.stderr)
        return 2
    summary = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "decompiler": "fission", "version": manifest["environment"]["fission"]["version"], "layer": args.layer,
        "run_id": run_id, "metrics": manifest["environment"]["metrics"],
        "total": _finish(total),
        "by_opt": {k: _finish(v) for k, v in sorted(by_opt.items())},
        "by_project": [dict(opt=o, project=p, **_finish(v)) for (o, p), v in sorted(by_proj.items())],
        "binaries": bins,
    }
    out = DOCS / "data"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, separators=(",", ":")))
    (DOCS / ".nojekyll").touch()
    t = summary["total"]
    print(f"{t['binaries']} binaries / {t['functions']} functions  coverage {t['coverage']}%  "
          f"GED0 {t['ged']['perfect_pct']}%  Type1 {t['type_match']['perfect_pct']}%  "
          f"Byte1 {t['byte_match']['perfect_pct']}%  Union {t['union']}%  (None = metric abstained)")
    print(f"wrote {out / 'summary.json'}  -> commit docs/ and push to publish on GitHub Pages")
    return 0


def cmd_serve(args) -> int:
    import http.server
    import functools

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
    print(f"http://localhost:{args.port}")
    http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fbench", description="Local Fission decompilation benchmark (DecBench-style).")
    sub = p.add_subparsers(dest="cmd", required=True)

    def selection(sp):
        sp.add_argument("--data", default=os.environ.get("DECBENCH_DATA", str(DATA_DEFAULT)),
                        help="DecBench dataset root (binaries/, pipeline_data/)")
        sp.add_argument("--opt", action="append", default=[], help="O0 | O2 | O2-noinline (repeatable)")
        sp.add_argument("--project", action="append", default=[], help="project name (repeatable)")
        sp.add_argument("--match", help="substring of opt/project/binary")
        sp.add_argument("--limit", type=int, help="evenly sample N binaries")

    sp = sub.add_parser("list", help="show selectable binaries")
    selection(sp)
    sp.set_defaults(fn=cmd_list)
    sp = sub.add_parser("audit", help="inventory binaries, including missing source CFGs")
    selection(sp)
    sp.set_defaults(fn=cmd_audit)

    sp = sub.add_parser("run", help="decompile + score binaries locally")
    selection(sp)
    sp.add_argument("-j", "--jobs", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    sp.add_argument("--layer", default="nir", choices=["nir", "hir"])
    sp.add_argument("--metrics", nargs="+", default=list(METRICS))
    sp.add_argument("--fission-cli")
    sp.add_argument("--binary-timeout", type=int, default=3600)
    sp.add_argument("--force", action="store_true", help="rescore binaries that already have results")
    sp.add_argument("--results", default=str(RESULTS_DEFAULT))
    sp.set_defaults(fn=cmd_run)

    sp = sub.add_parser("report", help="aggregate results into docs/data for GitHub Pages")
    sp.add_argument("--layer", default="nir", choices=["nir", "hir"])
    sp.add_argument("--results", default=str(RESULTS_DEFAULT))
    sp.add_argument("--run-id", help="report one manifest-identified run (default: latest)")
    sp.set_defaults(fn=cmd_report)

    sp = sub.add_parser("serve", help="preview docs/ locally")
    sp.add_argument("--port", type=int, default=8000)
    sp.set_defaults(fn=cmd_serve)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
