import importlib.util
from pathlib import Path


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mod():
    path = Path(__file__).resolve().parents[1] / "scripts" / "compare_runs.py"
    return _load("compare_runs", path)


def _row(
    decompiler: str = "fission",
    function_name: str = "f",
    compiler_variant: str = "gcc -O0",
    fail_category: str | None = None,
    type_match_score: float | None = None,
    semantic_score: float | None = None,
) -> dict:
    return {
        "decompiler": decompiler,
        "function_name": function_name,
        "compiler_variant": compiler_variant,
        "fail_category": fail_category,
        "type_match_score": type_match_score,
        "semantic_score": semantic_score,
    }


def test_row_key_and_index_filters_by_decompiler() -> None:
    mod = _mod()
    envelope = {
        "rows": [
            _row(decompiler="fission", function_name="a"),
            _row(decompiler="ghidra", function_name="a"),
        ]
    }
    idx = mod._index_rows(envelope, "fission")
    assert list(idx.keys()) == [("fission", "a", "gcc -O0")]

    idx_all = mod._index_rows(envelope, None)
    assert len(idx_all) == 2


def test_mean_metric_ignores_none() -> None:
    mod = _mod()
    rows = [
        _row(type_match_score=0.5),
        _row(type_match_score=None),
        _row(type_match_score=1.0),
    ]
    mean_val, n = mod._mean_metric(rows, "type_match_score")
    assert n == 2
    assert mean_val == 0.75


def test_fail_category_counts_treats_missing_as_ok() -> None:
    mod = _mod()
    rows = [_row(fail_category=None), _row(fail_category="compile_error")]
    counts = mod._fail_category_counts(rows)
    assert counts == {"ok": 1, "compile_error": 1}


def test_print_transitions_flags_regressed_and_fixed(capsys) -> None:
    mod = _mod()
    before_idx = {
        ("fission", "a", "gcc -O0"): _row(function_name="a", fail_category=None),
        ("fission", "b", "gcc -O0"): _row(function_name="b", fail_category="compile_error"),
    }
    after_idx = {
        ("fission", "a", "gcc -O0"): _row(function_name="a", fail_category="assertion_fail"),
        ("fission", "b", "gcc -O0"): _row(function_name="b", fail_category=None),
    }
    mod.print_transitions(before_idx, after_idx, limit=10)
    out = capsys.readouterr().out
    assert "REGRESSED" in out
    assert "FIXED" in out
    assert "a" in out and "b" in out


def test_main_runs_end_to_end(tmp_path: Path, capsys) -> None:
    mod = _mod()
    before = {
        "run": {"run_id": "before-1"},
        "rows": [_row(fail_category=None, semantic_score=1.0)],
    }
    after = {
        "run": {"run_id": "after-1"},
        "rows": [_row(fail_category="compile_error", semantic_score=0.0)],
    }
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    before_path.write_text(__import__("json").dumps(before))
    after_path.write_text(__import__("json").dumps(after))

    rc = mod.main(["--before", str(before_path), "--after", str(after_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "before-1" in out
    assert "after-1" in out
    assert "REGRESSED" in out
