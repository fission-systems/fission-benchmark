"""Matrix profile loading and corpus filtering."""
from __future__ import annotations

from runner.corpus import CompilerVariant, Corpus, FunctionEntry
import pytest

from runner.matrix_profile import (
    apply_profile_to_functions,
    get_profile,
    load_profiles,
    validate_release_contract,
)


def test_profiles_yaml_loads_smoke_and_core() -> None:
    data = load_profiles()
    assert "smoke" in data["profiles"]
    assert "core_c_pe" in data["profiles"]
    smoke = get_profile("smoke")
    assert smoke is not None
    assert "c" in smoke["languages"]
    assert smoke["max_functions"] == 10

    scale_smoke = get_profile("decbench_scale_smoke")
    assert scale_smoke is not None
    assert scale_smoke["sampling"] == "project_round_robin"


def test_project_round_robin_sampling_balances_uneven_projects() -> None:
    functions = []
    for project, count in (("alpha", 5), ("beta", 2), ("gamma", 1)):
        for index in range(count):
            functions.append(
                FunctionEntry(
                    name=f"{project}_{index}",
                    project=project,
                    source=f"source/{project}.c",
                    language="c",
                    compiler_variants=[
                        CompilerVariant(
                            "gcc",
                            "-O0",
                            f"binaries/{project}",
                            isa="x86_64",
                            format="elf",
                        )
                    ],
                )
            )

    out = apply_profile_to_functions(
        functions,
        {
            "languages": ["c"],
            "sampling": "project_round_robin",
            "max_functions": 6,
        },
    )

    assert [(fn.project, fn.name) for fn in out] == [
        ("alpha", "alpha_0"),
        ("beta", "beta_0"),
        ("gamma", "gamma_0"),
        ("alpha", "alpha_1"),
        ("beta", "beta_1"),
        ("alpha", "alpha_2"),
    ]


def test_unknown_sampling_strategy_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unknown matrix profile sampling strategy"):
        apply_profile_to_functions([], {"sampling": "random"})


def test_apply_profile_filters_opts_and_allowlist() -> None:
    fns = [
        FunctionEntry(
            name="count_bits",
            source="source/c/control_flow.c",
            language="c",
            compiler_variants=[
                CompilerVariant("gcc", "-O0", "binaries/c/a.exe", isa="x86_64", format="pe"),
                CompilerVariant("gcc", "-O2", "binaries/c/b.exe", isa="x86_64", format="pe"),
                CompilerVariant("gcc-m32", "-O0", "binaries/c/c.exe", isa="x86_32", format="pe"),
            ],
        ),
        FunctionEntry(
            name="not_in_smoke",
            source="source/c/other.c",
            language="c",
            compiler_variants=[
                CompilerVariant("gcc", "-O0", "binaries/c/d.exe", isa="x86_64", format="pe"),
            ],
        ),
    ]
    prof = get_profile("smoke")
    assert prof is not None
    out = apply_profile_to_functions(fns, prof)
    names = {f.name for f in out}
    assert "count_bits" in names
    assert "not_in_smoke" not in names
    cb = next(f for f in out if f.name == "count_bits")
    assert all(v.opt == "-O0" for v in cb.compiler_variants)
    assert all(v.compiler == "gcc" for v in cb.compiler_variants)
    assert len(cb.compiler_variants) == 1  # max_variants_per_function=1


def test_corpus_apply_profile_smoke() -> None:
    c = Corpus.load_all("dev")
    if not c.functions:
        return  # empty in some CI slices
    filtered = c.apply_profile("smoke")
    assert len(filtered.functions) <= 10
    for fn in filtered.functions:
        assert fn.language == "c"
        for v in fn.compiler_variants:
            assert v.opt == "-O0"
            assert v.compiler == "gcc"


def test_core_release_contract_is_exactly_36_by_6() -> None:
    profile = get_profile("core_c_pe")
    assert profile is not None
    corpus = Corpus.load_all("dev")
    functions = apply_profile_to_functions(corpus.functions, profile)
    contract = validate_release_contract(
        "core_c_pe", profile, functions, ["fission", "ghidra"]
    )
    assert contract is not None
    assert contract["id"] == "release-baseline-v1"
    assert contract["function_count"] == 36
    assert contract["compiler_variant_count"] == 6
    assert contract["subject_count"] == 216
    assert contract["row_count"] == 432


def test_release_contract_fails_closed_on_cohort_drift() -> None:
    profile = get_profile("core_c_pe")
    assert profile is not None
    corpus = Corpus.load_all("dev")
    functions = apply_profile_to_functions(corpus.functions, profile)

    with pytest.raises(ValueError, match="function drift"):
        validate_release_contract(
            "core_c_pe", profile, functions[:-1], ["fission", "ghidra"]
        )
    with pytest.raises(ValueError, match="decompiler drift"):
        validate_release_contract(
            "core_c_pe", profile, functions, ["ghidra", "fission"]
        )
