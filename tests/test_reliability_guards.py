"""Reliability guards: empty≠match, decode stub skip, telemetry coverage rates."""
from __future__ import annotations

from benchmark.assembly_parity.run import compare_assembly
from benchmark.cfg_parity.run import compare_cfg
from benchmark.common.compare_guards import (
    cfg_invariant_violations,
    decode_surface_is_stub,
    empty_pair_result,
)
from benchmark.common.schema import BenchmarkSubject
from benchmark.decode_parity.run import compare_decode
from benchmark.function_discovery.run import compare_functions, normalize_function_address
from benchmark.pcode_parity.run import compare_pcode
from benchmark.telemetry.aggregate import aggregate_rows


def subject() -> BenchmarkSubject:
    return BenchmarkSubject(
        binary="bin",
        function="fn",
        addr="0x1000",
        arch="x86_64",
        compiler="gcc",
        opt="-O0",
    )


def test_empty_assembly_is_not_match() -> None:
    r = compare_assembly(subject(), "ghidra", "fission", [], [])
    assert r.status == "both_empty_invalid"


def test_empty_pcode_is_not_match() -> None:
    r = compare_pcode(subject(), "ghidra", "fission", [], [])
    assert r.status == "both_empty_invalid"


def test_empty_cfg_is_not_match() -> None:
    r = compare_cfg(
        subject(),
        "ghidra",
        "fission",
        {"blocks": [], "edges": []},
        {"blocks": [], "edges": []},
    )
    assert r.status == "both_empty_invalid"


def test_reference_empty_assembly() -> None:
    r = compare_assembly(
        subject(),
        "ghidra",
        "fission",
        [],
        [{"address": "0x1", "bytes": "90", "mnemonic": "nop"}],
    )
    assert r.status == "reference_empty"


def test_decode_stub_is_skipped_not_matched() -> None:
    stub = [
        {
            "address": "0x1",
            "bytes": "90",
            "length": 1,
            "mnemonic": "nop",
            "prefixes": [],
            "modrm": None,
            "sib": None,
            "displacement": None,
            "immediate": None,
        }
    ]
    assert decode_surface_is_stub(stub)
    r = compare_decode(subject(), "ghidra", "fission", stub, stub)
    assert r.status == "skipped"
    assert r.mismatch_kind == "decode_surface_stub"


def test_function_address_normalize_pads() -> None:
    assert normalize_function_address("0x0000000140001530") == normalize_function_address(
        "0x140001530"
    )
    r = compare_functions(
        subject(),
        "manifest",
        "fission",
        [{"address": "0x140001530", "name": "count_bits"}],
        [{"address": "0x0000000140001530", "name": "count_bits"}],
    )
    assert r.status == "match"


def test_cfg_invariant_edge_source() -> None:
    v = cfg_invariant_violations(
        {
            "blocks": [{"start": "0x10", "end": "0x20"}],
            "edges": [{"source": "0x99", "target": "0x10", "kind": "branch"}],
        }
    )
    assert any(x.get("kind") == "edge_source_not_in_blocks" for x in v)


def test_strict_pcode_abstracts_store_space_selector() -> None:
    from benchmark.common.providers import canonicalize_pcode

    ops = [
        {
            "seq": 0,
            "op": "STORE",
            "output": None,
            "inputs": [
                {"space": "const", "offset": "0x1b1", "size": 8},
                {"space": "register", "offset": "0x20", "size": 8},
            ],
        }
    ]
    loose = canonicalize_pcode(ops, mode="loose")
    strict = canonicalize_pcode(ops, mode="strict")
    literal = canonicalize_pcode(ops, mode="literal")
    assert loose[0]["inputs"][0]["offset"] == "*"
    assert strict[0]["inputs"][0]["offset"] == "space_selector"
    assert literal[0]["inputs"][0]["offset"] == "0x1b1"


