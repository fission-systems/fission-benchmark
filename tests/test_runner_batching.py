import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from runner.checkpoint import BenchmarkCheckpoint
from runner.scoring import FunctionScore
from runner import runner as benchmark_runner


def test_scale_batches_are_bounded_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BENCHMARK_MAX_BATCH_FUNCTIONS", raising=False)

    assert benchmark_runner.resolve_max_batch_functions("scale") == 128
    assert benchmark_runner.resolve_max_batch_functions("dev") == 0
    assert [len(chunk) for chunk in benchmark_runner.chunk_targets(list(range(260)), 128)] == [
        128,
        128,
        4,
    ]


def test_batch_size_override_is_validated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BENCHMARK_MAX_BATCH_FUNCTIONS", "32")
    assert benchmark_runner.resolve_max_batch_functions("scale") == 32

    monkeypatch.setenv("BENCHMARK_MAX_BATCH_FUNCTIONS", "-1")
    with pytest.raises(ValueError, match="non-negative integer"):
        benchmark_runner.resolve_max_batch_functions("scale")


def test_scale_semantic_precheck_preserves_adapter_failures() -> None:
    external = SimpleNamespace(semantic={"mode": "none"})

    clean = benchmark_runner.semantic_precheck(external, None, ["register_pseudo_inputs"])
    failed = benchmark_runner.semantic_precheck(external, "preview_timeout", [])

    assert clean is not None and clean[0] is None and clean[2] == "no_wrapper"
    assert failed == (0.0, "preview_timeout", "adapter_error", 0, 0)


def test_output_preflight_excludes_invalid_boundary_from_metrics() -> None:
    code = "\n".join(
        f"int unrelated_{index}(void) {{ return {index}; }}"
        for index in range(4)
    )

    preflight = benchmark_runner.preflight_decompile_item(
        "target_function",
        "fission",
        "0x401000",
        {"code": code, "code_nir": code},
        duplicate_count=1,
    )

    assert preflight["output_diagnostics"]["status"] == "whole_program_output"
    assert preflight["error"] == (
        "Decompiler returned whole-program or truncated output, not a target function"
    )
    assert preflight["metric_eligible"] is False


def test_output_preflight_keeps_clean_function_metric_eligible() -> None:
    code = "int target_function(void) { return 7; }"

    preflight = benchmark_runner.preflight_decompile_item(
        "target_function",
        "ghidra",
        "0x401000",
        {"code": code},
        duplicate_count=1,
    )

    assert preflight["output_diagnostics"]["status"] == "direct_function"
    assert preflight["error"] is None
    assert preflight["metric_eligible"] is True


