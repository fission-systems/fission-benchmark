"""
Semantic verification engine.
Compiles decompiled functions and runs them against unit test wrappers.
"""
import asyncio
import re
import subprocess
import tempfile
from pathlib import Path
try:
    from .test_wrappers import TEST_WRAPPERS
except ImportError:  # Direct script/module execution from runner/.
    from test_wrappers import TEST_WRAPPERS

STANDARD_HEADER = """
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

// Common decompiler types (Ghidra / Hex-Rays style)
typedef uint8_t byte;
typedef uint16_t word;
typedef uint32_t dword;
typedef uint64_t qword;
typedef int32_t undefined4;
typedef int64_t undefined8;
typedef int16_t undefined2;
typedef int8_t undefined1;
typedef int32_t undefined;

typedef unsigned int uint;
typedef unsigned long ulong;
typedef unsigned short ushort;
typedef unsigned char uchar;
typedef unsigned long long ulonglong;
typedef long long longlong;

// Reko-style fixed-width names
typedef uint8_t word8;
typedef uint16_t word16;
typedef uint32_t word32;
typedef uint64_t word64;
typedef int8_t int8;
typedef int16_t int16;
typedef int32_t int32;
typedef int64_t int64;
typedef uint8_t uint8;
typedef uint16_t uint16;
typedef uint32_t uint32;
typedef uint64_t uint64;

// Boomerang size types
typedef int8_t __size8;
typedef int16_t __size16;
typedef int32_t __size32;
typedef int64_t __size64;
typedef uint8_t __size8u;
typedef uint16_t __size16u;
typedef uint32_t __size32u;
typedef uint64_t __size64u;

// Rev.ng / other synthetic register types + no-op ABI markers
typedef uint64_t generic64_t;
typedef uint32_t generic32_t;
typedef uint16_t generic16_t;
typedef uint8_t generic8_t;
#ifndef _REG
#define _REG(x)
#endif
#ifndef _STACK
#define _STACK
#endif

// Structures used in corpus
typedef struct Pair {
    int key;
    int value;
} Pair;

// advanced_patterns.c fixtures
typedef struct Node {
    int value;
    struct Node *next;
} Node;
typedef struct Kv {
    int key;
    int value;
} Kv;
typedef int (*binop_fn)(int, int);
// File-scope helpers for apply_binop oracle cases (host gcc/clang; no nested fns).
static inline int bench_add_ints(int a, int b) { return a + b; }
static inline int bench_mul_ints(int a, int b) { return a * b; }

// Bitfield / union layout used by memory_layouts.c
struct Flags {
    uint32_t is_active : 1;
    uint32_t is_admin : 1;
    uint32_t privilege_level : 4;
    uint32_t reserved : 26;
};

union DataValue {
    int32_t int_val;
    float float_val;
    char char_vals[4];
};

struct ConfigNode {
    struct Flags flags;
    union DataValue val;
};
// Ghidra often emits bare ConfigNode* without the struct keyword.
typedef struct ConfigNode ConfigNode;
typedef struct Flags Flags;
typedef union DataValue DataValue;

// SLEIGH/Fission intrinsics — type-generic computation-based implementations
#define __carry(a, b)   (__builtin_add_overflow((a), (b), &(__typeof__(a)){0}))
#define __borrow(a, b)  ((a) < (b))
// Signed overflow detection: result sign differs from both operands' sign
#define __scarry(a, b)  (__builtin_add_overflow(((__typeof__(a))(a)), ((__typeof__(a))(b)), &((__typeof__(a)){0})))
#define __sborrow(a, b) (__builtin_sub_overflow(((__typeof__(a))(a)), ((__typeof__(a))(b)), &((__typeof__(a)){0})))

#define __popcount(x) __builtin_popcount(x)

// Win32 status/error constants, for corpus functions that traffic in them.
// Without these the harness punishes exactly the recovery it means to measure:
// a decompiler that names ERROR_ACCESS_DENIED emits an identifier this TU has
// never heard of and scores compile_error, while one that leaves the raw 5
// compiles and passes. Guarded so a decompiler emitting its own definitions
// wins instead of colliding.
#ifndef ERROR_SUCCESS
#define ERROR_SUCCESS 0L
#endif
#ifndef ERROR_FILE_NOT_FOUND
#define ERROR_FILE_NOT_FOUND 2L
#endif
#ifndef ERROR_ACCESS_DENIED
#define ERROR_ACCESS_DENIED 5L
#endif
#ifndef ERROR_INVALID_HANDLE
#define ERROR_INVALID_HANDLE 6L
#endif
#ifndef ERROR_NOT_ENOUGH_MEMORY
#define ERROR_NOT_ENOUGH_MEMORY 8L
#endif
#ifndef ERROR_INSUFFICIENT_BUFFER
#define ERROR_INSUFFICIENT_BUFFER 122L
#endif
#ifndef ERROR_SHARING_VIOLATION
#define ERROR_SHARING_VIOLATION 32L
#endif
#ifndef WAIT_OBJECT_0
#define WAIT_OBJECT_0 0x00000000L
#endif
#ifndef WAIT_ABANDONED
#define WAIT_ABANDONED 0x00000080L
#endif
#ifndef WAIT_TIMEOUT
#define WAIT_TIMEOUT 258L
#endif
"""


