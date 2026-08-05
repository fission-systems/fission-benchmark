import json
from pathlib import Path
from types import SimpleNamespace

import scripts.archive_benchmark_history as archive


def envelope(*, official: bool, valid: bool, publishable: bool) -> dict:
    return {
        "toolchain": {"fission_version": "v1.2.3"},
        "run": {"official": official},
        "validity": {"valid": valid, "publishable": publishable},
        "rows": [],
    }


def test_diagnostic_snapshot_is_not_archived_by_default(
    tmp_path: Path, monkeypatch,
) -> None:
    monkeypatch.setattr(archive, "HISTORY_DIR", tmp_path)
    monkeypatch.setattr(archive, "DIAGNOSTIC_DIR", tmp_path / "diagnostic")

    result = archive.archive_envelope(
        envelope(official=False, valid=True, publishable=False),
        "diagnostic.json",
    )

    assert result == ""
    assert not (tmp_path / "v1.2.3.json").exists()
    archived = list((tmp_path / "diagnostic").glob("v1.2.3--*.json"))
    assert len(archived) == 1


def test_only_valid_publishable_official_snapshot_is_canonical(
    tmp_path: Path, monkeypatch,
) -> None:
    monkeypatch.setattr(archive, "HISTORY_DIR", tmp_path)
    monkeypatch.setattr(archive, "DIAGNOSTIC_DIR", tmp_path / "diagnostic")
    data = envelope(official=True, valid=True, publishable=True)

    assert archive.canonical_release_reasons(data) == []
    assert archive.archive_envelope(data, "official.json") == "v1.2.3"
    assert (tmp_path / "v1.2.3.json").is_file()


def test_history_archive_drops_generated_code_evidence(
    tmp_path: Path, monkeypatch,
) -> None:
    monkeypatch.setattr(archive, "HISTORY_DIR", tmp_path)
    monkeypatch.setattr(archive, "DIAGNOSTIC_DIR", tmp_path / "diagnostic")
    data = envelope(official=True, valid=True, publishable=True)
    data["rows"] = [{
        "decompiler": "fission",
        "function_name": "f",
        "compiler_variant": "gcc -O0",
        "semantic_score": 1.0,
        "time_ms": 10,
        "decompiled_code": "large generated code",
        "oracle_evidence": {"large": "payload"},
    }]

    archive.archive_envelope(data, "official.json")
    stored = json.loads((tmp_path / "v1.2.3.json").read_text())

    assert stored["rows"][0]["semantic_score"] == 1.0
    assert stored["rows"][0]["time_ms"] == 10
    assert "decompiled_code" not in stored["rows"][0]
    assert "oracle_evidence" not in stored["rows"][0]


def test_diagnostic_archive_requires_explicit_override(
    tmp_path: Path, monkeypatch,
) -> None:
    monkeypatch.setattr(archive, "HISTORY_DIR", tmp_path)
    monkeypatch.setattr(archive, "DIAGNOSTIC_DIR", tmp_path / "diagnostic")
    data = envelope(official=False, valid=True, publishable=False)

    result = archive.archive_envelope(
        data,
        "diagnostic.json",
        include_diagnostic=True,
    )

    assert result == "v1.2.3"
    assert (tmp_path / "v1.2.3.json").is_file()


def test_backfill_finds_older_official_snapshot_behind_newer_smoke(
    tmp_path: Path, monkeypatch,
) -> None:
    history_dir = tmp_path / "history"
    history_dir.mkdir()
    diagnostic = envelope(official=False, valid=True, publishable=False)
    official = envelope(official=True, valid=True, publishable=True)
    (history_dir / "v1.2.3.json").write_text(json.dumps(diagnostic))

    def fake_run(args, **_kwargs):
        if args[1] == "log":
            return SimpleNamespace(stdout="newest\nrelease\n", returncode=0)
        payload = diagnostic if args[2].startswith("newest:") else official
        return SimpleNamespace(stdout=json.dumps(payload), returncode=0)

    monkeypatch.setattr(archive, "HISTORY_DIR", history_dir)
    monkeypatch.setattr(archive, "DIAGNOSTIC_DIR", history_dir / "diagnostic")
    monkeypatch.setattr(archive, "INDEX_PATH", history_dir / "index.json")
    monkeypatch.setattr(archive.subprocess, "run", fake_run)

    assert archive.cmd_backfill() == 0
    stored = json.loads((history_dir / "v1.2.3.json").read_text())
    assert stored["run"]["official"] is True
    assert json.loads((history_dir / "index.json").read_text()) == ["v1.2.3"]