def test_dual_layer_hir_guard_is_measured_without_replacing_nir_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binary = tmp_path / "fixture.bin"
    source = tmp_path / "fixture.c"
    binary.write_bytes(b"fixture")
    source.write_text("int target_function(int x) { return x; }", encoding="utf-8")
    nir = "int target_function(int x) { int tmp; tmp = x; goto done; done: return tmp; }"
    hir = "int target_function(int x) { return 0; }"
    function = SimpleNamespace(
        name="target_function",
        subject_name="target_function",
        language="c",
        project="fixture",
        semantic={},
    )
    variant = SimpleNamespace(
        addr="0x401000",
        compiler="gcc",
        opt="-O0",
        format="elf",
        isa="x86_64",
        abi_profile="sysv_amd64",
    )

    class FakeResponse:
        status_code = 200
        text = ""

        @staticmethod
        def json():
            return {
                "results": [
                    {
                        "addr": variant.addr,
                        "code": nir,
                        "code_nir": nir,
                        "code_hir": hir,
                        "layer": "nir",
                        "time_ms": 1,
                    }
                ],
                "time_ms": 1,
            }

    class FakeClient:
        @staticmethod
        async def post(*_args, **_kwargs):
            return FakeResponse()

    semantic_inputs: list[str] = []

    async def fake_verify(_name: str, code: str):
        semantic_inputs.append(code)
        if code == nir:
            return 1.0, None, None, 2, 2
        return 0.0, "wrong result", "assertion_fail", 0, 2

    monkeypatch.setattr(benchmark_runner, "extract_decompiled_cfgs", lambda _items: {})
    monkeypatch.setattr(benchmark_runner, "extract_source_cfgs", lambda _path: {})
    monkeypatch.setattr(benchmark_runner, "ground_truth_for_binary", lambda _path: {})
    monkeypatch.setattr(
        benchmark_runner,
        "measure_recompilation",
        lambda *_args, **_kwargs: (None, {"category": "not_measured"}),
    )
    monkeypatch.setattr(
        benchmark_runner,
        "try_bare_compile",
        lambda _code: {"ok": True, "category": "ok"},
    )
    monkeypatch.setattr(
        benchmark_runner, "verify_semantic_correctness_async", fake_verify
    )

    rows = asyncio.run(
        benchmark_runner.decompile_batch_and_score(
            FakeClient(),
            "fission",
            "http://fission",
            binary,
            [(function, variant, source.read_text(), source, "authored_source_fallback")],
            asyncio.Semaphore(1),
            None,
        )
    )

    assert semantic_inputs == [nir, hir]
    assert len(rows) == 1
    row = rows[0]
    assert row.semantic_score == 1.0
    assert row.cases_passed == 2
    assert row.hir_semantic_guard["ranking_input"] is False
    assert row.hir_semantic_guard["score"] == 0.0
    assert row.hir_semantic_guard["matches_nir"] is False
    assert row.readability_metrics_nir
    assert row.readability_metrics_hir
    assert row.dual_layer_delta["delta"]["goto_count"] == -1


def test_invalid_boundary_never_reaches_joern_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    code = "\n".join(
        f"int unrelated_{index}(void) {{ return {index}; }}"
        for index in range(4)
    )
    binary = tmp_path / "fixture.bin"
    binary.write_bytes(b"fixture")
    source = tmp_path / "fixture.c"
    source.write_text("int target_function(void) { return 7; }", encoding="utf-8")
    function = SimpleNamespace(
        name="target_function",
        subject_name="decbench::fixture::target_function",
        language="c",
        project="fixture",
        semantic={"mode": "none"},
    )
    variant = SimpleNamespace(
        addr="0x401000",
        compiler="gcc",
        opt="-O0",
        format="elf",
        isa="x86_64",
        abi_profile="sysv_amd64",
    )

    class FakeResponse:
        status_code = 200
        text = ""

        @staticmethod
        def json():
            return {
                "results": [{"addr": variant.addr, "code": code, "time_ms": 1}],
                "time_ms": 1,
            }

    class FakeClient:
        @staticmethod
        async def post(*_args, **_kwargs):
            return FakeResponse()

    joern_inputs: list[dict[str, str]] = []

    def capture_joern_input(functions: dict[str, str]):
        joern_inputs.append(functions)
        return {}

    monkeypatch.setattr(benchmark_runner, "extract_decompiled_cfgs", capture_joern_input)
    monkeypatch.setattr(benchmark_runner, "ground_truth_for_binary", lambda _path: {})
    monkeypatch.setattr(
        benchmark_runner,
        "measure_recompilation",
        lambda *_args, **_kwargs: (None, {"category": "decompilation_error"}),
    )

    rows = asyncio.run(
        benchmark_runner.decompile_batch_and_score(
            FakeClient(),
            "fission",
            "http://fission",
            binary,
            [(function, variant, source.read_text(), source, "authored_source_fallback")],
            asyncio.Semaphore(1),
            None,
        )
    )

    assert joern_inputs == [{}]
    assert len(rows) == 1
    assert rows[0].ged_score is None
    assert rows[0].error == (
        "Decompiler returned whole-program or truncated output, not a target function"
    )


