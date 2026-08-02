#!/usr/bin/env python3
"""CI gate: multi-decomp dashboard must have non-empty display data.

The Vercel/Next dashboard loads (in order):
  1. public/benchmark-latest.json  (optional local/public seed)
  2. BENCHMARK_LATEST_URL          (optional env override)
  3. results/latest.json           (publication artifact)
  4. results/dev_latest.json       (tracked fallback on main)

Empty UI is a release failure. This script fails when no candidate source
has a parseable envelope with enough rows.

Usage:
  python scripts/check_dashboard_data.py
  python scripts/check_dashboard_data.py --check-remote
  python scripts/check_dashboard_data.py --min-rows 10
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_LOCAL = (
    "public/benchmark-latest.json",
    "results/latest.json",
    "results/dev_latest.json",
)

DEFAULT_REMOTE = (
    "https://raw.githubusercontent.com/fission-systems/fission-benchmark/main/results/latest.json",
    "https://raw.githubusercontent.com/fission-systems/fission-benchmark/main/results/dev_latest.json",
)


def _load_json_path(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"WARN {path}: unreadable JSON ({exc})", file=sys.stderr)
        return None
    return data if isinstance(data, dict) else None


def _load_json_url(url: str, timeout: float) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"WARN remote {url}: {exc}", file=sys.stderr)
        return None
    return data if isinstance(data, dict) else None


def evaluate_envelope(
    data: dict[str, Any],
    *,
    source: str,
    min_rows: int,
    require_valid: bool,
    min_decompilers: int = 1,
) -> list[str]:
    """Return error strings if envelope is not displayable."""
    errors: list[str] = []
    rows = data.get("rows")
    if not isinstance(rows, list):
        errors.append(f"{source}: missing rows[] list")
        return errors
    n = len(rows)
    if n < min_rows:
        errors.append(f"{source}: rows={n} < min_rows={min_rows}")
    schema = data.get("schema_version")
    if schema is not None and int(schema) < 2:
        errors.append(f"{source}: schema_version={schema} expected >= 2")
    validity = data.get("validity") or {}
    if require_valid and validity.get("valid") is not True:
        errors.append(
            f"{source}: validity.valid is not true "
            f"(publishable={validity.get('publishable')}, reasons={validity.get('reasons')})"
        )
    tools = {
        str(r.get("decompiler") or "")
        for r in rows
        if isinstance(r, dict) and r.get("decompiler")
    }
    tools.discard("")
    if n > 0 and not tools:
        errors.append(f"{source}: rows present but no decompiler fields")
    if min_decompilers > 1 and len(tools) < min_decompilers:
        errors.append(
            f"{source}: decompilers={sorted(tools)} count={len(tools)} "
            f"< min_decompilers={min_decompilers} "
            f"(dashboard would hide most backends — re-run multi-decomp and update envelope)"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--min-rows",
        type=int,
        default=1,
        help="Minimum rows required in a displayable envelope (default 1)",
    )
    parser.add_argument(
        "--require-valid",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require validity.valid=true (default true). Publishable not required.",
    )
    parser.add_argument(
        "--check-remote",
        action="store_true",
        help="Also verify raw.githubusercontent.com sources used by Vercel",
    )
    parser.add_argument(
        "--remote-timeout",
        type=float,
        default=30.0,
        help="HTTP timeout for --check-remote (seconds)",
    )
    parser.add_argument(
        "--require-local",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require a local display source under the repo (default true)",
    )
    parser.add_argument(
        "--min-decompilers",
        type=int,
        default=1,
        help=(
            "Minimum distinct decompiler names in rows (default 1). "
            "Set to 8+ so fission+ghidra-only envelopes fail CI."
        ),
    )
    parser.add_argument(
        "--local-paths",
        nargs="+",
        default=None,
        help=(
            "Override local envelope paths (repo-relative). "
            "Default: public/benchmark-latest.json results/latest.json results/dev_latest.json. "
            "Pass only public/benchmark-latest.json for multi-decomp UI checks during ranking runs."
        ),
    )
    parser.add_argument(
        "--remote-paths",
        nargs="+",
        default=None,
        help="Override remote URLs for --check-remote (default: main results/latest + dev_latest).",
    )
    args = parser.parse_args(argv)

    root: Path = args.root
    local_paths = tuple(args.local_paths) if args.local_paths else DEFAULT_LOCAL
    remote_paths = tuple(args.remote_paths) if args.remote_paths else DEFAULT_REMOTE
    local_hits: list[tuple[str, dict[str, Any]]] = []
    for rel in local_paths:
        path = root / rel
        data = _load_json_path(path)
        if data is None:
            print(f"MISS local {rel}")
            continue
        errs = evaluate_envelope(
            data,
            source=rel,
            min_rows=args.min_rows,
            require_valid=args.require_valid,
            min_decompilers=args.min_decompilers,
        )
        if errs:
            for e in errs:
                print(f"FAIL {e}", file=sys.stderr)
            continue
        rows = data.get("rows") or []
        validity = data.get("validity") or {}
        tools = sorted(
            {
                str(r.get("decompiler"))
                for r in rows
                if isinstance(r, dict) and r.get("decompiler")
            }
        )
        print(
            f"OK local {rel}: rows={len(rows)} tools={len(tools)} "
            f"valid={validity.get('valid')} publishable={validity.get('publishable')} "
            f"corpus={(data.get('run') or {}).get('corpus')} decompilers={tools}"
        )
        local_hits.append((rel, data))

    remote_hits: list[tuple[str, dict[str, Any]]] = []
    if args.check_remote:
        for url in remote_paths:
            data = _load_json_url(url, args.remote_timeout)
            if data is None:
                print(f"MISS remote {url}")
                continue
            errs = evaluate_envelope(
                data,
                source=url,
                min_rows=args.min_rows,
                require_valid=args.require_valid,
                min_decompilers=args.min_decompilers,
            )
            if errs:
                for e in errs:
                    print(f"FAIL {e}", file=sys.stderr)
                continue
            rows = data.get("rows") or []
            validity = data.get("validity") or {}
            tools = sorted(
                {
                    str(r.get("decompiler"))
                    for r in rows
                    if isinstance(r, dict) and r.get("decompiler")
                }
            )
            print(
                f"OK remote {url.split('/')[-1]}: rows={len(rows)} tools={len(tools)} "
                f"valid={validity.get('valid')} publishable={validity.get('publishable')} "
                f"decompilers={tools}"
            )
            remote_hits.append((url, data))

    hard: list[str] = []
    if args.require_local and not local_hits:
        hard.append(
            "no local displayable envelope "
            f"(checked: {', '.join(local_paths)}). "
            "Dashboard would be empty. Commit results/dev_latest.json or "
            "public/benchmark-latest.json with non-empty rows."
        )
    if args.check_remote and not remote_hits:
        hard.append(
            "no remote displayable envelope on main "
            f"(checked: {', '.join(remote_paths)}). "
            "Vercel fetch would show empty multi-decomp pages."
        )

    if hard:
        for e in hard:
            print(f"FAIL {e}", file=sys.stderr)
        print(
            "FAIL dashboard data gate: multi-decomp UI must not ship empty",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK dashboard data gate: local_hits={len(local_hits)} "
        f"remote_hits={len(remote_hits)} min_rows={args.min_rows}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
