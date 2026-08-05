from __future__ import annotations

from pathlib import Path

from runner import recompilation


def test_ordered_jaccard_preserves_instruction_order() -> None:
    score, changed = recompilation._ordered_jaccard(
        ["push rbp", "mov rbp, rsp", "ret"],
        ["push rbp", "xor eax, eax", "ret"],
    )
    assert score == 0.5
    assert changed == 2


def test_recompilation_abstains_without_matching_toolchain(
    monkeypatch, tmp_path: Path
) -> None:
    binary = tmp_path / "sample.exe"
    binary.write_bytes(b"MZ")
    monkeypatch.setattr(
        recompilation,
        "detect",
        lambda _path: recompilation.BinInfo("pe", "x86-64", 64),
    )
    monkeypatch.setattr(recompilation.shutil, "which", lambda _name: None)
    score, evidence = recompilation.measure_recompilation(
        "int add(int a, int b) { return a + b; }",
        function_name="add",
        binary_path=binary,
        function_address="0x140001000",
        compiler_variant="gcc -O0",
    )
    assert score is None
    assert evidence["category"] == "toolchain_missing"
    assert evidence["ranking"] is False


def test_aggregate_recompilation_uses_shared_subject_denominator() -> None:
    rows = [
        {
            "decompiler": "fission",
            "corpus": "dev",
            "function_name": "clamp",
            "compiler_variant": "gcc -O0",
            "recompilation_score": 1.0,
            "recompilation": {"compilable": True},
        },
        {
            "decompiler": "ghidra",
            "corpus": "dev",
            "function_name": "clamp",
            "compiler_variant": "gcc -O0",
            "recompilation_score": 0.4,
            "recompilation": {"compilable": True},
        },
        {
            "decompiler": "fission",
            "corpus": "dev",
            "function_name": "sum_array",
            "compiler_variant": "gcc -O0",
            "recompilation_score": None,
            "recompilation": {"category": "toolchain_missing"},
        },
        {
            "decompiler": "ghidra",
            "corpus": "dev",
            "function_name": "sum_array",
            "compiler_variant": "gcc -O0",
            "recompilation_score": 1.0,
            "recompilation": {"compilable": True},
        },
    ]
    summary = recompilation.aggregate_recompilation(rows)
    fission = summary["by_decompiler"]["fission"]
    assert fission["observed_rows"] == 1
    assert fission["shared_rows"] == 2
    assert fission["perfect_rows"] == 1
    assert fission["perfect_rate"] == 0.5
