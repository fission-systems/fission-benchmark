from benchmark.common.schema import BenchmarkSubject
from benchmark.metadata_parity.run import compare_metadata


SUBJECT = BenchmarkSubject(
    binary="binaries/sample.exe",
    function="(metadata)",
    addr="0x0",
    arch="x86_64",
    compiler="gcc",
    opt="O0",
)


def payload(*, functions=(0x1000,), block_size=0x100):
    return {
        "schema": "test-v1",
        "binary": {
            "bitness": 64,
            "image_base": 0x1000,
            "language_id": "x86:LE:64:default",
        },
        "memory_blocks": [
            {
                "start": 0x1000,
                "size": block_size,
                "permissions": {"read": True, "write": False, "execute": True},
            }
        ],
        "functions": [{"entry": entry} for entry in functions],
        "symbols": [{"address": 0x1000}],
        "relocations": [{"address": 0x1020, "relocation_type": 10}],
    }


def test_metadata_exact_match():
    row = compare_metadata(SUBJECT, "ghidra", "fission", payload(), payload())
    assert row.status == "match"
    assert row.metrics["core_metadata_match"] == 1
    assert row.metrics["function_entry_jaccard"] == 1.0


def test_metadata_reports_first_structural_mismatch():
    row = compare_metadata(
        SUBJECT,
        "ghidra",
        "fission",
        payload(functions=(0x1000, 0x1010)),
        payload(functions=(0x1000,)),
    )
    assert row.status == "mismatch"
    assert row.mismatch_kind == "function_entries"
    assert row.metrics["function_entry_jaccard"] == 0.5


def test_metadata_missing_schema_is_not_a_match():
    row = compare_metadata(SUBJECT, "ghidra", "fission", payload(), {})
    assert row.status == "candidate_empty"


def test_metadata_ignores_pe_absolute_relocation_padding():
    expected = payload()
    expected["relocations"].append(
        {"address": 0x2000, "relocation_type": 0}
    )

    row = compare_metadata(SUBJECT, "ghidra", "fission", expected, payload())
    assert row.status == "match"
    assert row.metrics["ref_relocations"] == 1


def test_symbol_coverage_does_not_hide_core_metadata_parity():
    expected = payload()
    expected["symbols"].append({"address": 0x1030})

    row = compare_metadata(SUBJECT, "ghidra", "fission", expected, payload())
    assert row.status == "mismatch"
    assert row.mismatch_kind == "symbol_addresses"
    assert row.metrics["core_metadata_match"] == 1
    assert row.metrics["symbol_reference_recall"] == 0.5
    assert row.metrics["symbol_candidate_precision"] == 1.0


def test_generated_ghidra_labels_are_not_loader_symbol_mismatches():
    expected = payload()
    expected["symbols"] = [
        {"address": 0x1000, "source": "imported"},
        {"address": 0x1030, "source": "default"},
        {"address": 0x1040, "source": "analysis"},
    ]
    actual = payload()
    actual["symbols"] = [
        {
            "address": 0x1000,
            "provenance": {"source": "symbol_table"},
        }
    ]

    row = compare_metadata(SUBJECT, "ghidra", "fission", expected, actual)

    assert row.status == "match"
    assert row.metrics["symbol_reference_recall"] == 1.0
    assert row.metrics["ref_generated_symbols"] == 2
    assert row.metrics["raw_symbol_address_jaccard"] == 0.3333


def test_provenanced_loader_symbol_gap_remains_a_mismatch():
    expected = payload()
    expected["symbols"] = [
        {"address": 0x1000, "source": "imported"},
        {"address": 0x1030, "source": "imported"},
    ]
    actual = payload()
    actual["symbols"] = [
        {
            "address": 0x1000,
            "provenance": {"source": "symbol_table"},
        }
    ]

    row = compare_metadata(SUBJECT, "ghidra", "fission", expected, actual)

    assert row.status == "mismatch"
    assert row.mismatch_kind == "symbol_addresses"
    assert row.metrics["symbol_reference_recall"] == 0.5
