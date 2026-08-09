# Decompiler Quality

The current decompiler-output similarity benchmark lives in `runner/`.

This folder marks the top-level quality stage in the layered benchmark model:

1. assembly parity
2. decode parity
3. raw p-code parity
4. CFG parity
5. function discovery
6. IR invariants
7. golden repros
8. telemetry gates
9. decompiler quality

Only rows that pass lower-level parity gates should be interpreted as meaningful
decompiler-quality comparisons.

## Fission dual NIR / HIR surfaces

Fission can emit two pseudocode surfaces from one IR build:

| Surface | Field(s) | Benchmark use |
|---|---|---|
| **NIR** (semantic-faithful) | `code`, `code_nir` | Semantic oracle, source similarity, structural diagnostics, correctness ranking inputs |
| **HIR** (readable) | `code_hir` | Readability proxy metrics when present |

Rules:

1. **Do not** score semantic correctness on HIR. Oracle compile/run always uses NIR.
2. **Do not** fold HIR readability proxies into `correctness_score` until the human
   comprehension study validates a readability composite.
3. When `code_nir` and `code_hir` differ, the runner records:
   - `decompiled_code` / `decompiled_code_nir` — NIR
   - `decompiled_code_hir` — HIR
   - `readability_metrics` — primary readability pass (prefers HIR)
   - `readability_metrics_nir` / `readability_proxy_score_nir` — explicit NIR evidence
   - `readability_metrics_hir` / `readability_proxy_score_hir` — explicit HIR evidence
   - `dual_layer_delta` — factual HIR-minus-NIR presentation deltas
   - `hir_semantic_guard` — diagnostic-only same-case semantic check
4. Other decompilers only populate `code`; dual fields stay empty and behavior is unchanged.
5. HIR semantic guard results never replace the NIR semantic score or enter
   `correctness_score`; they enforce the presentation contract diagnostically.

The Fission Docker adapter requests `fission_cli decomp … --json --layer nir` so the
primary `code` field remains NIR while still forwarding `code_nir` / `code_hir`.
