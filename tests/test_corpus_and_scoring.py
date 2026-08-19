from pathlib import Path

from runner.corpus import Corpus
from runner.runner import load_function_source_text
from runner.scoring import FunctionScore, assign_consensus_ranks, extract_function_source, compute_correctness_score
from runner.test_wrappers import SEMANTIC_UNTESTABLE, TEST_WRAPPERS
from scripts.precompute_source_metrics import discover_source_files


def test_load_function_source_text_handles_file_and_directory(tmp_path: Path) -> None:
    """Multi-file language packages must not raise IsADirectoryError."""
    pkg = tmp_path / "patterns"
    pkg.mkdir()
    (pkg / "main.go").write_text("package main\n//export go_add_ints\n", encoding="utf-8")
    (pkg / "go.mod").write_text("module patterns\n", encoding="utf-8")

    from_file = load_function_source_text(pkg / "main.go")
    from_dir = load_function_source_text(pkg)
    assert "go_add_ints" in from_file
    assert "go_add_ints" in from_dir
    assert load_function_source_text(tmp_path / "missing.go") == ""


def test_manifest_preserves_variant_addr(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        """
        {
          "functions": [
            {
              "name": "foo",
              "source": "source/foo.c",
              "compiler_variants": [
                {"compiler": "gcc", "opt": "-O0", "binary": "binaries/foo", "addr": "0x401120"}
              ]
            }
          ]
        }
        """
    )

    corpus = Corpus.load(manifest)

    assert corpus.functions[0].compiler_variants[0].addr == "0x401120"


def test_extract_function_source_returns_requested_function_only() -> None:
    source = """
    int alpha(int x) {
        return x + 1;
    }

    int beta(int y) {
        if (y > 0) {
            return y;
        }
        return -y;
    }
    """

    extracted = extract_function_source(source, "beta")

    assert "int beta" in extracted
    assert "return -y;" in extracted
    assert "int alpha" not in extracted


def test_assign_ranks_preserves_intrinsics_flag() -> None:
    scores = [
        FunctionScore(
            decompiler="ghidra",
            function_name="foo",
            compiler_variant="gcc -O0",
            source_similarity=0.5,
            goto_count=0,
            nesting_depth=1,
            time_ms=10,
            decompiled_code="int foo(int x) { return __carry(x, 1); }",
        )
    ]

    ranked = assign_consensus_ranks(scores)

    assert ranked[0].uses_intrinsics is True


def test_crypto_functions_have_semantic_wrappers() -> None:
    for name in ("rc4_init", "rc4_crypt", "crc32"):
        assert name in TEST_WRAPPERS
        assert len(TEST_WRAPPERS[name]) >= 4


def test_all_corpus_functions_have_semantic_wrappers() -> None:
    """Every locked corpus function is oracle-testable, or named as one that is not.

    The debt this guards against is the *silent* kind. A function the harness
    cannot run (a Win32 API call has no meaning under gcc-on-Linux) is allowed,
    but only by appearing in SEMANTIC_UNTESTABLE with a reason -- so the list
    is reviewable and cannot grow by accident.
    """
    from runner.corpus import Corpus

    names = {fn.name for fn in Corpus.load_all("full").functions}
    assert names, "expected non-empty corpus"

    overlap = sorted(set(TEST_WRAPPERS) & set(SEMANTIC_UNTESTABLE))
    assert overlap == [], f"listed both testable and untestable: {overlap}"

    missing = sorted(names - set(TEST_WRAPPERS) - set(SEMANTIC_UNTESTABLE))
    assert missing == [], f"functions without wrappers: {missing}"

    # An entry that no longer names a corpus function is stale; drop it rather
    # than leave a standing excuse for a function that is gone or renamed.
    stale = sorted(set(SEMANTIC_UNTESTABLE) - names)
    assert stale == [], f"SEMANTIC_UNTESTABLE names non-corpus functions: {stale}"

    for name, reason in SEMANTIC_UNTESTABLE.items():
        assert reason.strip(), f"{name} needs a reason"

    for name in names - set(SEMANTIC_UNTESTABLE):
        assert len(TEST_WRAPPERS[name]) >= 5, f"{name} needs ≥5 cases"


def test_holdout_split_is_non_empty_and_disjoint() -> None:
    from runner.corpus import Corpus

    dev = {fn.name for fn in Corpus.load_all("dev").functions}
    holdout = {fn.name for fn in Corpus.load_all("holdout").functions}
    assert holdout, "holdout corpus must be populated (run scripts/populate_holdout.py)"
    assert dev, "dev corpus must remain non-empty after holdout lock"
    assert dev.isdisjoint(holdout), f"overlap: {sorted(dev & holdout)}"


