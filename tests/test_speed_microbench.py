import json

from runner.speed_microbench import (
    _archive_release_snapshot,
    _parse_bytes,
    _parse_docker_stats,
    _resource_summary,
    _summarize_by_decompiler,
)


def test_parse_docker_stats_sample() -> None:
    sample = _parse_docker_stats(
        '\x1b[H{"CPUPerc":"128.50%","MemUsage":"512.5MiB / 7.75GiB",'
        '"MemPerc":"6.46%","PIDs":"17"}\x1b[K'
    )

    assert sample is not None
    assert sample["cpu_percent"] == 128.5
    assert sample["memory_bytes"] == round(512.5 * 1024 * 1024)
    assert sample["memory_percent"] == 6.46
    assert sample["pids"] == 17


def test_parse_bytes_supports_decimal_and_iec_units() -> None:
    assert _parse_bytes("1.5GiB") == round(1.5 * 1024**3)
    assert _parse_bytes("250 MB") == 250_000_000
    assert _parse_bytes("unknown") is None


def test_resource_summary_keeps_cpu_and_sampled_memory_distinct() -> None:
    summary = _resource_summary(
        [
            {"cpu_percent": 50.0, "memory_bytes": 100, "memory_percent": 1.0},
            {"cpu_percent": 150.0, "memory_bytes": 300, "memory_percent": 3.0},
        ]
    )

    assert summary["available"] is True
    assert summary["mean_cpu_percent"] == 100.0
    assert summary["peak_cpu_percent"] == 150.0
    assert summary["mean_memory_bytes"] == 200
    assert summary["peak_memory_bytes"] == 300


def test_microbench_rollup_summarizes_resource_trials() -> None:
    subjects = [
        {
            "decompiler": "fission",
            "trials": [
                {
                    "phase": "cold",
                    "adapter_ms": 40.0,
                    "resources": {
                        "available": True,
                        "samples": 2,
                        "mean_cpu_percent": 80.0,
                        "peak_cpu_percent": 120.0,
                        "peak_memory_bytes": 500,
                        "peak_memory_percent": 5.0,
                    },
                },
                {
                    "phase": "warm",
                    "adapter_ms": 10.0,
                    "resources": {
                        "available": True,
                        "samples": 1,
                        "mean_cpu_percent": 40.0,
                        "peak_cpu_percent": 60.0,
                        "peak_memory_bytes": 700,
                        "peak_memory_percent": 7.0,
                    },
                },
            ],
        }
    ]

    summary = _summarize_by_decompiler(subjects)["fission"]
    resources = summary["resources"]
    assert resources["cold"]["mean_cpu_percent"] == 80.0
    assert resources["warm"]["peak_memory_bytes"] == 700
    assert resources["all"]["mean_cpu_percent"] == 60.0
    assert resources["all"]["peak_cpu_percent"] == 120.0
    assert resources["all"]["peak_memory_bytes"] == 700
    assert resources["all"]["samples"] == 3


def test_release_speed_snapshot_is_version_keyed(tmp_path) -> None:
    doc = {
        "schema": "speed-microbench-v2",
        "toolchain": {"fission_version": "v1.2.3"},
        "by_decompiler": {"fission": {}},
    }

    assert _archive_release_snapshot(doc, tmp_path) == "v1.2.3"
    assert json.loads((tmp_path / "v1.2.3.json").read_text()) == doc
    assert json.loads((tmp_path / "index.json").read_text()) == ["v1.2.3"]


def test_release_speed_snapshot_skips_latest_alias(tmp_path) -> None:
    doc = {"toolchain": {"fission_version": "latest"}}

    assert _archive_release_snapshot(doc, tmp_path) is None
    assert list(tmp_path.iterdir()) == []
