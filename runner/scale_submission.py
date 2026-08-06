"""Validate and compact a local DecBench-scale benchmark submission.

Raw per-function output is intentionally kept as a GitHub Release asset.  The
dashboard receives only this module's small, non-ranking aggregate document.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MALWARE_PROJECTS = frozenset({"dexter", "minipig", "mirai", "mydoom", "x0r-usb"})
VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class ScaleSubmissionError(ValueError):
    """The local result does not satisfy the non-ranking publication contract."""


def normalize_version(value: object) -> str:
    match = VERSION_RE.fullmatch(str(value or "").strip())
    if not match:
        raise ScaleSubmissionError(f"invalid Fission release version: {value!r}")
    return "v" + ".".join(match.groups())


def load_json(path: Path) -> dict[str, Any]:
    try:
        handle = (
            gzip.open(path, "rt", encoding="utf-8")
            if path.suffix == ".gz"
            else path.open("rt", encoding="utf-8")
        )
        with handle:
            value = json.load(handle)
    except (OSError, ValueError) as exc:
        raise ScaleSubmissionError(f"cannot read submission {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ScaleSubmissionError("submission must be a benchmark envelope object")
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cell(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("decompiler") or ""),
        str(row.get("function_name") or ""),
        str(row.get("compiler_variant") or ""),
    )


def _clean(row: dict[str, Any]) -> bool:
    return not row.get("error") and row.get("fail_category") != "adapter_error"


def _project(row: dict[str, Any]) -> str:
    explicit = str(row.get("project") or "")
    if explicit:
        return explicit
    parts = str(row.get("function_name") or "").split("::", 3)
    return parts[1] if len(parts) == 4 and parts[0] == "decbench" else "unknown"


def validate_submission(
    envelope: dict[str, Any],
    lock: dict[str, Any],
    *,
    expected_version: str,
    min_clean_coverage: float = 0.5,
) -> dict[str, Any]:
    """Fail closed on provenance and matrix drift; failures remain measurements."""
    errors: list[str] = []
    run = envelope.get("run") or {}
    toolchain = envelope.get("toolchain") or {}
    matrix = envelope.get("matrix") or {}
    rows = envelope.get("rows") or []
    dataset = run.get("external_dataset") or {}
    config_name = str(dataset.get("config") or "")
    config = (lock.get("configs") or {}).get(config_name) or {}
    version = normalize_version(toolchain.get("fission_version"))

    if envelope.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    if str(run.get("corpus") or "") != "scale":
        errors.append("run.corpus must be scale")
    if str(run.get("matrix_profile") or "") != "decbench_scale_full":
        errors.append("matrix profile must be decbench_scale_full")
    if run.get("official") is not False:
        errors.append("scale submission must remain non-official")
    if str(run.get("requested_run_mode") or "") != "local":
        errors.append("scale submission must come from run_mode=local")
    if str(toolchain.get("fission_source") or "") != "release":
        errors.append("Fission source must be release")
    if version != normalize_version(expected_version):
        errors.append(f"Fission version {version} does not match {expected_version}")

    if str(dataset.get("name") or "") != "decbench":
        errors.append("external dataset must be decbench")
    if str(dataset.get("repository") or "") != str(lock.get("dataset_repo") or ""):
        errors.append("DecBench repository does not match the lock")
    if str(dataset.get("revision") or "") != str(lock.get("revision") or ""):
        errors.append("DecBench revision does not match the lock")
    if dataset.get("malware_included") is not False:
        errors.append("malware-inclusive scale results cannot be published")
    if not config:
        errors.append(f"unknown locked dataset config {config_name!r}")

    expected_subjects = int(config.get("safe_resolved_functions") or 0)
    expected_binaries = int(config.get("safe_binaries") or 0)
    expected_cfg = int(config.get("safe_source_cfg_functions") or 0)
    if not expected_subjects or not expected_binaries or not expected_cfg:
        errors.append("dataset lock lacks safe resolved/binary/CFG counts")
    if int(dataset.get("resolved_functions") or 0) != expected_subjects:
        errors.append("resolved function count does not match the lock")
    if int(dataset.get("selected_binaries") or 0) != expected_binaries:
        errors.append("selected binary count does not match the lock")
    if int(dataset.get("source_cfg_functions") or 0) != expected_cfg:
        errors.append("published source-CFG count does not match the lock")

    if not isinstance(rows, list) or not rows:
        errors.append("submission has no rows")
        rows = []
    decompilers = [str(value) for value in matrix.get("expected_decompilers") or []]
    if set(decompilers) != {"fission", "ghidra"} or len(decompilers) != 2:
        errors.append("scale publication requires exactly fission and ghidra")
    expected_rows = expected_subjects * len(decompilers)
    if int(matrix.get("expected_rows") or 0) != expected_rows:
        errors.append("matrix expected row count does not match the locked cohort")
    if int(matrix.get("observed_rows") or 0) != len(rows):
        errors.append("matrix observed row count does not match rows")
    if len(rows) != expected_rows:
        errors.append("submission is not the complete scale matrix")

    observed_cells = [_cell(row) for row in rows if isinstance(row, dict)]
    if len(set(observed_cells)) != len(observed_cells):
        errors.append("submission contains duplicate matrix cells")
    expected_cells = [
        _cell(cell)
        for cell in matrix.get("expected_cells") or []
        if isinstance(cell, dict)
    ]
    if len(expected_cells) != expected_rows or set(expected_cells) != set(observed_cells):
        errors.append("observed cells do not exactly match the planned matrix")

    subjects: set[str] = set()
    clean_by_tool: Counter[str] = Counter()
    attempted_by_tool: Counter[str] = Counter()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("every row must be an object")
            continue
        decompiler, subject, variant = _cell(row)
        attempted_by_tool[decompiler] += 1
        if _clean(row):
            clean_by_tool[decompiler] += 1
        subjects.add(subject)
        if not subject.startswith("decbench::") or len(subject.split("::", 3)) != 4:
            errors.append(f"invalid namespaced subject: {subject!r}")
            break
        if variant != "gcc -O0":
            errors.append(f"unexpected compiler variant: {variant!r}")
            break
        if _project(row) in MALWARE_PROJECTS:
            errors.append("real-malware project appears in the submitted rows")
            break
        if row.get("semantic_score") is not None or row.get("correctness_score") is not None:
            errors.append("scale rows must not contain semantic ranking scores")
            break
    if len(subjects) != expected_subjects:
        errors.append("unique subject count does not match the locked cohort")
    for decompiler in decompilers:
        attempted = attempted_by_tool[decompiler]
        coverage = clean_by_tool[decompiler] / attempted if attempted else 0.0
        if coverage < min_clean_coverage:
            errors.append(
                f"{decompiler} clean coverage {coverage:.2%} is below "
                f"{min_clean_coverage:.2%}"
            )

    run_id = str(run.get("run_id") or "")
    if not run_id or not SAFE_ID_RE.fullmatch(run_id):
        errors.append("run_id is missing or unsafe")
    for field in ("started_at", "finished_at", "runner_commit"):
        if not run.get(field):
            errors.append(f"run.{field} is required")

    if errors:
        raise ScaleSubmissionError("; ".join(dict.fromkeys(errors)))
    return {
        "version": version,
        "run_id": run_id,
        "subjects": len(subjects),
        "rows": len(rows),
        "decompilers": decompilers,
        "clean_by_decompiler": dict(clean_by_tool),
    }


def _numbers(rows: list[dict[str, Any]], field: str) -> list[float]:
    output: list[float] = []
    for row in rows:
        value = row.get(field)
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            output.append(float(value))
    return output


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(quantile * len(ordered)) - 1))
    return round(ordered[index], 6)


def _metric(values: list[float], *, perfect: float, lower_is_better: bool = False) -> dict[str, Any]:
    if lower_is_better:
        perfect_rows = sum(value <= perfect for value in values)
    else:
        perfect_rows = sum(value >= perfect for value in values)
    return {
        "tested_rows": len(values),
        "mean": _mean(values),
        "perfect_rows": perfect_rows,
        "perfect_rate": round(perfect_rows / len(values), 6) if values else None,
    }


def build_dashboard_document(
    envelope: dict[str, Any],
    validation: dict[str, Any],
    *,
    source_asset: str,
    source_sha256: str,
    published_at: str | None = None,
) -> dict[str, Any]:
    rows = [row for row in envelope["rows"] if isinstance(row, dict)]
    run = envelope["run"]
    dataset = run["external_dataset"]
    by_decompiler: dict[str, Any] = {}
    for decompiler in validation["decompilers"]:
        tool_rows = [row for row in rows if row.get("decompiler") == decompiler]
        clean_rows = [row for row in tool_rows if _clean(row)]
        times = _numbers(clean_rows, "time_ms")
        failures: Counter[str] = Counter()
        for row in tool_rows:
            if _clean(row):
                failures["clean"] += 1
            else:
                failures[
                    str(row.get("fail_taxonomy") or row.get("fail_category") or "adapter_error")
                ] += 1
        by_decompiler[decompiler] = {
            "attempted_rows": len(tool_rows),
            "clean_rows": len(clean_rows),
            "clean_rate": round(len(clean_rows) / len(tool_rows), 6),
            "latency_ms": {
                "measured_rows": len(times),
                "mean": _mean(times),
                "p50": _percentile(times, 0.5),
                "p95": _percentile(times, 0.95),
                "total": round(sum(times), 3),
            },
            "ged": _metric(_numbers(tool_rows, "ged_score"), perfect=0, lower_is_better=True),
            "type_match": _metric(_numbers(tool_rows, "type_match_score"), perfect=1),
            "recompilation": _metric(
                _numbers(tool_rows, "recompilation_score"), perfect=1
            ),
            "failures": dict(sorted(failures.items())),
        }

    project_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        project_rows[_project(row)].append(row)
    projects = []
    for project, values in project_rows.items():
        subjects = {str(row.get("function_name") or "") for row in values}
        clean = sum(_clean(row) for row in values)
        projects.append(
            {
                "project": project,
                "subjects": len(subjects),
                "rows": len(values),
                "clean_rows": clean,
                "clean_rate": round(clean / len(values), 6),
            }
        )
    projects.sort(key=lambda value: (-value["subjects"], value["project"]))

    return {
        "schema": "fission-unofficial-corpus-v1",
        "ranking": False,
        "publication": {
            "published_at": published_at
            or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source_asset": source_asset,
            "source_sha256": source_sha256,
        },
        "run": {
            "run_id": run["run_id"],
            "started_at": run["started_at"],
            "finished_at": run["finished_at"],
            "duration_ms": run.get("duration_ms"),
            "runner_commit": run["runner_commit"],
            "matrix_profile": run["matrix_profile"],
            "fission_version": validation["version"],
        },
        "toolchain": {
            "fission_source": envelope["toolchain"].get("fission_source"),
            "fission_git_sha": envelope["toolchain"].get("fission_git_sha"),
            "host": envelope["toolchain"].get("host") or {},
        },
        "corpus": dataset,
        "matrix": {
            "subjects": validation["subjects"],
            "expected_rows": validation["rows"],
            "observed_rows": len(rows),
            "completion_rate": 1.0,
            "decompilers": validation["decompilers"],
        },
        "by_decompiler": by_decompiler,
        "projects": projects,
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def publish_dashboard_document(document: dict[str, Any], public_root: Path) -> list[Path]:
    version = normalize_version(document["run"]["fission_version"])
    run_id = str(document["run"]["run_id"])
    if not SAFE_ID_RE.fullmatch(run_id):
        raise ScaleSubmissionError("unsafe run_id for history path")
    history_root = public_root / "unofficial-corpus-history"
    history_name = f"{version}--{run_id}.json"
    history_path = history_root / history_name
    latest_path = public_root / "unofficial-corpus-latest.json"
    index_path = history_root / "index.json"

    if history_path.exists():
        existing = json.loads(history_path.read_text(encoding="utf-8"))
        if existing != document:
            raise ScaleSubmissionError("history run_id already exists with different data")
    else:
        _write_json(history_path, document)
    _write_json(latest_path, document)

    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        index = {"schema": "fission-unofficial-corpus-index-v1", "entries": []}
    entries = [
        entry
        for entry in index.get("entries") or []
        if entry.get("run_id") != run_id
    ]
    entries.append(
        {
            "version": version,
            "run_id": run_id,
            "finished_at": document["run"]["finished_at"],
            "path": history_name,
            "subjects": document["matrix"]["subjects"],
            "rows": document["matrix"]["observed_rows"],
            "source_sha256": document["publication"]["source_sha256"],
        }
    )
    entries.sort(key=lambda entry: (entry.get("finished_at") or "", entry["run_id"]))
    _write_json(
        index_path,
        {"schema": "fission-unofficial-corpus-index-v1", "entries": entries},
    )
    return [latest_path, history_path, index_path]