def test_assembly_canonicalize_drops_display_and_null_control() -> None:
    from benchmark.common.providers import canonicalize_assembly_list

    inst = [
        {
            "address": "0x1",
            "bytes": "90",
            "mnemonic": "nop",
            "operands": "only_here",
            "fallthrough": "0x2",
            "branch_target": None,
        }
    ]
    for mode in ("loose", "strict"):
        out = canonicalize_assembly_list(inst, mode=mode)  # type: ignore[arg-type]
        assert "operands" not in out[0]
        assert "fallthrough" not in out[0]
        assert out[0]["bytes"] == "90"


def test_aggregate_reports_attempted_and_coverage() -> None:
    rows = [
        {"stage": "assembly_parity", "status": "match", "subject": {}, "reference": "g", "candidate": "f"},
        {"stage": "assembly_parity", "status": "match", "subject": {}, "reference": "g", "candidate": "f"},
        {"stage": "assembly_parity", "status": "fetch_error", "subject": {}, "reference": "g", "candidate": "f"},
        {"stage": "pcode_parity", "status": "mismatch", "subject": {}, "reference": "g", "candidate": "f", "mismatch_kind": "varnode"},
        {"stage": "decode_parity", "status": "skipped", "subject": {}, "reference": "g", "candidate": "f"},
    ]
    summary = aggregate_rows(rows)
    asm = summary["stages"]["assembly_parity"]
    assert asm["match_rate"] == 1.0  # among comparable only
    assert asm["match_rate_attempted"] == round(2 / 3, 4)
    assert asm["usable_coverage"] == round(2 / 3, 4)
    assert summary["reliability"]["fetch_error_rate"] is not None
    assert summary["schema"] == "parity-telemetry-v3"
    # Headline publishable is only primary stages *present in the run*.
    assert "decode_parity" not in summary["publishable"]["stages"]
    assert "ir_invariants" not in summary["publishable"]["stages"]
    assert "assembly_parity" in summary["publishable"]["stages"]
    assert "pcode_parity" in summary["publishable"]["stages"]
    assert set(summary["publishable"]["stages"]).issubset(
        {"assembly_parity", "pcode_parity", "cfg_parity", "function_discovery"}
    )
    assert "reliability_critique" in summary


def test_empty_pair_helper() -> None:
    r = empty_pair_result(subject(), "pcode_parity", "g", "f", [], [{"op": "COPY"}])
    assert r is not None and r.status == "reference_empty"


def test_pcode_dual_metrics_always_present() -> None:
    import os
    from benchmark.pcode_parity.run import compare_pcode

    ghidra = [
        {
            "seq": 0,
            "op": "INT_SUB",
            "output": {"space": "register", "offset": "0x20", "size": 8},
            "inputs": [
                {"space": "register", "offset": "0x20", "size": 8},
                {"space": "const", "offset": "0x8", "size": 8},
            ],
        },
        {
            "seq": 1,
            "op": "STORE",
            "output": None,
            "inputs": [
                {"space": "const", "offset": "0x1b1", "size": 8},
                {"space": "register", "offset": "0x20", "size": 8},
                {"space": "unique", "offset": "0x4f900", "size": 8},
            ],
        },
    ]
    fission = [
        {
            "seq": 0,
            "op": "IntSub",
            "output": {"space": "register", "offset": "0x20", "size": 8},
            "inputs": [
                {"space": "register", "offset": "0x20", "size": 8},
                {"space": "const", "offset": "0x8", "size": 8},
            ],
        },
        {
            "seq": 1,
            "op": "Store",
            "output": None,
            "inputs": [
                {"space": "const", "offset": "0x3", "size": 8},
                {"space": "register", "offset": "0x20", "size": 8},
                {"space": "unique", "offset": "0x4f900", "size": 8},
            ],
        },
    ]
    os.environ["PARITY_CANONICALIZE_MODE"] = "strict"
    r = compare_pcode(subject(), "ghidra", "fission", ghidra, fission)
    os.environ.pop("PARITY_CANONICALIZE_MODE", None)
    # Strict abstracts space selectors → full match; literal remains 0.
    assert r.status == "match"
    assert r.metrics.get("opcode_sequence_match") == 1
    assert r.metrics.get("loose_full_match") == 1
    assert r.metrics.get("strict_full_match") == 1
    assert r.metrics.get("literal_full_match") == 0