# 32-bit decompiler surface types that may hold pointers (m32). Do not match
# plain ``int`` — host wrappers for int-only functions stay host-native.
_HOST_WIDEN_TYPE = r"(?:uint|dword|undefined4|word32|uint32_t)"


def adapt_32bit_surface_for_host_semantic(func_name: str, decompiled_code: str) -> str:
    """Widen 32-bit formals of the target function for host recompilation.

    m32 decompilation correctly types pointers as ``uint``. The host semantic
    harness runs natively (no ``-m32`` on arm64) and wrappers pass host-width
    function pointers as ``ulonglong``. Truncating those to ``uint`` corrupts
    the pointer and crashes the harness — even when the decompiled *logic* is
    correct.

    This adaptation is harness-only; it does not change decompiler surface
    output or bare-compile diagnostics.
    """
    # uint _apply_binop(uint param_1, uint param_2, uint param_3)
    sig = re.compile(
        rf"^([ \t]*)({_HOST_WIDEN_TYPE})[ \t]+"
        rf"(_?{re.escape(func_name)})\s*\(([^;{{]*)\)",
        re.MULTILINE,
    )

    def _widen(match: re.Match[str]) -> str:
        indent, _ret, name, params = match.group(1), match.group(2), match.group(3), match.group(4)
        new_params = re.sub(rf"\b{_HOST_WIDEN_TYPE}\b", "ulonglong", params)
        return f"{indent}ulonglong {name}({new_params})"

    return sig.sub(_widen, decompiled_code, count=1)


def build_single_translation_unit(
    func_name: str,
    decompiled_code: str,
    cases: list[str],
) -> str:
    """Combine the decompilation and every semantic case into one C program."""
    decompiled_code = adapt_32bit_surface_for_host_semantic(func_name, decompiled_code)
    alias = ""
    if f" _{func_name}" in decompiled_code or f" *_{func_name}" in decompiled_code:
        alias = f"#define {func_name} _{func_name}\n"

    case_functions = []
    dispatch = []
    for index, case in enumerate(cases):
        renamed, replacements = re.subn(
            r"\bint\s+main\s*\(\s*(?:void)?\s*\)",
            f"static int semantic_case_{index}(void)",
            case,
            count=1,
        )
        if replacements != 1:
            raise ValueError(f"semantic case {index} does not define one int main()")
        case_functions.append(renamed)
        dispatch.append(
            f'  rc = semantic_case_{index}(); printf("CASE {index} %d\\n", rc); failures += rc != 0;'
        )

    dispatcher = "\n".join([
        "int main(void) {",
        "  int failures = 0;",
        "  int rc = 0;",
        *dispatch,
        "  return failures == 0 ? 0 : 1;",
        "}",
    ])
    return "\n".join([
        STANDARD_HEADER,
        decompiled_code,
        alias,
        *case_functions,
        dispatcher,
    ])