def test_scale_missing_published_cfg_is_explicitly_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    corpus_root = tmp_path / "corpus"
    monkeypatch.setattr(benchmark_runner, "CORPUS_ROOT", corpus_root)
    source_path = corpus_root / "scale" / "sources" / "nuttx"

    path, basis = benchmark_runner.resolve_ged_source(
        "scale",
        source_path,
        SimpleNamespace(source_cfg="", preprocessed_source=""),
    )

    assert path == source_path
    assert basis == "external_source_cfg_unavailable"
    assert benchmark_runner.ged_source_contract(basis) == "unavailable_external_dataset"


def test_authored_corpus_retains_source_fallback(tmp_path: Path) -> None:
    source_path = tmp_path / "fixture.c"
    path, basis = benchmark_runner.resolve_ged_source(
        "dev",
        source_path,
        SimpleNamespace(source_cfg="", preprocessed_source=""),
    )

    assert path == source_path
    assert basis == "authored_source_fallback"


def test_tool_binary_chunks_execute_sequentially(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[int]] = []
    active = 0

    async def fake_decompile(_client, _dname, _url, _binary, targets, _sem, _oracle, **_kwargs):
        nonlocal active
        active += 1
        assert active == 1
        calls.append(list(targets))
        await asyncio.sleep(0)
        active -= 1
        return []

    monkeypatch.setattr(
        benchmark_runner, "decompile_batch_and_score", fake_decompile
    )
    asyncio.run(
        benchmark_runner.decompile_target_group(
            None,
            "fission",
            "http://fission",
            Path("fixture.bin"),
            list(range(5)),
            asyncio.Semaphore(2),
            None,
            corpus_split="scale",
            checkpoint=None,
            max_batch_functions=2,
        )
    )

    assert calls == [[0, 1], [2, 3], [4]]


def test_transport_failure_is_not_checkpointed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus_root = tmp_path / "corpus"
    source = corpus_root / "scale" / "sources" / "fixture.c"
    binary = corpus_root / "scale" / "binaries" / "fixture"
    source.parent.mkdir(parents=True)
    binary.parent.mkdir(parents=True)
    source.write_text("int foo(void) { return 1; }", encoding="utf-8")
    binary.write_bytes(b"fixture")
    monkeypatch.setattr(benchmark_runner, "CORPUS_ROOT", corpus_root)

    variant = SimpleNamespace(
        compiler="gcc",
        opt="-O0",
        addr="0x1",
        binary="binaries/fixture",
        source_cfg="",
        preprocessed_source="",
    )
    function = SimpleNamespace(
        name="foo",
        subject_name="decbench::fixture::foo",
        source="sources/fixture.c",
        compiler_variants=[variant],
        language="c",
        project="fixture",
    )

    async def fake_transport_failure(
        _client, dname, _url, _binary, targets, _sem, _oracle, **_kwargs
    ):
        assert len(targets) == 1
        return [
            FunctionScore(
                decompiler=dname,
                function_name=function.subject_name,
                compiler_variant="gcc -O0",
                source_similarity=0.0,
                goto_count=0,
                nesting_depth=0,
                time_ms=0,
                error="Batch decompile error: timeout",
                fail_category="adapter_error",
            )
        ]

    monkeypatch.setattr(
        benchmark_runner, "decompile_batch_and_score", fake_transport_failure
    )
    checkpoint = BenchmarkCheckpoint(
        tmp_path / "checkpoint.jsonl", contract={"profile": "scale-test"}
    )

    rows = asyncio.run(
        benchmark_runner.run_all(
            [function],
            {"fission": "http://fission"},
            "scale",
            None,
            None,
            None,
            checkpoint,
            max_batch_functions=128,
        )
    )

    assert len(rows) == 1
    assert rows[0].error == "Batch decompile error: timeout"
    assert checkpoint.recovered_rows == []
