"""Tests for runner.type_match: DWARF ground truth + decompiled-code matching.

The DWARF-extraction tests need a real corpus PE binary compiled with -g
(scripts/build_matrix.py always passes -g); they skip when the corpus hasn't
been built locally, matching the convention in test_differential_oracle.py.
The matching-logic tests are pure functions and always run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from runner.type_match import (
    VariableInfo,
    _calibrate_shift,
    _calibrate_shift_multi,
    _effective_offset,
    _uncommitted_size,
    compute_type_match,
    extract_ground_truth_types,
    normalize_type,
    parse_c_variables,
)


def _require_sample_pe() -> Path:
    pe_path = Path("corpus/dev/binaries/c/advanced_patterns_gcc_O0.exe")
    if not pe_path.is_file():
        pytest.skip("corpus PE binaries not built (run scripts/build_corpus.py)")
    return pe_path


# ── normalize_type ──────────────────────────────────────────────────────────


def test_normalize_type_maps_ghidra_undefined_spellings() -> None:
    assert "int" in normalize_type("undefined4")
    assert "long long" in normalize_type("undefined8")
    assert "char" in normalize_type("undefined1")


def test_normalize_type_maps_kuna_sleigh_spellings() -> None:
    assert "int" in normalize_type("int4")
    assert "long long" in normalize_type("uint8")


def test_normalize_type_strips_qualifiers_but_keeps_original_form() -> None:
    forms = normalize_type("unsigned int")
    assert "int" in forms
    assert "unsigned int" in forms


def test_normalize_type_handles_pointer_spacing() -> None:
    forms = normalize_type("int *")
    assert "int*" in forms


def test_normalize_type_empty_string_returns_empty_set() -> None:
    assert normalize_type("") == set()


# ── parse_c_variables (regex extraction) ────────────────────────────────────


def test_parse_c_variables_recovers_args_by_position() -> None:
    code = "int add(int a, int b)\n{\n    return a + b;\n}\n"
    variables = parse_c_variables(code, "add")
    args = [v for v in variables if v.kind == "arg"]
    assert [v.name for v in args] == ["a", "b"]
    assert [v.arg_index for v in args] == [0, 1]
    assert all(v.type == "int" for v in args)


def test_parse_c_variables_recovers_locals_from_body() -> None:
    # Real Fission output spaces the pointer star from the name (`int * local_10;`).
    code = (
        "ulonglong list_sum(int * param_1)\n"
        "{\n"
        "    int * local_10;\n"
        "    ulonglong local_4;\n"
        "    local_4 = 0;\n"
        "    return local_4;\n"
        "}\n"
    )
    variables = parse_c_variables(code, "list_sum")
    locals_ = {v.name: v.type for v in variables if v.kind == "stack"}
    assert locals_["local_10"] == "int *"
    assert locals_["local_4"] == "ulonglong"


def test_parse_c_variables_ignores_control_flow_keywords() -> None:
    code = "void f(void)\n{\n    if (1) {}\n    for (;;) {}\n}\n"
    variables = parse_c_variables(code, "f")
    assert all(v.name not in ("if", "for", "while") for v in variables)


def test_parse_c_variables_only_matches_the_definition_not_a_call_site() -> None:
    code = "void g(int x);\nvoid f(void)\n{\n    g(1);\n}\nvoid g(int x)\n{\n    (void)x;\n}\n"
    variables = parse_c_variables(code, "g")
    args = [v for v in variables if v.kind == "arg"]
    assert len(args) == 1
    assert args[0].name == "x"


# ── _effective_offset / _uncommitted_size ───────────────────────────────────


def test_effective_offset_recovers_from_ghidra_style_local_name() -> None:
    var = VariableInfo(name="local_10", type="int *")
    assert _effective_offset(var) == -0x10


def test_effective_offset_prefers_structured_stack_offset_when_present() -> None:
    var = VariableInfo(name="local_10", type="int", stack_offset=-4)
    assert _effective_offset(var) == -4


def test_effective_offset_none_for_non_offset_name() -> None:
    var = VariableInfo(name="cur", type="Node*")
    assert _effective_offset(var) is None


def test_uncommitted_size_matches_ghidra_undefined_width() -> None:
    var = VariableInfo(name="local_4", type="undefined4")
    assert _uncommitted_size(var) == 4


def test_uncommitted_size_none_for_committed_pointer() -> None:
    var = VariableInfo(name="p", type="int *")
    assert _uncommitted_size(var) is None


# ── offset calibration ──────────────────────────────────────────────────────


def test_calibrate_shift_finds_frame_bottom_offset() -> None:
    # decomp offsets are 8 larger than DWARF's (4 vs -4, -8 vs -16); the
    # shift added to a decomp offset to reach the ground truth is d + k = g,
    # i.e. k = g - d = -8.
    shift = _calibrate_shift(gt_offsets=[-4, -16], decomp_offsets=[4, -8])
    assert shift == -8


def test_calibrate_shift_none_when_nothing_aligns() -> None:
    assert _calibrate_shift(gt_offsets=[-4], decomp_offsets=[]) is None
    assert _calibrate_shift([], [-4]) is None


def test_calibrate_shift_multi_prefers_shift_that_aligns_more_pairs() -> None:
    pairs = [
        ([-4, -16], [4, -8]),
        ([-8], [0]),
    ]
    shift = _calibrate_shift_multi(pairs)
    assert shift == -8


# ── compute_type_match end-to-end (synthetic) ───────────────────────────────


def test_compute_type_match_perfect_score_on_exact_match() -> None:
    gt_vars = [
        {"name": "a", "type": ["int"], "rbp_offset": [], "is_arg": True, "arg_index": 0},
        {"name": "b", "type": ["int"], "rbp_offset": [], "is_arg": True, "arg_index": 1},
    ]
    code = "int add(int a, int b)\n{\n    return a + b;\n}\n"
    result = compute_type_match(gt_vars, code, "add")
    assert result["accuracy"] == 1.0
    assert result["tp"] == 2
    assert result["fp"] == 0
    assert result["fn"] == 0


def test_compute_type_match_wrong_type_counts_as_fp() -> None:
    gt_vars = [
        {"name": "head", "type": ["Node*"], "rbp_offset": [16], "is_arg": True, "arg_index": 0},
    ]
    # Decompiler recovers only a generic int* for a Node* argument.
    code = "ulonglong f(int *param_1)\n{\n    return 0;\n}\n"
    result = compute_type_match(gt_vars, code, "f")
    assert result["fp"] == 1
    assert result["tp"] == 0


def test_compute_type_match_missing_variable_counts_as_fn() -> None:
    gt_vars = [
        {"name": "total", "type": ["int"], "rbp_offset": [-4], "is_arg": False, "arg_index": None},
    ]
    code = "void f(void)\n{\n}\n"
    result = compute_type_match(gt_vars, code, "f")
    assert result["fn"] == 1
    assert result["accuracy"] == 0.0


def test_compute_type_match_uncommitted_type_matches_same_width_scalar() -> None:
    gt_vars = [
        {"name": "total", "type": ["int"], "rbp_offset": [-4], "is_arg": False, "arg_index": None},
    ]
    # undefined4 is width-only but 4 bytes wide, same as ground-truth int.
    code = "void f(void)\n{\n    undefined4 local_4;\n}\n"
    result = compute_type_match(gt_vars, code, "f")
    assert result["tp"] == 1


def test_compute_type_match_no_ground_truth_returns_zero() -> None:
    result = compute_type_match([], "int f(void) { return 0; }", "f")
    assert result["accuracy"] == 0.0
    assert "error" in result


def test_compute_type_match_no_decompiled_variables_scores_all_fn() -> None:
    gt_vars = [
        {"name": "a", "type": ["int"], "rbp_offset": [], "is_arg": True, "arg_index": 0},
    ]
    result = compute_type_match(gt_vars, "", "f")
    assert result["fn"] == 1
    assert result["accuracy"] == 0.0


# ── DWARF extraction against a real corpus binary ───────────────────────────


def test_extract_ground_truth_types_from_real_pe_binary() -> None:
    pe_path = _require_sample_pe()
    gt = extract_ground_truth_types(pe_path)
    assert "list_sum" in gt
    by_name = {v["name"]: v for v in gt["list_sum"]}
    assert "Node*" in by_name["head"]["type"]
    assert by_name["head"]["is_arg"] is True
    assert "int" in by_name["total"]["type"]


def test_type_match_distinguishes_real_fission_and_ghidra_output() -> None:
    """End-to-end sanity check against real decompiler output: Ghidra's
    struct-aware pseudocode should score meaningfully higher than Fission's
    current int*/undefined-typed output on the same DWARF ground truth."""
    pe_path = _require_sample_pe()
    gt = extract_ground_truth_types(pe_path)
    gt_vars = gt["list_sum"]

    fission_code = (
        "ulonglong list_sum(int * param_1)\n"
        "{\n"
        "    int * local_10;\n"
        "    ulonglong local_4;\n"
        "    local_4 = 0;\n"
        "    local_10 = param_1;\n"
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

    fission_result = compute_type_match(gt_vars, fission_code, "list_sum")
    ghidra_result = compute_type_match(gt_vars, ghidra_code, "list_sum")

    assert ghidra_result["accuracy"] > fission_result["accuracy"]
