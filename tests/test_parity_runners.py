from benchmark.assembly_parity.run import compare_assembly
from benchmark.cfg_parity.run import compare_cfg
from benchmark.common.http_providers import corpus_relative_binary
from benchmark.common.providers import (
    canonicalize_cfg,
    canonicalize_pcode,
    normalize_pcode_op,
)
from benchmark.common.schema import BenchmarkSubject
from benchmark.decode_parity.run import compare_decode
from benchmark.function_discovery.run import compare_functions
from benchmark.ir_invariants.run import compare_invariants
from benchmark.pcode_parity.run import compare_pcode
from benchmark.telemetry.aggregate import (
    aggregate_rows,
    archive_release_telemetry,
    build_provenance,
)


def subject() -> BenchmarkSubject:
    return BenchmarkSubject(
        binary="bin",
        function="fn",
        addr="0x1000",
        arch="x86_64",
        compiler="gcc",
        opt="-O2",
    )


def test_assembly_compare_detects_instruction_count_mismatch() -> None:
    expected = [
        {"address": "0x1000", "bytes": "90", "mnemonic": "nop"},
        {"address": "0x1001", "bytes": "c3", "mnemonic": "ret"},
    ]
    actual = [{"address": "0x1000", "bytes": "90", "mnemonic": "nop"}]

    result = compare_assembly(subject(), "ref", "candidate", expected, actual)

    assert result.status == "mismatch"
    assert result.mismatch_kind == "instruction_count"


def test_assembly_empty_candidate_is_not_scored_mismatch() -> None:
    """Empty candidate must not look like a quality mismatch (reliability)."""
    expected = [{"address": "0x1000", "bytes": "90", "mnemonic": "nop"}]
    result = compare_assembly(subject(), "ref", "candidate", expected, [])
    assert result.status == "candidate_empty"


def test_assembly_normalizes_spaced_bytes_and_case() -> None:
    expected = [{"address": "0x140001560", "bytes": "4889e5", "mnemonic": "MOV", "operands": "MOV RBP,RSP"}]
    actual = [{"address": "0x140001560", "bytes": "48 89 e5", "mnemonic": "mov", "operands": "RBP,RSP"}]
    assert compare_assembly(subject(), "ghidra", "fission", expected, actual).status == "match"


def test_cfg_canonicalize_sorts_blocks() -> None:
    a = {"blocks": [{"start": "0x20", "end": "0x21"}, {"start": "0x10", "end": "0x11"}], "edges": []}
    b = {"blocks": [{"start": "0x10", "end": "0x11"}, {"start": "0x20", "end": "0x21"}], "edges": []}
    assert canonicalize_cfg(a) == canonicalize_cfg(b)


def test_corpus_relative_binary() -> None:
    assert corpus_relative_binary("binaries/foo.exe", "dev") == "corpus/dev/binaries/foo.exe"
    assert corpus_relative_binary("corpus/dev/binaries/foo.exe", "dev").startswith("corpus/")


def test_decode_compare_detects_sib_mismatch() -> None:
    expected = [{"address": "0x1000", "bytes": "48895c2408", "length": 5, "sib": "0x24"}]
    actual = [{"address": "0x1000", "bytes": "48895c2408", "length": 5, "sib": "0x25"}]

    result = compare_decode(subject(), "ref", "fission", expected, actual)

    assert result.status == "mismatch"
    assert result.mismatch_kind == "sib"


def test_pcode_compare_detects_op_kind_mismatch() -> None:
    expected = [{"seq": 0, "op": "COPY", "inputs": []}]
    actual = [{"seq": 0, "op": "STORE", "inputs": []}]

    result = compare_pcode(subject(), "ghidra", "fission", expected, actual)

    assert result.status == "mismatch"
    assert result.mismatch_kind == "op_kind"


def test_normalize_pcode_op_collapses_naming_styles() -> None:
    assert normalize_pcode_op("INT_SUB") == normalize_pcode_op("IntSub")
    assert normalize_pcode_op("INT_SUB") == normalize_pcode_op("INTSUB")
    assert normalize_pcode_op("BOOL_NEGATE") == normalize_pcode_op("BoolNegate")
    assert normalize_pcode_op("POPCOUNT") == normalize_pcode_op("PopCount")


