import { z } from "zod";

export const CoverageSchema = z.object({
  attempted: z.number(),
  clean: z.number(),
  ratio: z.number(),
});

export const ValiditySchema = z.object({
  valid: z.boolean(),
  publishable: z.boolean(),
  matrix_valid: z.boolean().optional(),
  adapter_output_valid: z.boolean().optional(),
  semantic_harness_valid: z.boolean().optional(),
  semantic_coverage_valid: z.boolean().optional(),
  semantic_result_valid: z.boolean().optional(),
  provenance_valid: z.boolean().optional(),
  artifact_valid: z.boolean().optional(),
  official_profile_valid: z.boolean().optional(),
  holdout_valid: z.boolean().optional(),
  fission_coverage: z.number().optional(),
  fission_attempted: z.number().optional(),
  fission_clean: z.number().optional(),
  backend_coverage: z.number().optional(),
  backend_attempted: z.number().optional(),
  backend_clean: z.number().optional(),
  reasons: z.array(z.string()).optional().default([]),
  publish_reasons: z.array(z.string()).optional().default([]),
});

export const RunMetaSchema = z.object({
  started_at: z.string().optional(),
  finished_at: z.string().optional(),
  duration_ms: z.number().optional(),
  runner_commit: z.string().optional(),
  corpus: z.string().optional(),
  profile: z.enum(["diagnostic", "realistic"]).optional(),
  limits: z.record(z.string(), z.unknown()).optional(),
  official: z.boolean(),
  run_id: z.string().optional(),
  fission_version: z.string().optional(),
  fission_source: z.string().optional(),
  legacy_source: z.boolean().optional(),
});

export const MatrixSchema = z.object({
  expected_decompilers: z.array(z.string()),
  expected_cells: z.array(z.object({
    decompiler: z.string().min(1),
    function_name: z.string().min(1),
    compiler_variant: z.string().min(1),
  })),
  expected_rows: z.number().int().nonnegative(),
  observed_rows: z.number().int().nonnegative(),
});

export const OracleSchema = z.object({
  mode: z.enum(["example_cases", "differential"]),
  valid: z.boolean(),
  oracle_subject: z.enum(["source_recompile", "original_binary"]).optional(),
  target_abi: z.string().optional(),
  compiler: z.string().optional(),
  compiler_version: z.string().optional(),
  runner: z.string().optional(),
  wrapper_sha256: z.string().regex(/^[0-9a-f]{64}$/).optional(),
  reference_binary_sha256: z.string().regex(/^[0-9a-f]{64}$/).optional(),
  row_evidence_sha256: z.string().regex(/^[0-9a-f]{64}$/).optional(),
  tested_rows: z.number().int().nonnegative().optional(),
});

export const RowSchema = z
  .object({
    decompiler: z.string(),
    function_name: z.string(),
    compiler_variant: z.string().min(1),
    binary: z.string().optional(),
    addr: z.string().optional(),
    source_similarity: z.number().default(0),
    semantic_score: z.number().nullable().default(null), // null = no_wrapper (untestable)
    correctness_score: z.number().nullable().default(null), // null = no_wrapper
    correctness_rank: z.number().int().positive().nullable(),
    goto_count: z.number().default(0),
    nesting_depth: z.number().default(0),
    time_ms: z.number().default(0),
    error: z.string().nullable().optional(),
    fail_category: z.string().nullable().optional(),
    fail_taxonomy: z.string().optional(),
    decompiled_code: z.string().optional(),
    decompiled_code_nir: z.string().optional(),
    decompiled_code_hir: z.string().optional(),
    pseudocode_layer: z.string().optional(),
    semantic_error: z.string().nullable().optional(),
    uses_intrinsics: z.boolean().optional(),
    oracle_evidence: z.record(z.string(), z.unknown()).optional(),
    output_diagnostics: z.record(z.string(), z.unknown()).optional(),
    bare_compile: z.record(z.string(), z.unknown()).optional(),
    track: z.string().optional(),
    isa_format: z.record(z.string(), z.string()).optional(),
    corpus: z.string().optional(),
    readability_metrics: z.record(z.string(), z.unknown()).optional(),
    readability_metrics_hir: z.record(z.string(), z.unknown()).optional(),
    readability_proxy_score: z.number().nullable().optional(),
    readability_proxy_score_hir: z.number().nullable().optional(),
    // Phase-2 AST similarity (corpus-only diagnostic; not ranking).
    ast_similarity: z.record(z.string(), z.unknown()).optional(),
    // Type correctness vs DWARF ground truth (diagnostic; not ranking).
    // null = no ground truth for this function, not a 0.0 miss.
    type_match_score: z.number().nullable().optional(),
    // Structural correctness vs source CFG (diagnostic; not ranking).
    // Lower is better, 0.0 = perfect structural match. null = no CFG pair
    // extracted for this function (degenerate/unparseable), not a miss.
    ged_score: z.number().nullable().optional(),
  })
  .passthrough();

