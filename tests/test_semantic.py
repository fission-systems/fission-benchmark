from types import SimpleNamespace

from runner.semantic import build_single_translation_unit, verify_semantic_correctness
from runner.test_wrappers import TEST_WRAPPERS


def test_single_translation_unit_preserves_static_target() -> None:
    source = build_single_translation_unit(
        "identity",
        "static int identity(int value) { return value; }",
        ["int main() { return identity(1) == 1 ? 0 : 1; }"],
    )

    assert "static int identity" in source
    assert "static int semantic_case_0(void)" in source
    assert source.count("int main(void)") == 1


def test_host_semantic_widens_m32_uint_formals_for_function_pointers() -> None:
    """m32 surface uses uint for pointers; host wrappers pass ulonglong fps."""
    from runner.semantic import adapt_32bit_surface_for_host_semantic

    code = (
        "uint _apply_binop(uint param_1, uint param_2, uint param_3)\n"
        "{\n"
        "    if (param_1) {\n"
        "        return ((unsigned long long (*)())(param_1))(param_2, param_3);\n"
        "    }\n"
        "    return 0;\n"
        "}\n"
    )
    adapted = adapt_32bit_surface_for_host_semantic("apply_binop", code)
    assert "ulonglong _apply_binop(ulonglong param_1, ulonglong param_2, ulonglong param_3)" in adapted
    # Body unchanged (still casts param_1 as callable).
    assert "((unsigned long long (*)())(param_1))" in adapted

    score, err, cat, passed, total = verify_semantic_correctness("apply_binop", code)
    assert (score, cat, passed, total) == (1.0, "", 6, 6), (score, err, cat, passed, total)


def test_semantic_verification_compiles_once_and_runs_each_case(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
        calls.append(command)
        if command[0] == "gcc":
            return SimpleNamespace(returncode=0, stderr="", stdout="")
        output = "\n".join(
            f"CASE {index} 0" for index in range(len(TEST_WRAPPERS["clamp"]))
        )
        return SimpleNamespace(returncode=0, stderr="", stdout=output)

    monkeypatch.setattr("runner.semantic.subprocess.run", fake_run)
    # This asserts on the *number of compiler invocations*, so it must observe
    # a cache miss. Without this the run's own cache (or an earlier test's)
    # answers from disk and gcc is never called at all.
    monkeypatch.setenv("FISSION_BENCHMARK_NO_CACHE", "1")

    result = verify_semantic_correctness(
        "clamp",
        "int clamp(int value, int lo, int hi) { return value < lo ? lo : value > hi ? hi : value; }",
    )

    assert result == (1.0, None, "", 6, 6)
    gcc_calls = [command for command in calls if command[0] == "gcc"]
    runtime_calls = [command for command in calls if command[0] != "gcc"]
    assert "-c" not in gcc_calls[0]
    assert len(gcc_calls) == 1
    assert len(runtime_calls) == 1
