# Readability Benchmark

This stage records readability evidence separately from semantic correctness.
It deliberately does not publish a final readability composite until the human
comprehension validation study proves which proxy metrics correlate with actual
understanding.

## Phase 1: Proxy Metrics

`runner/readability.py` computes five AST-oriented proxy families for each
successful decompiler output:

1. Generic Naming Ratio
   - Raw: generic identifier count, total identifier count, ratio.
   - Normalized: `1 - ratio`.
   - Generic patterns are configured per decompiler, so Fission, Ghidra,
     Boomerang, Radare2, angr, Snowman, rev.ng, and Reko naming conventions can
     be judged without a single length-based rule.

2. Type Specificity
   - Raw: average type score and typed node count.
   - Strong semantic types score higher than raw-width primitives, which score
     higher than collapsed `undefined*` or `unknown*` types.

3. Expression Complexity
   - Raw: operator count, average expression depth, max cast depth, ternary and
     comma counts, temporary identifier count, LOC, and temporary/LOC ratio.
   - Normalized: higher means less complex under the current proxy.

4. Structured Control Flow
   - Raw: structured constructs, goto count, nesting depth, suspected
     irreducible loop, state flag count, and structured ratio.
   - This avoids treating low goto count as sufficient when a decompiler hides
     control flow behind state flags.

5. Unresolved Artifacts
   - Raw: counts of unresolved SLEIGH-like intrinsics, LOWWORD/HIWORD-style
     macros, register-name leakage, and collapsed types.

Each metric stores raw values and a 0-1 normalized proxy value. These normalized
values are not weights and are not combined into a final readability score.

## Phase 2: Source AST Similarity

For corpus entries with original source, the runner also records three auxiliary
Zhang-Shasha tree-edit-distance views:

- `identifier_placeholder`: identifiers are abstracted.
- `type_erased`: type annotations are abstracted.
- `control_flow_normalized`: loop and switch-arm shapes are normalized.

This is corpus-only supporting evidence. It is not a primary readability score
because code can differ from the original and still be easier to understand.

## Evidence Base

- R2I frames decompiled-code readability around AST-extracted feature evidence.
- DIRTY, DIRE, and VarBERT motivate treating variable names and recovered types
  as first-class readability signals.
- DecompileBench-style evaluation motivates keeping correctness, structural
  similarity, and readability evidence separate.
- Prior understandability studies warn that automatic code metrics can fail to
  correlate with human comprehension, so Phase 3 is mandatory before publishing
  a composite.

## Implementation Contract

Every result row may include:

- `readability_metrics`: Phase 1 proxy families, raw and normalized.
- `readability_metrics_nir` / `readability_proxy_score_nir`: explicit NIR
  readability evidence.
- `readability_metrics_hir` / `readability_proxy_score_hir`: explicit HIR
  readability evidence.
- `dual_layer_delta`: factual `HIR - NIR` changes in bytes, LOC, gotos,
  nesting, temporaries, generic identifiers, and the unvalidated proxy.
- `hir_semantic_guard`: diagnostic execution against the same cases used for
  NIR. It never enters correctness ranking.
- `ast_similarity`: Phase 2 corpus-only AST similarity views.

For Fission dual printers (when the adapter supplies both surfaces):

- Semantic correctness still runs on **NIR** (`decompiled_code` / `code_nir`).
- Primary `readability_metrics` prefer the **HIR** surface when available.
- Explicit NIR/HIR metric families and `dual_layer_delta` retain both surfaces
  even though the backward-compatible primary readability view prefers HIR.
- A differing HIR surface is executed as a non-ranking semantic guard whenever
  the row has an executable oracle. This catches presentation-contract losses
  without replacing NIR as the semantic oracle.

No result row should include a final `readability_score` until Phase 3 and Phase
4 are complete. Dual NIR/HIR capture is evidence plumbing only — it does not
promote HIR into the correctness ranking formula.
