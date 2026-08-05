#!/usr/bin/env python3
"""Build a self-contained public re-evaluation kit from an official envelope."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runner.ged import extract_source_cfgs  # noqa: E402
from runner.preprocessed_tu import PREPROCESSED_TU_SCHEMA  # noqa: E402


EVAL_KIT_SCHEMA = "fission-eval-kit-v1"
PUBLIC_INDEX_SCHEMA = "fission-eval-kit-index-v1"
GUARDED_COUNTS = (
    "row_count",
    "subject_count",
    "decompiler_count",
    "binary_count",
    "source_cfg_count",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def corpus_relative_path(raw: str, split: str) -> str:
    """Normalize legacy absolute and modern relative corpus artifact paths."""
    normalized = raw.replace("\\", "/")
    marker = f"/corpus/{split}/"
    if marker in normalized:
        return normalized.split(marker, 1)[1]
    prefix = f"corpus/{split}/"
    if normalized.startswith(prefix):
        return normalized[len(prefix) :]
    return normalized.lstrip("/")


def serialize_cfg(graph: Any) -> dict[str, Any]:
    nodes = list(graph.nodes())
    indices = {node: index for index, node in enumerate(nodes)}
    return {
        "nodes": [
            {
                "id": index,
                "statements": [
                    repr(statement)
                    for statement in (getattr(node, "statements", None) or [])
                ],
                "in_degree": int(graph.in_degree(node)),
                "out_degree": int(graph.out_degree(node)),
            }
            for index, node in enumerate(nodes)
        ],
        "edges": sorted(
            [[indices[left], indices[right]] for left, right in graph.edges()]
        ),
    }


def assert_coverage_not_regressed(
    current: dict[str, Any], previous: dict[str, Any] | None
) -> None:
    if not previous:
        return
    current_contract = current.get("release_contract_id")
    previous_contract = previous.get("release_contract_id")
    if not current_contract or current_contract != previous_contract:
        return
    regressions = [
        f"{field}: {previous.get(field, 0)} -> {current.get(field, 0)}"
        for field in GUARDED_COUNTS
        if int(current.get(field, 0)) < int(previous.get(field, 0))
    ]
    if regressions:
        raise ValueError("eval-kit coverage regression: " + ", ".join(regressions))


def build_eval_kit(
    envelope_path: Path,
    output_dir: Path,
    public_index_path: Path,
    *,
    previous_index_path: Path | None = None,
    cfg_extractor: Callable[[str], dict[str, Any]] = extract_source_cfgs,
) -> dict[str, Any]:
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    run = envelope.get("run") or {}
    validity = envelope.get("validity") or {}
    matrix = envelope.get("matrix") or {}
    rows = list(envelope.get("rows") or [])
    release_contract = run.get("release_contract") or {}
    split = str(run.get("corpus") or "dev")

    if run.get("official") is not True or validity.get("publishable") is not True:
        raise ValueError("eval kit requires an official, publishable envelope")
    if not release_contract.get("id"):
        raise ValueError("eval kit requires a frozen release_contract")
    if len(rows) != int(matrix.get("expected_rows") or -1):
        raise ValueError("eval kit requires a complete expected row matrix")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path = output_dir / "rows.jsonl"
    normalized_rows: list[dict[str, Any]] = []
    binary_paths: set[str] = set()
    cfg_subjects: set[tuple[str, str]] = set()
    for source_row in rows:
        row = dict(source_row)
        binary_rel = corpus_relative_path(str(row.get("binary") or ""), split)
        if binary_rel:
            row["binary"] = binary_rel
            binary_paths.add(binary_rel)
        ged = dict(row.get("ged_metadata") or {})
        source_rel = corpus_relative_path(str(ged.get("source_path") or ""), split)
        if ged.get("source_basis") != "preprocessed_tu" or not source_rel:
            raise ValueError(
                f"{row.get('function_name')} lacks {PREPROCESSED_TU_SCHEMA} provenance"
            )
        ged["source_path"] = source_rel
        row["ged_metadata"] = ged
        cfg_subjects.add((source_rel, str(row.get("function_name") or "")))
        normalized_rows.append(row)

    with rows_path.open("w", encoding="utf-8") as handle:
        for row in normalized_rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            handle.write("\n")

    expected_cells_path = output_dir / "expected-cells.json"
    expected_cells_path.write_text(
        json.dumps(matrix.get("expected_cells") or [], indent=2) + "\n",
        encoding="utf-8",
    )

    binary_index: list[dict[str, Any]] = []
    for binary_rel in sorted(binary_paths):
        source = ROOT / "corpus" / split / binary_rel
        if not source.is_file():
            raise ValueError(f"eval-kit binary missing: {binary_rel}")
        destination = output_dir / binary_rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        binary_index.append(
            {
                "path": binary_rel,
                "sha256": sha256_file(destination),
                "size": destination.stat().st_size,
            }
        )
    (output_dir / "binary-index.json").write_text(
        json.dumps(binary_index, indent=2) + "\n", encoding="utf-8"
    )

    source_cfg_rows: list[dict[str, Any]] = []
    parsed_by_source: dict[str, dict[str, Any]] = {}
    copied_sources: set[str] = set()
    for source_rel, function_name in sorted(cfg_subjects):
        source_path = ROOT / "corpus" / split / source_rel
        if not source_path.is_file():
            raise ValueError(f"eval-kit preprocessed TU missing: {source_rel}")
        if source_rel not in copied_sources:
            destination = output_dir / source_rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination)
            copied_sources.add(source_rel)
        if source_rel not in parsed_by_source:
            parsed_by_source[source_rel] = cfg_extractor(str(source_path))
        cfgs = parsed_by_source[source_rel]
        graph = cfgs.get(function_name)
        if graph is None:
            raise ValueError(f"source CFG missing: {source_rel}:{function_name}")
        source_cfg_rows.append(
            {
                "source_path": source_rel,
                "function_name": function_name,
                "cfg": serialize_cfg(graph),
            }
        )
    source_cfg_path = output_dir / "source-cfgs.json"
    source_cfg_path.write_text(
        json.dumps(source_cfg_rows, indent=2) + "\n", encoding="utf-8"
    )

    subjects = {
        (str(row.get("function_name") or ""), str(row.get("compiler_variant") or ""))
        for row in normalized_rows
    }
    decompilers = sorted({str(row.get("decompiler") or "") for row in normalized_rows})
    release_version = str((envelope.get("toolchain") or {}).get("fission_version") or "")
    manifest: dict[str, Any] = {
        "schema": EVAL_KIT_SCHEMA,
        "release_version": release_version,
        "run_id": run.get("run_id"),
        "release_contract_id": release_contract["id"],
        "release_contract": release_contract,
        "source_envelope_sha256": sha256_file(envelope_path),
        "source_cfg_contract": PREPROCESSED_TU_SCHEMA,
        "row_count": len(normalized_rows),
        "subject_count": len(subjects),
        "decompiler_count": len(decompilers),
        "binary_count": len(binary_index),
        "source_cfg_count": len(source_cfg_rows),
        "decompilers": decompilers,
        "files": {},
    }
    for path in sorted(p for p in output_dir.rglob("*") if p.is_file()):
        relative = str(path.relative_to(output_dir))
        manifest["files"][relative] = {
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    public_index = {
        "schema": PUBLIC_INDEX_SCHEMA,
        **{field: manifest[field] for field in ("release_version", "run_id", "release_contract_id", *GUARDED_COUNTS)},
        "source_cfg_contract": PREPROCESSED_TU_SCHEMA,
        "manifest_sha256": sha256_file(manifest_path),
        "artifact_name": f"benchmark-eval-kit-{os.environ.get('GITHUB_RUN_ID') or run.get('run_id')}",
        "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
    }
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if repository and release_version:
        release_tag = f"benchmark-{release_version}"
        asset_name = f"fission-eval-kit-{release_version}.tar.gz"
        public_index.update(
            github_release_tag=release_tag,
            asset_name=asset_name,
            download_url=(
                f"https://github.com/{repository}/releases/download/"
                f"{release_tag}/{asset_name}"
            ),
        )
    previous = None
    if previous_index_path and previous_index_path.is_file():
        previous = json.loads(previous_index_path.read_text(encoding="utf-8"))
    assert_coverage_not_regressed(public_index, previous)
    public_index_path.parent.mkdir(parents=True, exist_ok=True)
    public_index_path.write_text(
        json.dumps(public_index, indent=2) + "\n", encoding="utf-8"
    )
    return public_index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--envelope", type=Path, default=Path("results/latest.json"))
    parser.add_argument("--output", type=Path, default=Path("results/eval-kit"))
    parser.add_argument(
        "--public-index", type=Path, default=Path("public/eval-kit-latest.json")
    )
    parser.add_argument("--previous-index", type=Path)
    args = parser.parse_args()
    index = build_eval_kit(
        args.envelope,
        args.output,
        args.public_index,
        previous_index_path=args.previous_index,
    )
    print(
        f"eval kit: rows={index['row_count']} subjects={index['subject_count']} "
        f"binaries={index['binary_count']} source_cfgs={index['source_cfg_count']}"
    )


if __name__ == "__main__":
    main()
