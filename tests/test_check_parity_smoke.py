import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _stage(
    total: int = 10,
    match: int = 5,
    mismatch: int = 5,
    fetch_error: int = 0,
) -> dict:
    comparable = match + mismatch
    return {
        "total": total,
        "match": match,
        "mismatch": mismatch,
        "fetch_error": fetch_error,
        "error_or_other": total - comparable,
        "match_rate": match / comparable if comparable else None,
        "mismatch_rate": mismatch / comparable if comparable else None,
        "usable_coverage": comparable / total if total else None,
        "match_rate_attempted": match / total if total else None,
    }


def test_check_parity_smoke_ok(tmp_path: Path) -> None:
    path = Path(__file__).resolve().parents[1] / "scripts" / "check_parity_smoke.py"
    mod = _load("check_parity_smoke", path)

    telemetry = {
        "total_rows": 40,
        "canonicalize_mode": "strict",
        "by_status": {"match": 20, "mismatch": 20},
        "reliability": {
            "usable_coverage": 1.0,
            "match_rate_attempted": 0.5,
            "fetch_error_rate": 0.0,
        },
        "stages": {
            "assembly_parity": _stage(),
            "cfg_parity": _stage(),
            "pcode_parity": _stage(),
            "function_discovery": _stage(total=10, match=0, mismatch=10),
            "decode_parity": {
                "total": 10,
                "match": 0,
                "mismatch": 0,
                "skipped": 10,
                "fetch_error": 0,
                "usable_coverage": 0.0,
            },
        },
    }
    p = tmp_path / "t.json"
    p.write_text(json.dumps(telemetry), encoding="utf-8")
    assert mod.main([str(p)]) == 0


def test_check_parity_smoke_requires_fresh_provenance(tmp_path: Path) -> None:
    path = Path(__file__).resolve().parents[1] / "scripts" / "check_parity_smoke.py"
    mod = _load("check_parity_smoke_provenance", path)
    telemetry = {
        "total_rows": 40,
        "canonicalize_mode": "strict",
        "by_status": {"match": 20, "mismatch": 20},
        "reliability": {"usable_coverage": 1.0, "fetch_error_rate": 0.0},
        "stages": {
            "assembly_parity": _stage(),
            "cfg_parity": _stage(),
            "pcode_parity": _stage(),
            "function_discovery": _stage(),
        },
        "provenance": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "runner_commit": "abc123",
            "sources": [
                {
                    "path": f"results/{stage}/latest.jsonl",
                    "stage": stage,
                    "sha256": "0" * 64,
                    "modified_at": datetime.now(timezone.utc).isoformat(),
                }
                for stage in (
                    "assembly_parity",
                    "cfg_parity",
                    "pcode_parity",
                    "function_discovery",
                )
            ],
        },
    }
    p = tmp_path / "fresh.json"
    p.write_text(json.dumps(telemetry), encoding="utf-8")
    assert mod.main([str(p), "--require-provenance", "--max-age-hours", "1"]) == 0

    telemetry["provenance"]["generated_at"] = (
        datetime.now(timezone.utc) - timedelta(hours=2)
    ).isoformat()
    p.write_text(json.dumps(telemetry), encoding="utf-8")
    assert mod.main([str(p), "--require-provenance", "--max-age-hours", "1"]) == 1

    telemetry["provenance"]["generated_at"] = datetime.now(timezone.utc).isoformat()
    telemetry["provenance"]["sources"][1]["modified_at"] = (
        datetime.now(timezone.utc) - timedelta(hours=2)
    ).isoformat()
    p.write_text(json.dumps(telemetry), encoding="utf-8")
    assert mod.main([str(p), "--require-provenance", "--max-source-age-hours", "1"]) == 1


def test_check_parity_smoke_fails_when_all_errors(tmp_path: Path) -> None:
    path = Path(__file__).resolve().parents[1] / "scripts" / "check_parity_smoke.py"
    mod = _load("check_parity_smoke2", path)

    telemetry = {
        "total_rows": 3,
        "canonicalize_mode": "strict",
        "by_status": {"fetch_error": 3},
        "reliability": {"usable_coverage": 0.0, "fetch_error_rate": 1.0},
        "stages": {
            "assembly_parity": _stage(total=1, match=0, mismatch=0, fetch_error=1),
            "cfg_parity": _stage(total=1, match=0, mismatch=0, fetch_error=1),
            "pcode_parity": _stage(total=1, match=0, mismatch=0, fetch_error=1),
            "function_discovery": _stage(total=1, match=0, mismatch=0, fetch_error=1),
        },
    }
    # zero comparable → coverage 0
    for st in telemetry["stages"].values():
        st["usable_coverage"] = 0.0
        st["match_rate"] = None
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(telemetry), encoding="utf-8")
    assert mod.main([str(p)]) == 1


def test_check_parity_smoke_fails_on_loose_mode(tmp_path: Path) -> None:
    path = Path(__file__).resolve().parents[1] / "scripts" / "check_parity_smoke.py"
    mod = _load("check_parity_smoke3", path)
    telemetry = {
        "total_rows": 40,
        "canonicalize_mode": "loose",
        "by_status": {"match": 20, "mismatch": 20},
        "reliability": {"usable_coverage": 1.0, "fetch_error_rate": 0.0},
        "stages": {
            "assembly_parity": _stage(),
            "cfg_parity": _stage(),
            "pcode_parity": _stage(),
            "function_discovery": _stage(),
        },
    }
    p = tmp_path / "loose.json"
    p.write_text(json.dumps(telemetry), encoding="utf-8")
    assert mod.main([str(p)]) == 1


def test_check_reliability_rejects_decode_match(tmp_path: Path) -> None:
    path = Path(__file__).resolve().parents[1] / "scripts" / "check_reliability.py"
    mod = _load("check_reliability", path)
    telemetry = {
        "total_rows": 40,
        "canonicalize_mode": "strict",
        "reliability_policy": "conservative",
        "by_status": {"match": 10, "mismatch": 30},
        "reliability": {"usable_coverage": 0.95, "fetch_error_rate": 0.0},
        "reliability_critique": {"warnings": []},
        "publishable": {
            "stages": {
                "assembly_parity": {},
                "pcode_parity": {},
                "cfg_parity": {},
                "function_discovery": {},
            },
            "match_rate_comparable": 0.2,
        },
        "stages": {
            "assembly_parity": {
                **_stage(total=10, match=8, mismatch=2),
                "primary_quality": True,
            },
            "pcode_parity": {
                **_stage(total=10, match=0, mismatch=10),
                "primary_quality": True,
                "dual": {
                    "n": 10,
                    "opcode_sequence_match_rate": 0.9,
                    "loose_full_match_rate": 0.6,
                    "strict_full_match_rate": 0.0,
                },
            },
            "cfg_parity": {
                **_stage(total=10, match=1, mismatch=9),
                "primary_quality": True,
            },
            "function_discovery": {
                **_stage(total=10, match=0, mismatch=10),
                "primary_quality": True,
                "dual": {"n": 10, "mean_presence_recall": 0.9, "mean_manifest_recall": 1.0},
            },
            "decode_parity": {
                "total": 10,
                "match": 3,
                "mismatch": 0,
                "skipped": 7,
                "usable_coverage": 0.3,
            },
        },
    }
    p = tmp_path / "dec.json"
    p.write_text(json.dumps(telemetry), encoding="utf-8")
    assert mod.main([str(p)]) == 1
