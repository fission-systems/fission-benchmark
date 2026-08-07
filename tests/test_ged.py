"""Tests for runner.ged: source vs decompiled CFG structural distance.

Sanitization/degenerate-CFG checks are pure functions and always run. The
pyjoern-dependent tests (real CFG extraction + vj_ged) skip gracefully if
pyjoern/Joern isn't available or the corpus hasn't been built locally,
matching the convention in test_type_match.py/test_differential_oracle.py.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

from runner.ged import (
    compute_ged,
    escape_literal_control_bytes,
    extract_decompiled_cfgs,
    extract_source_cfgs,
    is_degenerate_cfg,
    sanitize_decompiled_c,
)


def _require_sample_source() -> Path:
    src_path = Path("corpus/dev/source/c/advanced_patterns.c")
    if not src_path.is_file():
        pytest.skip("corpus source not built (run scripts/build_corpus.py)")
    return src_path


def _require_pyjoern() -> None:
    try:
        from pyjoern import parse_source
    except ImportError:
        pytest.skip("pyjoern not installed")
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
        f.write("int f(void) { return 0; }\n")
        path = Path(f.name)
    try:
        result = parse_source(path)
        if not result:
            pytest.skip("pyjoern/Joern not functional in this environment")
    except Exception as e:
        pytest.skip(f"pyjoern/Joern not functional in this environment: {e}")
    finally:
        path.unlink(missing_ok=True)


# ── sanitize_decompiled_c ────────────────────────────────────────────────────


def test_sanitize_rewrites_aggregate_return_type() -> None:
    code = "undefined8 [16] weird_fn(int a)\n{\n    return 0;\n}\n"
    out = sanitize_decompiled_c(code)
    assert "[16]" not in out.split("\n")[0]
    assert "weird_fn(int a)" in out


def test_sanitize_does_not_touch_in_body_array_decl() -> None:
    code = "int f(void)\n{\n    char buf[16];\n    return 0;\n}\n"
    out = sanitize_decompiled_c(code)
    assert "char buf[16];" in out


def test_sanitize_strips_register_annotation() -> None:
    code = "int f(void)\n{\n    int x @ rax;\n    return x;\n}\n"
    out = sanitize_decompiled_c(code)
    assert "@" not in out


def test_sanitize_widens_int128() -> None:
    code = "__int128 f(void) { return 0; }\n"
    out = sanitize_decompiled_c(code)
    assert "__int128" not in out
    assert "long long" in out


def test_escape_literal_control_bytes_only_touches_literals() -> None:
    text = 'char *s = "\x1b[0m";\nint x = 1;\n'
    out = escape_literal_control_bytes(text)
    assert "\\x1b" in out
    assert "\x1b" not in out
    assert "int x = 1;" in out


def test_escape_literal_control_bytes_keeps_tab_and_newline() -> None:
    text = 'char *s = "a\tb";\n'
    out = escape_literal_control_bytes(text)
    assert "\t" in out


# ── is_degenerate_cfg ───────────────────────────────────────────────────────


class _FakeCfg:
    def __init__(self, nodes):
        self._nodes = nodes

    def number_of_nodes(self):
        return len(self._nodes)

    def nodes(self):
        return self._nodes


class Nop:
    pass


class _RealStmt:
    pass


class _FakeNode:
    def __init__(self, statements):
        self.statements = statements


def test_is_degenerate_cfg_empty() -> None:
    assert is_degenerate_cfg(_FakeCfg([])) is True


def test_is_degenerate_cfg_single_nop_only_node() -> None:
    node = _FakeNode([Nop(), Nop()])
    assert is_degenerate_cfg(_FakeCfg([node])) is True


def test_is_degenerate_cfg_single_real_node_not_degenerate() -> None:
    node = _FakeNode([_RealStmt()])
    assert is_degenerate_cfg(_FakeCfg([node])) is False


def test_is_degenerate_cfg_multi_node_not_degenerate() -> None:
    assert is_degenerate_cfg(_FakeCfg([_FakeNode([]), _FakeNode([])])) is False


# ── compute_ged ──────────────────────────────────────────────────────────────


def test_compute_ged_missing_cfg_returns_error() -> None:
    result = compute_ged(None, None)
    assert "error" in result
    assert "ged" not in result


def test_compute_ged_degenerate_source_returns_error() -> None:
    result = compute_ged(_FakeCfg([]), _FakeCfg([_FakeNode([_RealStmt()])]))
    assert "error" in result
    assert "ged" not in result


# ── real pyjoern integration ─────────────────────────────────────────────────


def test_extract_source_cfgs_from_real_corpus_file() -> None:
    _require_pyjoern()
    src_path = _require_sample_source()
    cfgs = extract_source_cfgs(str(src_path))
    assert "list_sum" in cfgs
    cfg = cfgs["list_sum"]
    assert cfg.number_of_nodes() > 0


def test_extract_source_cfgs_accepts_preprocessed_i_extension(tmp_path: Path) -> None:
    """Real corpus paths are `.i` (preprocessed translation units), not `.c`.
    Joern's CPG generator is dispatched by file extension and doesn't know
    `.i`, raising "No suitable CPG generator found" if parsed in place --
    caught in production on advanced_patterns_clang_O0.i. extract_source_cfgs
    must route through a `.c`-suffixed tempfile the same way
    extract_decompiled_cfgs already does."""
    _require_pyjoern()
    src_path = _require_sample_source()
    i_path = tmp_path / "advanced_patterns_clang_O0.i"
    i_path.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
    cfgs = extract_source_cfgs(str(i_path))
    assert "list_sum" in cfgs
    assert cfgs["list_sum"].number_of_nodes() > 0


def test_extract_decompiled_cfgs_batches_multiple_functions() -> None:
    _require_pyjoern()
    functions = {
        "add": "int add(int a, int b) { return a + b; }",
        "sub": "int sub(int a, int b) { return a - b; }",
    }
    cfgs = extract_decompiled_cfgs(functions)
    assert "add" in cfgs
    assert "sub" in cfgs


def test_extract_decompiled_cfgs_isolates_one_malformed_function(
    monkeypatch,
) -> None:
    calls: list[str] = []

    def fake_parse_source(path: Path):
        text = path.read_text(encoding="utf-8")
        calls.append(text)
        if "bad_marker" in text:
            raise RuntimeError("synthetic parser failure")
        return {"good": SimpleNamespace(name="good", cfg=object())}

    monkeypatch.setitem(
        sys.modules,
        "pyjoern",
        SimpleNamespace(parse_source=fake_parse_source),
    )

    cfgs = extract_decompiled_cfgs(
        {
            "good": "int good(void) { return 1; }",
            "bad": "int bad(void) { bad_marker; }",
        }
    )

    assert "good" in cfgs
    assert "bad" not in cfgs
    assert len(calls) == 3  # combined batch, then one isolated call per half


def test_extract_decompiled_cfgs_splits_when_batch_omits_every_function(
    monkeypatch,
) -> None:
    calls: list[str] = []

    def fake_parse_source(path: Path):
        text = path.read_text(encoding="utf-8")
        calls.append(text)
        if "int left" in text and "int right" in text:
            return {}
        name = "left" if "int left" in text else "right"
        return {name: SimpleNamespace(name=name, cfg=object())}

    monkeypatch.setitem(
        sys.modules,
        "pyjoern",
        SimpleNamespace(parse_source=fake_parse_source),
    )

    cfgs = extract_decompiled_cfgs(
        {
            "left": "int left(void) { return 1; }",
            "right": "int right(void) { return 2; }",
        }
    )

    assert set(cfgs) == {"left", "right"}
    assert len(calls) == 3


def test_ged_distinguishes_real_fission_and_ghidra_structure() -> None:
    """End-to-end sanity check against real decompiler output on list_sum:
    Ghidra's for-loop mirrors the source's control-flow shape (GED 0);
    Fission's while(1)+break idiom currently does not (GED > 0)."""
    _require_pyjoern()
    src_path = _require_sample_source()
    source_cfgs = extract_source_cfgs(str(src_path))
    source_cfg = source_cfgs["list_sum"]

    fission_code = (
        "ulonglong list_sum(int * param_1)\n"
        "{\n"
        "    int * local_10;\n"
        "    ulonglong local_4;\n"
        "    local_4 = 0;\n"
        "    local_10 = param_1;\n"
        "    while (1) {\n"
        "        if (!local_10) {\n"
        "            break;\n"
        "        }\n"
        "        local_4 += *local_10;\n"
        "        local_10 = (int *)(*(ulonglong *)(local_10 + 2));\n"
        "    }\n"
        "    return local_4;\n"
        "}\n"
    )
    ghidra_code = (
        "int list_sum(Node *head)\n"
        "{\n"
        "  Node *cur;\n"
        "  int total;\n"
        "  total = 0;\n"
        "  for (cur = head; cur != (Node *)0x0; cur = cur->next) {\n"
        "    total = total + cur->value;\n"
        "  }\n"
        "  return total;\n"
        "}\n"
    )

    # Two separate calls, mirroring production usage: extract_decompiled_cfgs
    # is invoked once per (binary, decompiler) batch. Two decompilers'
    # output for the SAME function shares that function's own C name
    # (`list_sum` in both snippets here), so batching them into a single
    # call would collide -- that never happens in real usage, where one
    # batch call covers many DIFFERENT function names from one decompiler.
    fission_cfgs = extract_decompiled_cfgs({"list_sum": fission_code})
    ghidra_cfgs = extract_decompiled_cfgs({"list_sum": ghidra_code})

    fission_result = compute_ged(source_cfg, fission_cfgs.get("list_sum"))
    ghidra_result = compute_ged(source_cfg, ghidra_cfgs.get("list_sum"))

    assert ghidra_result.get("ged") == 0.0
    assert fission_result.get("ged", 0.0) > ghidra_result.get("ged", 0.0)
