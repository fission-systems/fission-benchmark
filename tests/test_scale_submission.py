"""Local scale-result validation and compact dashboard publication contracts."""
from __future__ import annotations

import json
import gzip
import subprocess
import sys
from pathlib import Path

import pytest

from runner.scale_submission import (
    ScaleSubmissionError,
    build_dashboard_document,
    publish_dashboard_document,
    validate_submission,
)

ROOT = Path(__file__).resolve().parents[1]


def _lock() -> dict:
    return {
        "dataset_repo": "noelo-lab/decbench-dataset",
        "revision": "a" * 40,
        "configs": {
            "unoptimized": {
                "safe_resolved_functions": 2,
                "safe_binaries": 1,
                "safe_source_cfg_functions": 2,
            }
        },
    }


def _row(decompiler: str, project: str, symbol: str, **updates: object) -> dict:
    row = {
        "decompiler": decompiler,
        "function_name": f"decbench::{project}::app::{symbol}",
        "function_symbol": symbol,
        "project": project,
        "compiler_variant": "gcc -O0",
        "error": None,
        "fail_category": "no_wrapper",
        "fail_taxonomy": "clean",
        "semantic_score": None,
        "correctness_score": None,
        "time_ms": 100,
        "ged_score": 0.0,
        "type_match_score": 1.0,
        "recompilation_score": 0.5,
    }
    row.update(updates)
    return row


def _envelope() -> dict:
    rows = [
        _row(decompiler, project, symbol)
        for project, symbol in (("grep", "main"), ("gzip", "main"))
        for decompiler in ("fission", "ghidra")
    ]
    cells = [
        {
            "decompiler": row["decompiler"],
            "function_name": row["function_name"],
            "compiler_variant": row["compiler_variant"],
        }
        for row in rows
    ]
    return {
        "schema_version": 2,
        "run": {
            "run_id": "run-123",
            "started_at": "2026-08-06T00:00:00Z",
            "finished_at": "2026-08-06T01:00:00Z",
            "duration_ms": 3_600_000,
            "runner_commit": "b" * 40,
            "corpus": "scale",
            "matrix_profile": "decbench_scale_full",
            "official": False,
            "requested_run_mode": "local",
            "external_dataset": {
                "schema": "fission-scale-corpus-inventory-v1",
                "name": "decbench",
                "repository": "noelo-lab/decbench-dataset",
                "revision": "a" * 40,
                "license": "BSD-2-Clause",
                "config": "unoptimized",
                "selected_binaries": 1,
                "requested_functions": 2,
                "resolved_functions": 2,
                "source_cfg_functions": 2,
                "source_cfg_coverage": 1.0,
                "malware_included": False,
            },
        },
        "toolchain": {
            "fission_version": "v1.2.3",
            "fission_source": "release",
            "fission_git_sha": "c" * 40,
            "host": {"system": "Darwin", "cpu_count": 12},
        },
        "matrix": {
            "expected_decompilers": ["fission", "ghidra"],
            "expected_rows": 4,
            "observed_rows": 4,
            "expected_cells": cells,
        },
        "oracle": {"valid": False},
        "validity": {"valid": True, "publishable": False},
        "rows": rows,
    }


def test_scale_submission_builds_nonranking_compact_document() -> None:
    envelope = _envelope()
    validation = validate_submission(
        envelope, _lock(), expected_version="1.2.3"
    )
    document = build_dashboard_document(
        envelope,
        validation,
        source_asset="scale.json.gz",
        source_sha256="d" * 64,
        published_at="2026-08-06T02:00:00Z",
    )

    assert document["ranking"] is False
    assert document["matrix"]["subjects"] == 2
    assert document["matrix"]["observed_rows"] == 4
    assert document["by_decompiler"]["fission"]["clean_rate"] == 1.0
    assert document["by_decompiler"]["fission"]["ged"]["perfect_rate"] == 1.0
    assert len(document["projects"]) == 2


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda env: env["rows"].__setitem__(0, {**env["rows"][0], "semantic_score": 1.0}), "semantic"),
        (lambda env: env["run"]["external_dataset"].__setitem__("revision", "e" * 40), "revision"),
        (lambda env: env["rows"].pop(), "observed row count"),
        (lambda env: env["rows"][0].__setitem__("project", "mirai"), "malware"),
    ],
)
def test_scale_submission_rejects_boundary_drift(mutation, message: str) -> None:
    envelope = _envelope()
    mutation(envelope)
    with pytest.raises(ScaleSubmissionError, match=message):
        validate_submission(envelope, _lock(), expected_version="v1.2.3")


def test_scale_publication_keeps_versioned_history(tmp_path: Path) -> None:
    envelope = _envelope()
    validation = validate_submission(
        envelope, _lock(), expected_version="v1.2.3"
    )
    document = build_dashboard_document(
        envelope,
        validation,
        source_asset="scale.json.gz",
        source_sha256="d" * 64,
        published_at="2026-08-06T02:00:00Z",
    )
    paths = publish_dashboard_document(document, tmp_path)
    index = json.loads(
        (tmp_path / "unofficial-corpus-history" / "index.json").read_text()
    )

    assert len(paths) == 3
    assert index["entries"] == [
        {
            "version": "v1.2.3",
            "run_id": "run-123",
            "finished_at": "2026-08-06T01:00:00Z",
            "path": "v1.2.3--run-123.json",
            "subjects": 2,
            "rows": 4,
            "source_sha256": "d" * 64,
        }
    ]
    assert json.loads((tmp_path / "unofficial-corpus-latest.json").read_text())[
        "run"
    ]["run_id"] == "run-123"


def test_local_submit_helper_packages_validated_gzip_without_upload(
    tmp_path: Path,
) -> None:
    submission = tmp_path / "scale.json"
    lock = tmp_path / "lock.json"
    output = tmp_path / "assets"
    submission.write_text(json.dumps(_envelope()), encoding="utf-8")
    lock.write_text(json.dumps(_lock()), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "submit_scale_benchmark.py"),
            str(submission),
            "--fission-version",
            "v1.2.3",
            "--lock",
            str(lock),
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assets = list(output.glob("*.json.gz"))
    assert len(assets) == 1
    with gzip.open(assets[0], "rt", encoding="utf-8") as handle:
        assert json.load(handle)["run"]["run_id"] == "run-123"
    assert "Dry run; add --execute" in completed.stdout
