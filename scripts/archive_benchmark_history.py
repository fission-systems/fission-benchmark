#!/usr/bin/env python3
"""Archive a multi-decomp dashboard envelope into the per-release history set.

Every "Update dashboard multi-decomp envelope" CI step overwrites
public/benchmark-latest.json in place (see benchmark.yml). This script keeps
canonical release measurements in public/benchmark-history/<fission_version>.json
and updates the version-sorted index. Smoke/diagnostic envelopes are skipped by
default so a CI preview cannot masquerade as release history; they require the
explicit --include-diagnostic override.

Usage:
    # Archive the current envelope if it is official, valid, and publishable:
    python3 scripts/archive_benchmark_history.py

    # One-off backfill from git history (already-superseded versions only
    # exist as old commits of public/benchmark-latest.json):
    python3 scripts/archive_benchmark_history.py --backfill
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LATEST_PATH = REPO_ROOT / "public" / "benchmark-latest.json"
HISTORY_DIR = REPO_ROOT / "public" / "benchmark-history"
INDEX_PATH = HISTORY_DIR / "index.json"
DIAGNOSTIC_DIR = HISTORY_DIR / "diagnostic"

_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
_HISTORY_ROW_OMIT = {
    "decompiled_code",
    "decompiled_code_nir",
    "decompiled_code_hir",
    "oracle_evidence",
    "output_diagnostics",
    "bare_compile",
    "ast_similarity",
    "ged_metadata",
    "type_match_metadata",
}


def version_sort_key(version: str) -> tuple:
    m = _VERSION_RE.match(version)
    if not m:
        # Unparseable versions sort first (oldest/lowest priority).
        return (-1, -1, -1, version)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), "")


def write_index(versions: set[str]) -> None:
    ordered = sorted(versions, key=version_sort_key)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")
    print(f"index.json: {ordered}")


def canonical_release_reasons(envelope: dict) -> list[str]:
    run = envelope.get("run") or {}
    validity = envelope.get("validity") or {}
    reasons: list[str] = []
    if run.get("official") is not True:
        reasons.append("run.official != true")
    if validity.get("valid") is not True:
        reasons.append("validity.valid != true")
    if validity.get("publishable") is not True:
        reasons.append("validity.publishable != true")
    return reasons


def compact_history_envelope(envelope: dict) -> dict:
    """Drop generated/code-heavy row evidence not used by release trends."""
    compact = dict(envelope)
    compact["rows"] = [
        {key: value for key, value in row.items() if key not in _HISTORY_ROW_OMIT}
        for row in envelope.get("rows") or []
    ]
    return compact


def archive_diagnostic_envelope(envelope: dict, source_label: str) -> Path | None:
    version = (envelope.get("toolchain") or {}).get("fission_version")
    if not version:
        return None
    run_id = str((envelope.get("run") or {}).get("run_id") or "unknown")
    safe_run_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", run_id)
    DIAGNOSTIC_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DIAGNOSTIC_DIR / f"{version}--{safe_run_id}.json"
    out_path.write_text(
        json.dumps(compact_history_envelope(envelope), separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    entries = sorted(path.name for path in DIAGNOSTIC_DIR.glob("*.json") if path.name != "index.json")
    (DIAGNOSTIC_DIR / "index.json").write_text(
        json.dumps(entries, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"archived diagnostic {source_label} -> {out_path}")
    return out_path


def archive_envelope(
    envelope: dict,
    source_label: str,
    *,
    include_diagnostic: bool = False,
) -> str | None:
    version = (envelope.get("toolchain") or {}).get("fission_version")
    if not version:
        print(f"SKIP {source_label}: no toolchain.fission_version", file=sys.stderr)
        return None
    reasons = canonical_release_reasons(envelope)
    if reasons and not include_diagnostic:
        archive_diagnostic_envelope(envelope, source_label)
        print(
            f"SKIP {source_label}: {version} is not a canonical release "
            f"measurement ({'; '.join(reasons)})",
            file=sys.stderr,
        )
        return ""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    out_path = HISTORY_DIR / f"{version}.json"
    if out_path.exists() and not reasons:
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = None
        if existing and canonical_release_reasons(existing):
            archive_diagnostic_envelope(existing, f"replaced {out_path}")
    out_path.write_text(
        json.dumps(compact_history_envelope(envelope), separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"archived {source_label} -> {out_path} (fission_version={version})")
    return version


def cmd_archive_current(
    *,
    include_diagnostic: bool = False,
    input_path: Path = LATEST_PATH,
) -> int:
    if not input_path.exists():
        print(f"ERROR: {input_path} does not exist", file=sys.stderr)
        return 1
    envelope = json.loads(input_path.read_text(encoding="utf-8"))
    version = archive_envelope(
        envelope,
        str(input_path),
        include_diagnostic=include_diagnostic,
    )
    if version is None:
        return 1
    if version == "":
        return 0
    versions = {p.stem for p in HISTORY_DIR.glob("*.json") if p.stem != "index"}
    write_index(versions)
    return 0


def cmd_backfill(*, include_diagnostic: bool = False) -> int:
    """One-off: walk git history of public/benchmark-latest.json and archive
    the most recent snapshot for every distinct fission_version seen, so
    already-superseded releases (whose only trace is an old commit) get a
    permanent, independently-fetchable archive entry too."""
    log = subprocess.run(
        ["git", "log", "--format=%H", "--", "public/benchmark-latest.json"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    seen_versions: set[str] = set()
    archived: set[str] = set()
    for commit in log:  # newest first -> first hit per version is its final state
        show = subprocess.run(
            ["git", "show", f"{commit}:public/benchmark-latest.json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if show.returncode != 0:
            continue
        try:
            envelope = json.loads(show.stdout)
        except json.JSONDecodeError:
            continue
        version = (envelope.get("toolchain") or {}).get("fission_version")
        if not version or version in seen_versions:
            continue
        # In canonical mode, keep walking backwards until we find the newest
        # publishable official envelope for this version.  A later smoke run
        # must not hide an earlier release measurement.
        if canonical_release_reasons(envelope) and not include_diagnostic:
            continue
        seen_versions.add(version)
        out_path = HISTORY_DIR / f"{version}.json"
        if out_path.exists():
            if include_diagnostic:
                continue
            try:
                existing = json.loads(out_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                existing = {}
            # Preserve an existing canonical archive.  A diagnostic archive
            # from the old policy is replaced by the canonical git snapshot.
            if not canonical_release_reasons(existing):
                continue
        archived_version = archive_envelope(
            envelope,
            f"{commit[:8]}:public/benchmark-latest.json",
            include_diagnostic=include_diagnostic,
        )
        if archived_version:
            archived.add(version)

    versions = {p.stem for p in HISTORY_DIR.glob("*.json") if p.stem != "index"}
    write_index(versions)
    print(f"backfilled {len(archived)} version(s): {sorted(archived, key=version_sort_key)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=LATEST_PATH,
        help="Envelope to archive (default: public/benchmark-latest.json)",
    )
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Backfill from git history instead of archiving the current envelope",
    )
    parser.add_argument(
        "--include-diagnostic",
        action="store_true",
        help="Explicitly archive non-official/non-publishable snapshots",
    )
    args = parser.parse_args()
    return (
        cmd_backfill(include_diagnostic=args.include_diagnostic)
        if args.backfill
        else cmd_archive_current(
            include_diagnostic=args.include_diagnostic,
            input_path=args.input,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
