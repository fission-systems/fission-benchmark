"""
Scoring engine for multi-decompiler comparison.

Metrics:
  1. source_similarity  — normalized edit distance vs original C source
  2. semantic_score     — fraction of test cases passed (0.0–1.0)
  3. structural_penalty — relative goto/nesting increase vs original source
  4. correctness_score  — semantic-gated correctness ranking metric
  5. correctness_rank   — relative correctness position among all decompilers
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Any


# Intrinsic functions that may affect semantic score validity
INTRINSIC_NAMES = {"__carry", "__scarry", "__sborrow", "__borrow"}


@dataclass
class FunctionScore:
    decompiler: str
    function_name: str
    compiler_variant: str       # e.g. "gcc -O2"
    source_similarity: float    # 0.0 – 1.0
    goto_count: int
    nesting_depth: int
    time_ms: int
    error: str | None = None
    semantic_score: float | None = None     # None = no_wrapper (untestable); 0.0–1.0 otherwise
    semantic_error: str | None = None
    fail_category: str | None = None    # compile_error|runtime_error|timeout|assertion_fail|no_wrapper
    cases_passed: int = 0               # number of test cases passed
    cases_total: int = 0                # total number of test cases
    structural_penalty: float = 0.0     # 0.0–1.0 based on relative goto/nesting delta
    correctness_score: float | None = None  # None when no_wrapper and no other signal
    correctness_rank: int | None = None # set after all decompilers run
    readability_proxy_score: float | None = None  # unvalidated proxy evidence only
    composite_score: float = 0.0        # deprecated alias for correctness_score
    consensus_rank: int | None = None   # deprecated alias for correctness_rank
    uses_intrinsics: bool = False       # True if decompiled code uses __carry/__scarry etc.
    decompiled_code: str = ""           # primary surface used for scoring (NIR for Fission)
    # Dual NIR/HIR surfaces when the adapter provides them (Fission dual printers).
    # Semantic oracle always scores NIR; readability proxies prefer HIR.
    decompiled_code_nir: str = ""
    decompiled_code_hir: str = ""
    pseudocode_layer: str = ""          # adapter-reported layer selection, e.g. "nir"
    readability_metrics: dict[str, Any] = field(default_factory=dict)
    # Optional second readability pass on HIR (when dual surfaces differ).
    readability_metrics_hir: dict[str, Any] = field(default_factory=dict)
    readability_proxy_score_hir: float | None = None
    ast_similarity: dict[str, Any] = field(default_factory=dict)
    # Type correctness vs DWARF ground truth. None = no ground truth
    # available for this function (no debug info, or DWARF extraction
    # failed) -- distinct from a real 0.0 (ground truth existed, nothing
    # matched). Diagnostic evidence only, not part of semantic ranking.
    type_match_score: float | None = None
    type_match_metadata: dict[str, Any] = field(default_factory=dict)
    # Structural correctness: source-vs-decompiled CFG edit distance (lower
    # is better; 0.0 = perfect structural match). None = no CFG on one side
    # (parse failure / degenerate source), not a real 0 miss. Diagnostic
    # evidence only, not part of semantic ranking.
    ged_score: float | None = None
    ged_metadata: dict[str, Any] = field(default_factory=dict)
    # Same-toolchain recompilation assembly match. None = matching compiler or
    # ABI unavailable; 0.0 includes compile/extraction failures. Diagnostic only.
    recompilation_score: float | None = None
    recompilation: dict[str, Any] = field(default_factory=dict)
    output_diagnostics: dict[str, Any] = field(default_factory=dict)
    oracle_evidence: dict[str, Any] = field(default_factory=dict)
    # Stable exclusive fail bucket for standard-set reporting (see standard_summary).
    fail_taxonomy: str = ""
    # Extension diagnostics (never used for semantic ranking).
    bare_compile: dict[str, Any] = field(default_factory=dict)
    track: str = ""
    language: str = "c"
    isa_format: dict[str, str] = field(default_factory=dict)
    binary: str = ""
    corpus: str = ""



# ── Correctness Score ─────────────────────────────────────────────────────────

# Correctness is semantic evidence only. Source resemblance, structure and
# readability remain independent diagnostic axes.
WEIGHT_SEMANTIC = 1.0
WEIGHT_AST = 0.0
WEIGHT_READABILITY = 0.0
WEIGHT_SIMILARITY = 0.0
WEIGHT_STRUCTURAL = 0.0


def compute_correctness_score(
    semantic_score: float | None,
    source_similarity: float,
    structural_penalty: float,
    ast_score: float = 0.0,
    readability_score: float = 0.0,
) -> float | None:
    """
    Return finite semantic test-case pass rate, or ``None`` without an oracle.

    Other parameters remain for saved-result compatibility but never affect
    correctness or ranking.
    """
    _ = source_similarity, structural_penalty, ast_score, readability_score
    if semantic_score is None:
        return None
    return round(semantic_score, 4)


def compute_composite(
    semantic_score: float,
    source_similarity: float,
    structural_penalty: float,
) -> float | None:
    """Deprecated compatibility wrapper for compute_correctness_score."""
    return compute_correctness_score(semantic_score, source_similarity, structural_penalty)


# ── Structural Penalty ────────────────────────────────────────────────────────

def compute_structural_penalty(
    goto_count: int,
    nesting_depth: int,
    source_goto_count: int = 0,
    source_nesting_depth: int = 0,
) -> float:
    """
    Compute structural penalty based on relative increase vs original source.

    If the original source already uses gotos, no penalty for matching count.
    Penalty increases linearly: 5 extra gotos → 100% goto penalty.
    """
    goto_delta = max(0, goto_count - source_goto_count)
    goto_pen = min(goto_delta / 5.0, 1.0)

    depth_delta = max(0, nesting_depth - source_nesting_depth)
    depth_pen = min(depth_delta / 3.0, 1.0)

    return round(goto_pen * 0.7 + depth_pen * 0.3, 4)


# ── Normalizers & Similarity ──────────────────────────────────────────────────

def normalize_code(code: str) -> str:
    """Strip comments, normalize whitespace, lowercase identifiers."""
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    code = re.sub(r"//[^\n]*", "", code)
    code = re.sub(r"\s+", " ", code).strip().lower()
    return code


def source_similarity(source: str, decompiled: str) -> float:
    """Normalized SequenceMatcher ratio on normalized code."""
    if not decompiled.strip():
        return 0.0
    a = normalize_code(source)
    b = normalize_code(decompiled)
    return round(difflib.SequenceMatcher(None, a, b).ratio(), 4)


def extract_function_source(source: str, function_name: str) -> str:
    """
    Extract one C function body from a source file.

    Handles:
    - Standard C functions with any return type
    - Qualifiers: static, inline, extern, __attribute__(...), __declspec(...)
    - Functions returning pointers or function pointers (best-effort)

    If extraction fails, callers can fall back to whole-file source.
    """
    # Strip comments first so they don't confuse brace matching.
    stripped = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    stripped = re.sub(r"//[^\n]*", "", stripped)

    # Match the function definition: optional qualifiers/return type, then function_name(
    # We look for the name as a whole word, preceded by a non-identifier character.
    pattern = re.compile(
        rf"(?:^|\n)(?:[\w\s\*,<>\[\]]+?)?\b{re.escape(function_name)}\s*\(",
        re.MULTILINE,
    )

    for match in pattern.finditer(stripped):
        # Verify this is a definition (has a body), not a declaration (ends with ;)
        # Scan forward to find the opening brace of the body.
        rest = stripped[match.start():]
        # Find matching { — skip past the parameter list first
        paren_depth = 0
        brace_start = -1
        for idx, ch in enumerate(rest):
            if ch == '(':
                paren_depth += 1
            elif ch == ')':
                paren_depth -= 1
            elif ch == '{' and paren_depth == 0:
                brace_start = match.start() + idx
                break
            elif ch == ';' and paren_depth == 0:
                break  # declaration, not definition

        if brace_start == -1:
            continue

        # Now find the matching closing brace.
        depth = 0
        for idx in range(brace_start, len(stripped)):
            c = stripped[idx]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return stripped[match.start():idx + 1].strip()
        break  # matched open brace but not close — malformed

    return ""


def check_uses_intrinsics(code: str) -> bool:
    """Return True if decompiled code uses any SLEIGH intrinsic functions."""
    # Use word-boundary matching to avoid false positives on names like __carry_flag.
    for name in INTRINSIC_NAMES:
        if re.search(rf"\b{re.escape(name)}\b", code):
            return True
    return False


def count_gotos(code: str) -> int:
    return len(re.findall(r"\bgoto\b", code))


def measure_nesting_depth(code: str) -> int:
    """Estimate maximum nesting depth by brace counting, ignoring string/char literals."""
    depth = 0
    max_depth = 0
    i = 0
    while i < len(code):
        ch = code[i]
        # Skip C string literals: "..."
        if ch == '"':
            i += 1
            while i < len(code):
                if code[i] == '\\':  # escape sequence
                    i += 2
                    continue
                if code[i] == '"':
                    break
                i += 1
        # Skip C char literals: '...'
        elif ch == "'":
            i += 1
            while i < len(code):
                if code[i] == '\\':
                    i += 2
                    continue
                if code[i] == "'":
                    break
                i += 1
        elif ch == '{':
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch == '}':
            depth = max(0, depth - 1)
        i += 1
    return max_depth


def structural_score(code: str) -> tuple[int, int]:
    """Returns (goto_count, max_nesting_depth)."""
    return count_gotos(code), measure_nesting_depth(code)


# ── Consensus Ranking ─────────────────────────────────────────────────────────

def assign_consensus_ranks(
    scores: list[FunctionScore],
    source_goto_counts: dict[str, int] | None = None,
    source_nesting_depths: dict[str, int] | None = None,
) -> list[FunctionScore]:
    """
    For the same function+variant, rank decompilers by correctness_score desc.

    Also assigns structural_penalty and correctness_score for each score entry.

    Consensus interpretation:
      - All decompilers rank low  → objectively hard function
      - Only Fission ranks low    → Fission quality issue
    """
    from collections import defaultdict

    src_gotos = source_goto_counts or {}
    src_depths = source_nesting_depths or {}

    # First pass: structural penalty + correctness for every row.
    # correctness_score tracks semantic even when adapter/output error is set
    # (contract check: correctness_score == semantic_score when finite).
    for s in scores:
        if s.error is None:
            s.structural_penalty = compute_structural_penalty(
                s.goto_count,
                s.nesting_depth,
                src_gotos.get(s.function_name, 0),
                src_depths.get(s.function_name, 0),
            )
            s.uses_intrinsics = s.uses_intrinsics or check_uses_intrinsics(
                s.decompiled_code
            )
        s.correctness_score = compute_correctness_score(
            s.semantic_score,  # may be None for no_wrapper
            s.source_similarity,
            s.structural_penalty,
        )
        s.composite_score = s.correctness_score or 0.0

    # Group by (function_name, compiler_variant)
    groups: dict[tuple, list[FunctionScore]] = defaultdict(list)
    for s in scores:
        groups[(s.function_name, s.compiler_variant)].append(s)

    result = []
    for group in groups.values():
        valid = [
            s for s in group
            if s.error is None and s.semantic_score is not None
        ]
        for s in group:
            if s not in valid:
                s.correctness_rank = None
                s.consensus_rank = None
        # Rank by finite semantic evidence only.
        valid.sort(key=lambda s: s.correctness_score if s.correctness_score is not None else 0.0, reverse=True)
        current_rank = 1
        for idx, s in enumerate(valid):
            prev_score = valid[idx - 1].correctness_score if valid[idx - 1].correctness_score is not None else 0.0
            curr_score = s.correctness_score if s.correctness_score is not None else 0.0
            if idx > 0 and curr_score < prev_score:
                current_rank = idx + 1
            s.correctness_rank = current_rank
            s.consensus_rank = current_rank
        # errored entries get no rank
        result.extend(group)

    return result


# ── Consensus Badge ───────────────────────────────────────────────────────────

def get_consensus_badge(
    function_name: str,
    compiler_variant: str,
    scores: list[FunctionScore],
    fission_decompiler_name: str = "fission",
    low_threshold: float = 0.20,
) -> str:
    """
    Return a consensus badge for a function+variant group.

    🔴 Fission-only gap: Fission is low but others are not
    ⚪ Universally low (harness): All decompilers are low under the current
        test harness — may indicate a common wrapper/ABI issue rather than
        an objectively hard function
    🟢 Fission leads: Fission is #1
    """
    group = [
        s for s in scores
        if s.function_name == function_name
        and s.compiler_variant == compiler_variant
        and s.error is None
    ]
    if not group:
        return ""

    fission_scores = [s for s in group if s.decompiler == fission_decompiler_name]
    other_scores = [s for s in group if s.decompiler != fission_decompiler_name]

    if not fission_scores:
        return ""

    fission_correctness = fission_scores[0].correctness_score
    others_correctness = [s.correctness_score for s in other_scores]

    # Fission leads
    if fission_scores[0].correctness_rank == 1:
        return "🟢 Fission leads"

    # All decompilers low under the current harness
    all_low = fission_correctness < low_threshold and all(c < low_threshold for c in others_correctness)
    if all_low:
        return "⚪ Universally low (harness)"

    # Fission-only gap: Fission is low, but at least one other is clearly higher
    others_avg = sum(others_correctness) / len(others_correctness) if others_correctness else 0.0
    if fission_correctness < low_threshold and others_avg > low_threshold * 2:
        return "🔴 Fission-only gap"

    return ""
