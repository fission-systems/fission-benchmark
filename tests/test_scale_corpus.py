"""Contracts for the namespaced DecBench-scale corpus path."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from runner.corpus import Corpus
from runner.ged import is_degenerate_cfg, load_published_source_cfgs
from runner.runner import build_expected_cells, filter_functions

ROOT = Path(__file__).resolve().parents[1]


def test_external_subject_identity_is_distinct_from_binary_symbol(tmp_path: Path) -> None:
    manifest = tmp_path / "external.json"
    manifest.write_text(
        json.dumps(
            {
                "functions": [
                    {
                        "name": "main",
                        "subject_id": "decbench::grep::grep::main",
                        "project": "grep",
                        "source": "sources/grep",
                        "semantic": {"mode": "none"},
                        "compiler_variants": [
                            {
                                "compiler": "gcc",
                                "opt": "-O0",
                                "binary": "binaries/O0/grep/grep",
                                "addr": "0x401000",
                                "format": "elf",
                                "isa": "x86_64",
                                "source_cfg": "source_cfgs/O0/grep/grep.json",
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    corpus = Corpus.load(manifest)
    function = corpus.functions[0]
    assert function.name == "main"
    assert function.subject_name == "decbench::grep::grep::main"
    assert function.compiler_variants[0].source_cfg.endswith("grep.json")
    cells = build_expected_cells([function], ["fission", "ghidra"], None)
    assert {cell["function_name"] for cell in cells} == {
        "decbench::grep::grep::main"
    }


def test_bare_duplicate_symbol_filter_requires_subject_id(tmp_path: Path) -> None:
    payload = {
        "functions": [
            {
                "name": "main",
                "subject_id": f"decbench::{project}::app::main",
                "project": project,
                "source": f"sources/{project}",
                "compiler_variants": [
                    {
                        "compiler": "gcc",
                        "opt": "-O0",
                        "binary": f"binaries/O0/{project}/app",
                        "addr": "0x1000",
                    }
                ],
            }
            for project in ("grep", "gzip")
        ]
    }
    manifest = tmp_path / "duplicates.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    functions = Corpus.load(manifest).functions
    with pytest.raises(ValueError, match="ambiguous external symbol"):
        filter_functions(functions, "main")
    selected = filter_functions(functions, "decbench::grep::app::main")
    assert [function.project for function in selected] == ["grep"]


def test_published_source_cfg_rebuilds_entry_exit_and_real_block(
    tmp_path: Path,
) -> None:
    path = tmp_path / "cfg.json"
    path.write_text(
        json.dumps(
            {
                "functions": {
                    "straight": {
                        "nodes": [0],
                        "edges": [],
                        "entry": [0],
                        "exit": [0],
                        "degenerate": False,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    cfg = load_published_source_cfgs(str(path))["straight"]
    node = next(iter(cfg.nodes()))
    assert node.is_entrypoint is True
    assert node.is_exitpoint is True
    assert is_degenerate_cfg(cfg) is False


def test_scale_lock_is_pinned_and_malware_is_opt_in() -> None:
    lock = json.loads(
        (ROOT / "corpus" / "scale" / "dataset-lock.json").read_text()
    )
    assert len(lock["revision"]) == 40
    assert lock["configs"]["unoptimized"]["functions"] >= 30_000
    assert lock["configs"]["unoptimized"]["safe_resolved_functions"] >= 30_000
    assert (
        lock["configs"]["unoptimized"]["safe_source_cfg_functions"]
        < lock["configs"]["unoptimized"]["safe_resolved_functions"]
    )

    script = ROOT / "scripts" / "materialize_scale_corpus.py"
    spec = importlib.util.spec_from_file_location("materialize_scale_corpus", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert "mirai" in module.MALWARE_PROJECTS
    assert module._variant_opt("O0") == "-O0"
    with pytest.raises(ValueError, match="unsafe project"):
        module._safe_component("../escape", "project")