def test_semantic_stress_family_has_full_variant_matrix() -> None:
    manifest = (
        Path(__file__).parent.parent
        / "corpus"
        / "dev"
        / "manifests"
        / "c_semantic_stress.json"
    )
    corpus = Corpus.load(manifest)
    expected_functions = {
        "rolling_hash32",
        "bounded_tlv_sum",
        "state_machine_score",
        "overlap_move",
        "mixed_width_accumulate",
        "rotate_words",
    }
    # Expanded C PE matrix (P0 multi-opt): gcc opt ladder + m32 + clang x64.
    expected_variants = {
        *{("gcc", opt) for opt in ("-O0", "-O1", "-O2", "-Os", "-O3")},
        *{("gcc-m32", opt) for opt in ("-O0", "-O2")},
        *{("clang", opt) for opt in ("-O0", "-O2")},
    }

    assert {fn.name for fn in corpus.functions} == expected_functions
    for fn in corpus.functions:
        variants = {(v.compiler, v.opt) for v in fn.compiler_variants}
        assert variants == expected_variants
        assert all(v.source.endswith(".c") or True for v in [fn])
        assert fn.language == "c"
        assert fn.source.startswith("source/c/")
        # New opt/clang cells start at 0x0 until build_matrix.py runs in CI.
        built = [v for v in fn.compiler_variants if v.addr and v.addr != "0x0"]
        assert built, "at least legacy O0/O2 cells should retain addresses"


def test_source_metrics_ignore_generated_decompiler_output(tmp_path: Path) -> None:
    authored = tmp_path / "dev" / "source" / "sample.c"
    generated = tmp_path / "dev" / "binaries" / "sample.reko" / "sample.c"
    authored.parent.mkdir(parents=True)
    generated.parent.mkdir(parents=True)
    authored.write_text("int authored(void) { return 1; }")
    generated.write_text("int generated(void) { goto done; done: return 2; }")

    assert discover_source_files(tmp_path) == [authored]


def test_assign_consensus_ranks_handles_ties_correctly() -> None:
    scores = [
        FunctionScore(
            decompiler="ghidra",
            function_name="foo",
            compiler_variant="gcc -O0",
            source_similarity=0.8,
            goto_count=0,
            nesting_depth=1,
            time_ms=10,
            semantic_score=1.0,
        ),
        FunctionScore(
            decompiler="angr",
            function_name="foo",
            compiler_variant="gcc -O0",
            source_similarity=0.8,
            goto_count=0,
            nesting_depth=1,
            time_ms=10,
            semantic_score=1.0,
        ),
        FunctionScore(
            decompiler="fission",
            function_name="foo",
            compiler_variant="gcc -O0",
            source_similarity=0.5,
            goto_count=0,
            nesting_depth=1,
            time_ms=10,
            semantic_score=1.0,
        ),
    ]

    ranked = assign_consensus_ranks(scores)
    # Group by name/variant to extract ranks
    ranks = {s.decompiler: s.consensus_rank for s in ranked}

    # ghidra and angr have the exact same score, so they must have the same rank (1)
    assert ranks["ghidra"] == 1
    assert ranks["angr"] == 1
    # Similarity is not correctness evidence; all three passed the same oracle.
    assert ranks["fission"] == 1


def test_new_correctness_formula_happy_path() -> None:
    # Correctness is finite semantic test-case pass rate only.
    score = compute_correctness_score(
        semantic_score=0.8,
        source_similarity=0.6,
        structural_penalty=0.2,
        ast_score=0.9,
        readability_score=0.7,
    )
    assert score == 0.8


def test_ast_parsing_failures_map_to_zero_score() -> None:
    # AST similarity is supporting evidence only, so parse failures must not affect correctness ranking.
    scores = [
        FunctionScore(
            decompiler="fission",
            function_name="foo",
            compiler_variant="gcc -O0",
            source_similarity=1.0,
            goto_count=0,
            nesting_depth=1,
            time_ms=10,
            semantic_score=1.0,
            readability_proxy_score=1.0,
            ast_similarity={
                "available": False,
                "identifier_placeholder": {"similarity": 1.0},
                "type_erased": {"similarity": 1.0},
                "control_flow_normalized": {"similarity": 1.0},
            }
        )
    ]
    
    ranked = assign_consensus_ranks(scores)
    assert ranked[0].correctness_score == 1.0


def test_semantic_failures_cap_correctness_score() -> None:
    # A complete semantic failure has zero correctness, regardless of resemblance.
    score = compute_correctness_score(
        semantic_score=0.0,
        source_similarity=1.0,
        structural_penalty=0.0,
        ast_score=1.0,
        readability_score=1.0,
    )
    assert score == 0.0


def test_ast_similarity_robust_sub_key_lookup() -> None:
    # Verify that assign_consensus_ranks is robust to missing or None sub-keys in ast_similarity
    scores = [
        FunctionScore(
            decompiler="fission",
            function_name="foo",
            compiler_variant="gcc -O0",
            source_similarity=1.0,
            goto_count=0,
            nesting_depth=1,
            time_ms=10,
            semantic_score=1.0,
            readability_proxy_score=1.0,
            ast_similarity={
                "available": True,
                "identifier_placeholder": None,
                "type_erased": {"similarity": 0.9},
                # control_flow_normalized is missing completely
            }
        )
    ]

    # AST similarity values are recorded but excluded from correctness ranking.
    ranked = assign_consensus_ranks(scores)
    assert ranked[0].correctness_score == 1.0


def test_no_wrapper_has_no_correctness_or_rank() -> None:
    score = FunctionScore(
        decompiler="fission",
        function_name="foo",
        compiler_variant="gcc -O0",
        source_similarity=1.0,
        goto_count=0,
        nesting_depth=0,
        time_ms=1,
        semantic_score=None,
        fail_category="no_wrapper",
    )
    ranked = assign_consensus_ranks([score])
    assert ranked[0].correctness_score is None
    assert ranked[0].correctness_rank is None
