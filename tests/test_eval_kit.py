import json
from pathlib import Path

import networkx as nx
import pytest

import scripts.build_eval_kit as eval_kit


def _envelope() -> dict:
    base_row = {
        "function_name": "foo",
        "compiler_variant": "gcc -O2",
        "binary": "binaries/c/foo.exe",
        "corpus": "dev",
        "ged_metadata": {
            "source_basis": "preprocessed_tu",
            "source_path": "preprocessed/c/foo.i",
        },
    }
    rows = [
        {**base_row, "decompiler": "fission"},
        {**base_row, "decompiler": "ghidra"},
    ]
    return {
        "schema_version": 2,
        "run": {
            "official": True,
            "run_id": "run-1",
            "corpus": "dev",
            "release_contract": {"id": "release-baseline-v1"},
        },
        "toolchain": {"fission_version": "v1.2.3"},
        "validity": {"publishable": True},
        "matrix": {
            "expected_rows": 2,
            "expected_cells": [
                {
                    "decompiler": row["decompiler"],
                    "function_name": "foo",
                    "compiler_variant": "gcc -O2",
                }
                for row in rows
            ],
        },
        "rows": rows,
    }


def test_build_eval_kit_is_self_contained(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(eval_kit, "ROOT", tmp_path)
    corpus = tmp_path / "corpus/dev"
    binary = corpus / "binaries/c/foo.exe"
    source = corpus / "preprocessed/c/foo.i"
    binary.parent.mkdir(parents=True)
    source.parent.mkdir(parents=True)
    binary.write_bytes(b"MZfixture")
    source.write_text("int foo(void) { return 1; }\n")
    envelope_path = tmp_path / "latest.json"
    envelope_path.write_text(json.dumps(_envelope()))
    graph = nx.DiGraph()
    graph.add_edge("entry", "return")
    extractor_calls = 0

    def extractor(_path: str):
        nonlocal extractor_calls
        extractor_calls += 1
        return {"foo": graph}

    public_index = tmp_path / "public/eval-kit-latest.json"
    result = eval_kit.build_eval_kit(
        envelope_path,
        tmp_path / "kit",
        public_index,
        cfg_extractor=extractor,
    )

    assert result["row_count"] == 2
    assert result["subject_count"] == 1
    assert result["binary_count"] == 1
    assert result["source_cfg_count"] == 1
    assert extractor_calls == 1
    assert (tmp_path / "kit/binaries/c/foo.exe").read_bytes() == b"MZfixture"
    assert (tmp_path / "kit/preprocessed/c/foo.i").is_file()
    assert (tmp_path / "kit/source-cfgs.json").is_file()
    assert json.loads(public_index.read_text())["manifest_sha256"]


def test_eval_kit_coverage_guard_rejects_regression() -> None:
    previous = {
        "release_contract_id": "release-baseline-v1",
        "row_count": 432,
        "subject_count": 216,
        "decompiler_count": 2,
        "binary_count": 36,
        "source_cfg_count": 216,
    }
    current = {**previous, "source_cfg_count": 215}

    with pytest.raises(ValueError, match="source_cfg_count: 216 -> 215"):
        eval_kit.assert_coverage_not_regressed(current, previous)