def verify_semantic_correctness(
    func_name: str,
    decompiled_code: str,
) -> tuple[float | None, str | None, str, int, int]:
    """
    Verify correctness of decompiled code by running all test cases.

    Returns:
        (score, error_detail, fail_category, cases_passed, cases_total)

    score: fraction of test cases passed (0.0–1.0)
    fail_category: one of:
        "no_wrapper"      — no test wrapper defined for this function
        "compile_error"   — GCC compilation failed
        "timeout"         — compilation or runtime exceeded time limit
        "runtime_error"   — binary exited with non-zero code (assertion failed or crash)
        "assertion_fail"  — all cases ran but at least one returned non-zero
        ""                — fully passed
    """
    if func_name not in TEST_WRAPPERS:
        # "no_wrapper" means the function is untestable, not that it failed.
        # Return None semantic_score so correctness ranking can treat this separately.
        return None, f"No test wrapper defined for function {func_name}", "no_wrapper", 0, 0

    if not decompiled_code.strip():
        return 0.0, "Empty decompilation output", "compile_error", 0, 0

    cases = TEST_WRAPPERS[func_name]
    if not cases:
        return None, "No test cases defined", "no_wrapper", 0, 0

    cases_total = len(cases)
    cases_passed = 0
    last_error = None
    last_category = ""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        source_file = tmpdir_path / "semantic_harness.c"
        binary_file = tmpdir_path / "semantic_harness"
        try:
            source = build_single_translation_unit(func_name, decompiled_code, cases)
        except ValueError as exc:
            return 0.0, str(exc), "fixture_error", 0, cases_total
        source_file.write_text(source, encoding="utf-8")

        try:
            result = subprocess.run(
                [
                    "gcc",
                    "-w",
                    "-O0",
                    str(source_file),
                    "-o",
                    str(binary_file),
                ],
                capture_output=True,
                text=True,
                timeout=5.0,
            )
            if result.returncode != 0:
                error = f"Compilation failed:\n{result.stderr[:300]}"
                return 0.0, error, "compile_error", 0, cases_total
        except subprocess.TimeoutExpired:
            return 0.0, "Compilation timed out (5s)", "timeout", 0, cases_total
        except Exception as e:
            return 0.0, f"Compiler execution failed: {e}", "compile_error", 0, cases_total

        try:
            run_res = subprocess.run(
                [str(binary_file)],
                capture_output=True,
                text=True,
                timeout=5.0,
            )
        except subprocess.TimeoutExpired:
            return 0.0, "Semantic harness execution timed out (5s)", "timeout", 0, cases_total
        except Exception as exc:
            return 0.0, f"Semantic harness execution failed: {exc}", "runtime_error", 0, cases_total

        observed: dict[int, int] = {}
        for line in run_res.stdout.splitlines():
            match = re.fullmatch(r"CASE (\d+) (-?\d+)", line.strip())
            if match:
                observed[int(match.group(1))] = int(match.group(2))
        cases_passed = sum(observed.get(index) == 0 for index in range(cases_total))
        if len(observed) != cases_total:
            last_error = f"Semantic harness emitted {len(observed)}/{cases_total} case results"
            last_category = "runtime_error"
        elif cases_passed != cases_total:
            failed = [str(index) for index in range(cases_total) if observed[index] != 0]
            last_error = f"Semantic cases failed: {', '.join(failed)}"
            last_category = "assertion_fail"

    score = cases_passed / cases_total if cases_total > 0 else 0.0

    if cases_passed == cases_total:
        return score, None, "", cases_passed, cases_total
    else:
        return score, last_error, last_category or "assertion_fail", cases_passed, cases_total


async def verify_semantic_correctness_async(
    func_name: str,
    decompiled_code: str,
) -> tuple[float | None, str | None, str, int, int]:
    """Async wrapper for verify_semantic_correctness.

    Runs the blocking GCC compilation and execution in a thread pool so that the
    asyncio event loop is not blocked during parallel batch decompilation scoring.
    Use this from async contexts (runner.py decompile_batch_and_score).
    """
    return await asyncio.to_thread(verify_semantic_correctness, func_name, decompiled_code)
