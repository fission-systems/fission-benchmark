from pathlib import Path

import networkx as nx
import pytest

from runner.checkpoint import BenchmarkCheckpoint
from runner.ged import compute_ged
from runner.recompilation import measure_recompilation
from runner.scoring import FunctionScore


def _score(name: str = "foo") -> FunctionScore:
    return FunctionScore(
        decompiler="fission",
        function_name=name,
        compiler_variant="gcc -O2",
        source_similarity=0.5,
        goto_count=0,
        nesting_depth=1,
        time_ms=10,
    )


def test_checkpoint_round_trip_and_deduplication(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    contract = {"expected_cells": [["fission", "foo", "gcc -O2"]]}
    first = BenchmarkCheckpoint(path, contract=contract)
    first.append([_score(), _score()])

    resumed = BenchmarkCheckpoint(path, contract=contract)

    assert len(resumed.recovered_rows) == 1
    assert resumed.contains(("fission", "foo", "gcc -O2"))
    assert len(path.read_text().splitlines()) == 2


def test_checkpoint_rejects_a_different_contract(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    BenchmarkCheckpoint(path, contract={"profile": "release"})

    with pytest.raises(ValueError, match="does not match"):
        BenchmarkCheckpoint(path, contract={"profile": "smoke"})


def test_ged_content_cache_skips_second_metric_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FISSION_BENCHMARK_CACHE_DIR", str(tmp_path / "cache"))
    calls = 0

    def fake_vj_ged(_source, _decompiled):
        nonlocal calls
        calls += 1
        return 2.0

    monkeypatch.setattr("runner.ged._get_vj_ged", lambda: fake_vj_ged)
    source = nx.DiGraph()
    source.add_edge("a", "b")
    decompiled = nx.DiGraph()
    decompiled.add_edge("a", "b")

    first = compute_ged(source, decompiled)
    second = compute_ged(source, decompiled)

    assert first["ged"] == second["ged"] == 2.0
    assert first["cache"]["hit"] is False
    assert second["cache"]["hit"] is True
    assert calls == 1


def test_recompilation_content_cache_skips_second_measurement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FISSION_BENCHMARK_CACHE_DIR", str(tmp_path / "cache"))
    binary = tmp_path / "fixture.bin"
    binary.write_bytes(b"fixture")
    calls = 0

    def fake_measure(*args, **kwargs):
        nonlocal calls
        calls += 1
        return 0.75, {"schema": "recompilation-bytematch-v1", "category": "ok"}

    monkeypatch.setattr("runner.recompilation._measure_recompilation_uncached", fake_measure)
    kwargs = {
        "function_name": "foo",
        "binary_path": binary,
        "function_address": "0x1000",
        "compiler_variant": "gcc -O2",
    }
    first = measure_recompilation("int foo(void) { return 1; }", **kwargs)
    second = measure_recompilation("int foo(void) { return 1; }", **kwargs)

    assert first[0] == second[0] == 0.75
    assert first[1]["cache"]["hit"] is False
    assert second[1]["cache"]["hit"] is True
    assert calls == 1