/** Optional standard-set summary block (schema standard-set-v1). */
export const StandardSummarySchema = z
  .object({
    schema: z.literal("standard-set-v1").optional(),
    mvp: z
      .object({
        by_decompiler: z.record(z.string(), z.unknown()).optional(),
      })
      .passthrough()
      .optional(),
    secondary: z.record(z.string(), z.unknown()).optional(),
    extensions: z.record(z.string(), z.unknown()).optional(),
    diagnostics: z.record(z.string(), z.unknown()).optional(),
  })
  .passthrough()
  .optional();

export const ToolchainSchema = z.object({
  fission_version: z.string().optional(),
  fission_source: z.string().optional(),
  fission_git_sha: z.string().optional(),
  fission_source_fingerprint: z.string().optional(),
  runner_commit: z.string().optional(),
  runner_os: z.string().optional(),
  python_version: z.string().optional(),
  ci: z.string().optional(),
  github_run_id: z.string().optional(),
  github_actor: z.string().optional(),
});

export const BenchmarkEnvelopeSchema = z.object({
  schema_version: z.literal(2),
  run: RunMetaSchema,
  toolchain: ToolchainSchema,
  matrix: MatrixSchema,
  oracle: OracleSchema,
  validity: ValiditySchema,
  summary: StandardSummarySchema,
  rows: z.array(RowSchema),
}).superRefine((envelope, context) => {
  if (!envelope.run.official) return;
  const requiredRunFields = [
    envelope.run.run_id,
    envelope.run.started_at,
    envelope.run.finished_at,
    envelope.run.runner_commit,
    envelope.run.corpus,
    envelope.run.profile,
    envelope.run.limits,
  ];
  if (requiredRunFields.some((value) => value === undefined || value === "")) {
    context.addIssue({ code: "custom", message: "Official run provenance is incomplete", path: ["run"] });
  }
  if (envelope.matrix.expected_cells.length === 0) {
    context.addIssue({ code: "custom", message: "Official matrix is empty", path: ["matrix", "expected_cells"] });
  }
  if (
    envelope.matrix.expected_rows !== envelope.matrix.expected_cells.length
    || envelope.matrix.observed_rows !== envelope.rows.length
  ) {
    context.addIssue({ code: "custom", message: "Official matrix row counts do not match", path: ["matrix"] });
  }
  if (envelope.oracle.mode !== "differential" || envelope.oracle.valid !== true) {
    context.addIssue({ code: "custom", message: "Official differential oracle evidence is invalid", path: ["oracle"] });
  }
  const requiredOracleFields = [
    envelope.oracle.oracle_subject,
    envelope.oracle.target_abi,
    envelope.oracle.compiler,
    envelope.oracle.compiler_version,
    envelope.oracle.runner,
    envelope.oracle.wrapper_sha256,
    envelope.oracle.reference_binary_sha256,
    envelope.oracle.row_evidence_sha256,
    envelope.oracle.tested_rows,
  ];
  if (requiredOracleFields.some((value) => value === undefined || value === "")) {
    context.addIssue({ code: "custom", message: "Official oracle linkage is incomplete", path: ["oracle"] });
  }
});

export type BenchmarkEnvelope = z.infer<typeof BenchmarkEnvelopeSchema>;
export type Row = z.infer<typeof RowSchema>;
export type Validity = z.infer<typeof ValiditySchema>;
export type RunMeta = z.infer<typeof RunMetaSchema>;
export type Toolchain = z.infer<typeof ToolchainSchema>;
