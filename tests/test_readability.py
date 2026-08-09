from runner.readability import (
    analyze_readability,
    ast_structure_similarity,
    compare_readability_layers,
    summarize_readability_proxy_score,
)


def test_readability_tracks_generic_ghidra_names_and_artifacts() -> None:
    code = """
    undefined4 fibonacci(int param_1) {
      undefined4 uVar1;
      int local_10;
      uVar1 = __carry(param_1, local_10);
      return uVar1;
    }
    """

    metrics = analyze_readability(code, "ghidra")

    assert metrics["generic_naming_ratio"]["raw"]["generic"] >= 3
    assert metrics["generic_naming_ratio"]["raw"]["ratio"] > 0
    assert metrics["type_specificity"]["normalized"] < 0.5
    assert metrics["unresolved_artifacts"]["raw"]["details"]["sleigh_intrinsic"] == 1
    assert metrics["composite_score"] is None
    assert metrics["validated_against_humans"] is False


def test_ast_similarity_reports_three_separate_views() -> None:
    source = "int add(int lhs, int rhs) { return lhs + rhs; }"
    decompiled = "int add(int param_1, int param_2) { return param_1 + param_2; }"

    similarity = ast_structure_similarity(source, decompiled)

    assert similarity["available"] is True
    assert similarity["algorithm"] == "zhang_shasha"
    assert set(similarity) >= {
        "identifier_placeholder",
        "type_erased",
        "control_flow_normalized",
    }
    assert similarity["identifier_placeholder"]["similarity"] >= 0.8


def test_readability_proxy_summary_uses_normalized_artifact_value() -> None:
    metrics = {
        "generic_naming_ratio": {"normalized": 1.0},
        "type_specificity": {"normalized": 1.0},
        "expression_complexity": {"normalized": 1.0},
        "structured_control_flow": {"normalized": 1.0},
        "unresolved_artifacts": {"normalized": 0.0, "raw": {"total": 58}},
    }

    assert summarize_readability_proxy_score(metrics) == 0.8


def test_dual_layer_delta_keeps_nir_and_hir_evidence_separate() -> None:
    nir = "int f(int x) { int tmp; tmp = x; goto done; done: return tmp; }"
    hir = "int f(int x) { return x; }"
    nir_metrics = analyze_readability(nir, "fission")
    hir_metrics = analyze_readability(hir, "fission")

    comparison = compare_readability_layers(nir, hir, nir_metrics, hir_metrics)

    assert comparison["available"] is True
    assert comparison["text_differs"] is True
    assert comparison["interpretation"] == "hir_minus_nir"
    assert comparison["nir"]["goto_count"] == 1
    assert comparison["hir"]["goto_count"] == 0
    assert comparison["delta"]["goto_count"] == -1
    assert comparison["delta"]["bytes"] < 0
    assert comparison["validated_against_humans"] is False
