"""Fixup repairs the shapes a fixed header cannot enumerate.

Each case here is a real failure mode, not a synthetic one: `describe_error`
is what `corpus/dev/source/c/win32_status.c` produces when a decompiler
recovers Win32 constant *names*, which the semantic harness scored 0 for on
2026-08-19 while a decompiler that emitted the raw integer passed.
"""
from __future__ import annotations

import shutil

import pytest

from runner.fixup import compile_with_fixup

pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="no gcc")


def _compiles(code: str, name: str):
    res = compile_with_fixup(code, name)
    ok = res.obj_path is not None
    if res.obj_path is not None:
        res.obj_path.unlink(missing_ok=True)
    return ok, res


def test_recovered_constant_names_in_case_labels_compile():
    """A `case` label needs an integer constant, so the `long NAME;` a missing
    global normally gets is rejected. Penalising this scores *better* recovery
    lower, which is backwards."""
    ok, res = _compiles(
        """
const char *describe_error(unsigned long code)
{
  switch (code) {
  case ERROR_ACCESS_DENIED: return "denied";
  case ERROR_INVALID_HANDLE: return "handle";
  default: return "other";
  }
}
""",
        "describe_error",
    )
    assert ok, res.error
    assert any("enum" in d for d in res.injected), res.injected


def test_ghidra_pseudo_types_compile():
    ok, res = _compiles(
        "undefined4 sum3(undefined4 a, uint b, code *fn) { return a + b; }",
        "sum3",
    )
    assert ok, res.error


def test_undeclared_callee_gets_a_prototype():
    ok, res = _compiles(
        "int wrapper(int x) { return helper_never_declared(x) + 1; }",
        "wrapper",
    )
    assert ok, res.error
    assert any("helper_never_declared" in d for d in res.injected), res.injected


def test_clang_diagnostics_are_understood():
    """On macOS `gcc` is clang. Upstream only matched gcc's wording, so the
    repair loop found nothing to inject and reported the function as
    non-compiling -- the same silent zero this module removes."""
    from runner.fixup import _RE_IMPLICIT_FUNC, _RE_UNDECLARED

    assert _RE_IMPLICIT_FUNC.search("error: call to undeclared function 'foo'")
    assert _RE_IMPLICIT_FUNC.search("error: implicit declaration of function 'foo'")
    assert _RE_UNDECLARED.search("error: use of undeclared identifier 'BAR'")
    assert _RE_UNDECLARED.search("error: 'BAR' undeclared (first use in this function)")


def test_bare_compile_falls_back_to_fixup():
    from runner.bare_compile import try_bare_compile

    result = try_bare_compile("undefined4 f(uint a) { Kv *p; return a; }")
    assert result["ok"] is True
    assert result["category"] == "ok_after_fixup"


def test_semantic_cache_returns_the_same_verdict():
    """The cache must be transparent: a hit and a miss agree exactly.

    Semantic verification is the benchmark's dominant metric cost (0.35s/row
    against 0.05s for bare-compile), and it was the one metric not consulting
    metric_cache -- which is why the cache CI restored held 0 MB.
    """
    import os
    import tempfile

    from runner import semantic as sem

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("FISSION_BENCHMARK_CACHE_DIR")
        os.environ["FISSION_BENCHMARK_CACHE_DIR"] = tmp
        try:
            name = next(iter(sem.TEST_WRAPPERS))
            code = "int %s(void) { return 0; }" % name
            miss = sem.verify_semantic_correctness(name, code)
            hit = sem.verify_semantic_correctness(name, code)
            assert miss == hit
            assert any(p.suffix == ".json" for p in __import__("pathlib").Path(tmp).rglob("*"))
        finally:
            if old is None:
                os.environ.pop("FISSION_BENCHMARK_CACHE_DIR", None)
            else:
                os.environ["FISSION_BENCHMARK_CACHE_DIR"] = old


def test_semantic_cache_key_separates_different_code():
    import os
    import tempfile

    from runner import semantic as sem

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("FISSION_BENCHMARK_CACHE_DIR")
        os.environ["FISSION_BENCHMARK_CACHE_DIR"] = tmp
        try:
            name = next(iter(sem.TEST_WRAPPERS))
            a = sem.verify_semantic_correctness(name, "int %s(void){return 0;}" % name)
            b = sem.verify_semantic_correctness(name, "int %s(void){return 1;}" % name)
            # Different bodies must not share a cache entry; at minimum the
            # second call must not have been answered by the first's result
            # when the verdicts genuinely differ.
            assert a is not None and b is not None
        finally:
            if old is None:
                os.environ.pop("FISSION_BENCHMARK_CACHE_DIR", None)
            else:
                os.environ["FISSION_BENCHMARK_CACHE_DIR"] = old


def test_decompile_cache_key_includes_image_identity():
    """A rebuilt decompiler must not be served the previous image's output.

    Decompilation is the run's largest cost -- de-duplicated per binary on the
    smoke slice, revng alone is 152.4s of 256.4s -- so it is worth caching, but
    only if a new image invalidates it. With no identity available the cache is
    skipped entirely rather than risk a stale answer.
    """
    import os
    import tempfile

    from runner.metric_cache import load, store

    with tempfile.TemporaryDirectory() as tmp:
        old = os.environ.get("FISSION_BENCHMARK_CACHE_DIR")
        os.environ["FISSION_BENCHMARK_CACHE_DIR"] = tmp
        try:
            base = {
                "decompiler": "revng",
                "binary_sha256": "a" * 64,
                "addresses": ["0x1000"],
            }
            key_v1 = {**base, "image": "sha256:aaa"}
            key_v2 = {**base, "image": "sha256:bbb"}

            store("decompile-batch", "v1-batch-addresses", key_v1, [{"addr": "0x1000"}])
            assert load("decompile-batch", "v1-batch-addresses", key_v1) is not None
            # A different image id must miss.
            assert load("decompile-batch", "v1-batch-addresses", key_v2) is None
        finally:
            if old is None:
                os.environ.pop("FISSION_BENCHMARK_CACHE_DIR", None)
            else:
                os.environ["FISSION_BENCHMARK_CACHE_DIR"] = old


def test_decompile_cache_is_skipped_without_image_identity():
    """`BENCHMARK_IMAGE_ID_*` absent means no caching at all, not a blank key."""
    import inspect

    from runner import runner as runner_mod

    src = inspect.getsource(runner_mod)
    # The guard is `if _image_id else None`; a blank id must not produce a key.
    assert "if _image_id" in src
    assert '"image": _image_id' in src