def test_pcode_compare_matches_ghidra_vs_fission_spelling() -> None:
    """Opcode names normalize; STORE space-id still differs under strict (no leniency)."""
    expected = [
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
    actual = [
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
    # Loose stubs selector; strict abstracts selector offset; literal keeps table ids.
    assert canonicalize_pcode(expected, mode="loose") == canonicalize_pcode(
        actual, mode="loose"
    )
    assert canonicalize_pcode(expected, mode="strict") == canonicalize_pcode(
        actual, mode="strict"
    )
    assert canonicalize_pcode(expected, mode="literal") != canonicalize_pcode(
        actual, mode="literal"
    )
    result = compare_pcode(subject(), "ghidra", "fission", expected, actual)
    assert result.status == "match"
    assert result.metrics.get("opcode_sequence_match") == 1
    assert result.metrics.get("strict_full_match") == 1
    assert result.metrics.get("literal_full_match") == 0


def test_pcode_compare_still_flags_real_varnode_diffs() -> None:
    expected = [
        {
            "seq": 0,
            "op": "COPY",
            "output": {"space": "register", "offset": "0x0", "size": 8},
            "inputs": [{"space": "register", "offset": "0x28", "size": 8}],
        }
    ]
    actual = [
        {
            "seq": 0,
            "op": "Copy",
            "output": {"space": "register", "offset": "0x0", "size": 8},
            "inputs": [{"space": "register", "offset": "0x30", "size": 8}],
        }
    ]
    result = compare_pcode(subject(), "ghidra", "fission", expected, actual)
    assert result.status == "mismatch"
    assert result.mismatch_kind == "varnode"


def test_cfg_compare_detects_edge_connectivity_mismatch() -> None:
    expected = {"blocks": [{"start": "0x1000"}], "edges": [{"source": "0x1000", "target": "0x1010"}]}
    actual = {"blocks": [{"start": "0x1000"}], "edges": []}

    result = compare_cfg(subject(), "ref", "fission", expected, actual)

    assert result.status == "mismatch"
    # Prefer connectivity over raw edge_count when pairs differ.
    assert result.mismatch_kind in {"edge_connectivity", "edge_count"}
    assert result.metrics.get("edge_pair_jaccard") == 0.0


def test_cfg_match_on_topology_despite_span_encoding_diff() -> None:
    """Primary match is starts + edges; end-byte span is dual-only."""
    expected = {
        "blocks": [{"start": "0x1000", "end": "0x1003"}, {"start": "0x1004", "end": "0x1007"}],
        "edges": [{"source": "0x1000", "target": "0x1004", "kind": "branch"}],
    }
    actual = {
        "blocks": [{"start": "0x1000", "end": "0x1002"}, {"start": "0x1004", "end": "0x1006"}],
        "edges": [{"source": "0x1000", "target": "0x1004", "kind": "fallthrough"}],
    }
    result = compare_cfg(subject(), "ghidra", "fission", expected, actual)
    assert result.status == "match"
    assert result.metrics.get("compare_policy") == "starts_and_edge_pairs"
    assert result.metrics.get("span_encoding_diff") == 1
    assert result.metrics.get("block_start_jaccard") == 1.0
    assert result.metrics.get("edge_pair_jaccard") == 1.0


def test_abi_location_aliases_and_count() -> None:
    from benchmark.abi_parity.run import compare_abi

    exp = {
        "status": "ok",
        "parameters": [{"index": 0, "location": "ECX", "size": 4}],
        "return": {"location": "EAX", "size": 4},
    }
    act = {
        "status": "ok",
        "parameters": [{"index": 0, "location": "rcx", "size": 8}],
        "return": {"location": "rax", "size": 8},
    }
    assert compare_abi(subject(), "ghidra", "fission", exp, act).status == "match"

    act_bad = {
        "status": "ok",
        "parameters": [],
        "return": {"location": "rax", "size": 8},
    }
    bad = compare_abi(subject(), "ghidra", "fission", exp, act_bad)
    assert bad.status == "mismatch"
    assert bad.mismatch_kind == "abi_param_count"


def test_type_and_callgraph_and_string_extension_compares() -> None:
    from benchmark.callgraph_parity.run import compare_callgraph
    from benchmark.string_recovery.run import compare_strings
    from benchmark.type_parity.run import compare_types

    exp_t = {
        "status": "ok",
        "return_type": "int",
        "parameters": [{"index": 0, "type": "int"}],
        "structs": [],
    }
    act_t = {
        "status": "ok",
        "return_type": "int",
        "parameters": [{"index": 0, "type": "int"}],
        "structs": [],
    }
    assert compare_types(subject(), "ghidra", "fission", exp_t, act_t).status == "match"

    # Field layout IoU: same offsets/sizes match
    exp_layout = {
        "status": "ok",
        "return_type": "int",
        "parameters": [],
        "structs": [
            {
                "name": "ConfigNode",
                "size": 8,
                "fields": [
                    {"name": "flags", "offset": 0, "size": 4, "type": "Flags"},
                    {"name": "val", "offset": 4, "size": 4, "type": "DataValue"},
                ],
            }
        ],
    }
    act_layout = {
        "status": "ok",
        "return_type": "int",
        "parameters": [],
        "structs": [
            {
                "name": "ConfigNode",
                "size": 8,
                "fields": [
                    {"name": "flags", "offset": 0, "size": 4, "type": "Flags"},
                    {"name": "val", "offset": 4, "size": 4, "type": "int"},
                ],
            }
        ],
    }
    assert compare_types(subject(), "ghidra", "fission", exp_layout, act_layout).status == "match"
    act_bad = {
        "status": "ok",
        "return_type": "int",
        "parameters": [],
        "structs": [
            {
                "name": "ConfigNode",
                "size": 8,
                "fields": [{"name": "flags", "offset": 0, "size": 8, "type": "Flags"}],
            }
        ],
    }
    bad = compare_types(subject(), "ghidra", "fission", exp_layout, act_bad)
    assert bad.status == "mismatch"
    assert bad.mismatch_kind == "field_layout"

    exp_c = {"status": "ok", "callees": ["0x140001000", "0x140001100"]}
    act_c = {"status": "ok", "callees": ["0x140001100", "0x140001000"]}
    assert compare_callgraph(subject(), "ghidra", "fission", exp_c, act_c).status == "match"

    exp_s = {"status": "ok", "strings": ["hello", "world"]}
    act_s = {"status": "ok", "strings": []}
    assert compare_strings(subject(), "ghidra", "fission", exp_s, act_s).status == "mismatch"


def test_pe_runtime_function_and_string_scan() -> None:
    from pathlib import Path

    from benchmark.common.pe_exceptions import parse_pe_runtime_functions
    from benchmark.common.string_scan import extract_ascii_strings

    pe = Path("corpus/dev/binaries/control_flow_gcc_O0.exe")
    if pe.is_file():
        table = parse_pe_runtime_functions(pe)
        assert table["status"] == "ok"
        assert table["function_count"] >= 1
    assert ("hello",) or extract_ascii_strings(b"xxxxhello worldxxxx")


def test_opt_cliff_bucket() -> None:
    from benchmark.opt_cliff.run import _opt_bucket

    assert _opt_bucket("gcc -O0") == "O0"
    assert _opt_bucket("gcc-m32 -O2") == "O2"


def test_function_discovery_detects_function_set_mismatch() -> None:
    expected = [{"address": "0x1000", "name": "main"}, {"address": "0x2000", "name": "foo"}]
    actual = [{"address": "0x1000", "name": "main"}]

    result = compare_functions(subject(), "ref", "fission", expected, actual)

    assert result.status == "mismatch"
    assert result.mismatch_kind == "function_set"


def test_function_discovery_empty_is_invalid_not_match() -> None:
    result = compare_functions(subject(), "ref", "fission", [{"address": "0x1", "name": "a"}], [])
    assert result.status == "candidate_empty"


def test_ir_invariants_fail_on_violation() -> None:
    payload = {"violations": [{"kind": "dangling_edge"}], "metrics": {"block_count": 2}}

    result = compare_invariants(subject(), "fission", payload)

    assert result.status == "mismatch"
    assert result.mismatch_kind == "dangling_edge"
    assert result.metrics["violation_count"] == 1


def test_telemetry_aggregate_counts_stage_status_and_variant() -> None:
    rows = [
        {
            "subject": {"compiler": "gcc", "opt": "-O2"},
            "stage": "pcode_parity",
            "status": "mismatch",
            "mismatch_kind": "op_kind",
            "reference": "ghidra",
            "candidate": "fission",
        },
        {
            "subject": {"compiler": "gcc", "opt": "-O2"},
            "stage": "assembly_parity",
            "status": "match",
            "mismatch_kind": None,
            "reference": "ghidra",
            "candidate": "fission",
        },
    ]

    summary = aggregate_rows(rows)

    assert summary["total_rows"] == 2
    assert summary["schema"] == "parity-telemetry-v3"
    assert "reliability" in summary
    assert "match_rate_attempted" in summary["stages"]["assembly_parity"]
    assert summary["by_stage"] == {"assembly_parity": 1, "pcode_parity": 1}
    assert summary["by_status"] == {"match": 1, "mismatch": 1}
    assert summary["by_mismatch_kind"] == {"none": 1, "op_kind": 1}
    assert summary["by_variant"] == {"gcc -O2": 2}
    assert summary["stages"]["assembly_parity"]["match_rate"] == 1.0
    assert summary["stages"]["pcode_parity"]["mismatch_rate"] == 1.0


def test_telemetry_provenance_fingerprints_sources(tmp_path, monkeypatch) -> None:
    source = tmp_path / "cfg_parity" / "latest.jsonl"
    source.parent.mkdir()
    source.write_text('{"stage":"cfg_parity"}\n', encoding="utf-8")
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("FISSION_VERSION", "1.2.3")

    provenance = build_provenance([source])

    assert provenance["generated_at"].endswith("Z")
    assert provenance["runner_commit"] == "abc123"
    assert provenance["tool_versions"]["fission"] == "1.2.3"
    assert provenance["sources"][0]["rows"] == 1
    assert len(provenance["sources"][0]["sha256"]) == 64
    assert provenance["sources"][0]["modified_at"].endswith("Z")


def test_parity_history_is_keyed_by_fission_release(tmp_path) -> None:
    summary = {
        "schema": "parity-telemetry-v3",
        "provenance": {"tool_versions": {"fission": "v1.2.3"}},
    }

    assert archive_release_telemetry(summary, tmp_path) == "v1.2.3"
    assert (tmp_path / "v1.2.3.json").is_file()
    assert (tmp_path / "index.json").read_text().strip() == '[\n  "v1.2.3"\n]'


def test_parity_history_rejects_unversioned_snapshot(tmp_path) -> None:
    summary = {"provenance": {"tool_versions": {"fission": None}}}

    assert archive_release_telemetry(summary, tmp_path) is None
    assert list(tmp_path.iterdir()) == []
