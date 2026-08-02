import { readFile } from "fs/promises";
import path from "path";
import {
  BenchmarkEnvelopeSchema,
  type BenchmarkEnvelope,
} from "./schemas";

const REPO_RAW =
  "https://raw.githubusercontent.com/fission-systems/fission-benchmark/main";

/**
 * Ordered candidates for multi-decomp dashboard data.
 * `results/latest.json` is only written on full publication; until then
 * `dev_latest.json` (tracked on main) is the public display fallback.
 */
function candidateUrls(): string[] {
  const urls: string[] = [];
  if (process.env.BENCHMARK_LATEST_URL) {
    urls.push(process.env.BENCHMARK_LATEST_URL);
  }
  // Same-origin public file when present on Vercel / local `public/`.
  if (process.env.VERCEL_URL) {
    urls.push(`https://${process.env.VERCEL_URL}/benchmark-latest.json`);
  }
  urls.push(
    `${REPO_RAW}/results/latest.json`,
    `${REPO_RAW}/results/dev_latest.json`,
  );
  return urls;
}

export type MvpDecompilerStats = {
  decompiler: string;
  attempted: number;
  adapterClean: number;
  invalidBoundary: number;
  semanticTested: number;
  noWrapper: number;
  meanSemantic: number | null;
  perfectRows: number;
  meanTimeMs: number | null;
  taxonomy: Record<string, number>;
  oracleSubject: string | null;
};

export type CrossVariantRow = {
  decompiler: string;
  compiler_variant: string;
  compiler: string;
  opt: string;
  tested_rows: number;
  mean_pass_rate: number | null;
  perfect_rows: number;
};

/** Non-ranking extension pivots from envelope.summary. */
export type QualityExtensions = {
  bareByDecompiler: Record<string, Record<string, number | null | undefined>>;
  readabilityByDecompiler: Record<
    string,
    Record<string, number | null | undefined>
  >;
  byTrack: Record<string, Record<string, number | null | undefined>>;
  byLanguage: Record<string, Record<string, number | null | undefined>>;
  byIsa: Record<string, Record<string, number | null | undefined>>;
  byFormat: Record<string, Record<string, number | null | undefined>>;
  byOpt: Record<string, Record<string, number | null | undefined>>;
};

export function extractQualityExtensions(
  data: BenchmarkEnvelope | null | undefined,
): QualityExtensions {
  const empty: QualityExtensions = {
    bareByDecompiler: {},
    readabilityByDecompiler: {},
    byTrack: {},
    byLanguage: {},
    byIsa: {},
    byFormat: {},
    byOpt: {},
  };
  if (!data) return empty;
  const summary = (data as { summary?: Record<string, unknown> }).summary;
  if (!summary || typeof summary !== "object") return empty;
  const extensions = (summary.extensions || {}) as Record<string, unknown>;
  const diagnostics = (summary.diagnostics || {}) as Record<string, unknown>;
  const bare =
    (extensions.bare_compile as Record<string, unknown> | undefined) ||
    (diagnostics.bare_compile as Record<string, unknown> | undefined) ||
    {};
  const readability =
    (extensions.readability_axis as Record<string, unknown> | undefined) ||
    (diagnostics.readability_axis as Record<string, unknown> | undefined) ||
    {};
  const tracks =
    (extensions.tracks as Record<string, unknown> | undefined) ||
    (diagnostics.tracks as Record<string, unknown> | undefined) ||
    {};
  return {
    bareByDecompiler: (bare.by_decompiler as QualityExtensions["bareByDecompiler"]) || {},
    readabilityByDecompiler:
      (readability.by_decompiler as QualityExtensions["readabilityByDecompiler"]) ||
      {},
    byTrack: (tracks.by_track as QualityExtensions["byTrack"]) || {},
    byLanguage: (tracks.by_language as QualityExtensions["byLanguage"]) || {},
    byIsa: (tracks.by_isa as QualityExtensions["byIsa"]) || {},
    byFormat: (tracks.by_format as QualityExtensions["byFormat"]) || {},
    byOpt: (tracks.by_opt as QualityExtensions["byOpt"]) || {},
  };
}

/**
 * Strict loader for call sites that already handle missing data.
 * Prefer {@link getLatestBenchmarkOptional} on pages — never throw during
 * Next.js prerender/export.
 */
export async function getLatestBenchmark(): Promise<BenchmarkEnvelope> {
  const envelope = await getLatestBenchmarkOptional({ requirePublishable: true });
  if (!envelope) {
    throw new Error("Failed to load a publishable official benchmark envelope");
  }
  return envelope;
}

async function tryParseEnvelope(raw: unknown): Promise<BenchmarkEnvelope | null> {
  try {
    return BenchmarkEnvelopeSchema.parse(raw);
  } catch {
    return null;
  }
}

async function loadFromPublicFile(): Promise<BenchmarkEnvelope | null> {
  try {
    const filePath = path.join(process.cwd(), "public", "benchmark-latest.json");
    const text = await readFile(filePath, "utf8");
    return tryParseEnvelope(JSON.parse(text));
  } catch {
    return null;
  }
}

/**
 * Load multi-decomp envelope without throwing.
 *
 * Default: accept any valid envelope (`valid` preferred but not required for
 * schema parse). Set `requirePublishable: true` only for gates that need the
 * official publication artifact.
 */
export async function getLatestBenchmarkOptional(options?: {
  requirePublishable?: boolean;
}): Promise<BenchmarkEnvelope | null> {
  // Intentionally NOT using Next.js data cache for multi-MB JSON.
  const requirePublishable = options?.requirePublishable === true;
  const preferValid = options?.requirePublishable !== true;

  const candidates: BenchmarkEnvelope[] = [];

  const local = await loadFromPublicFile();
  if (local) candidates.push(local);

  for (const url of candidateUrls()) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) continue;
      const env = await tryParseEnvelope(await res.json());
      if (env) candidates.push(env);
    } catch {
      // try next source
    }
  }

  if (candidates.length === 0) return null;

  // Prefer publishable, then measurement-valid, then first parseable.
  const ranked = [...candidates].sort((a, b) => {
    const score = (e: BenchmarkEnvelope) =>
      (e.validity?.publishable ? 4 : 0) +
      (e.validity?.valid ? 2 : 0) +
      (Array.isArray(e.rows) && e.rows.length > 0 ? 1 : 0);
    return score(b) - score(a);
  });

  for (const env of ranked) {
    if (requirePublishable && env.validity?.publishable !== true) continue;
    if (preferValid && env.validity?.valid === false && env.rows?.length === 0) {
      continue;
    }
    return env;
  }
  return ranked[0] ?? null;
}

function isAdapterFailure(row: BenchmarkEnvelope["rows"][number]): boolean {
  return Boolean(row.error) || row.fail_category === "adapter_error";
}

/** Prefer envelope.summary.mvp when present; otherwise aggregate from rows. */
export function groupByDecompiler(data: BenchmarkEnvelope): MvpDecompilerStats[] {
  const fromSummary = data.summary?.mvp?.by_decompiler as
    | Record<
        string,
        {
          semantic?: {
            mean_pass_rate?: number | null;
            perfect_rows?: number;
            tested_rows?: number;
            oracle_subject?: string | null;
          };
          coverage?: {
            attempted?: number;
            adapter_clean?: number;
            invalid_boundary?: number;
            semantic_tested?: number;
            no_wrapper?: number;
          };
          fail_taxonomy?: Record<string, number>;
          runtime?: { mean_ms?: number | null };
        }
      >
    | undefined;

  if (fromSummary && Object.keys(fromSummary).length > 0) {
    return Object.entries(fromSummary)
      .map(([decompiler, s]) => ({
        decompiler,
        attempted: s.coverage?.attempted ?? 0,
        adapterClean: s.coverage?.adapter_clean ?? 0,
        invalidBoundary: s.coverage?.invalid_boundary ?? 0,
        semanticTested: s.coverage?.semantic_tested ?? s.semantic?.tested_rows ?? 0,
        noWrapper: s.coverage?.no_wrapper ?? 0,
        meanSemantic:
          s.semantic?.mean_pass_rate === undefined || s.semantic?.mean_pass_rate === null
            ? null
            : Number(s.semantic.mean_pass_rate),
        perfectRows: s.semantic?.perfect_rows ?? 0,
        meanTimeMs:
          s.runtime?.mean_ms === undefined || s.runtime?.mean_ms === null
            ? null
            : Number(s.runtime.mean_ms),
        taxonomy: s.fail_taxonomy ?? {},
        oracleSubject: s.semantic?.oracle_subject ?? null,
      }))
      .sort((a, b) => {
        if (a.decompiler === "fission") return -1;
        if (b.decompiler === "fission") return 1;
        return (b.meanSemantic ?? -1) - (a.meanSemantic ?? -1);
      });
  }

  // Fallback for legacy envelopes without summary.
  const map = new Map<
    string,
    {
      attempted: number;
      adapterClean: number;
      invalidBoundary: number;
      semanticScores: number[];
      noWrapper: number;
      times: number[];
      taxonomy: Record<string, number>;
    }
  >();

  for (const row of data.rows) {
    const d = row.decompiler;
    if (!map.has(d)) {
      map.set(d, {
        attempted: 0,
        adapterClean: 0,
        invalidBoundary: 0,
        semanticScores: [],
        noWrapper: 0,
        times: [],
        taxonomy: {},
      });
    }
    const s = map.get(d)!;
    s.attempted++;
    const tax = row.fail_taxonomy || (isAdapterFailure(row) ? "adapter_error" : "other");
    s.taxonomy[tax] = (s.taxonomy[tax] ?? 0) + 1;
    if (tax === "boundary_mismatch" || tax === "whole_program_output") {
      s.invalidBoundary++;
    }
    if (!isAdapterFailure(row) && tax !== "boundary_mismatch" && tax !== "whole_program_output") {
      s.adapterClean++;
    }
    if (row.fail_category === "no_wrapper" || tax === "no_wrapper") {
      s.noWrapper++;
    } else if (
      row.semantic_score !== null &&
      row.semantic_score !== undefined &&
      !isAdapterFailure(row)
    ) {
      s.semanticScores.push(row.semantic_score);
    }
    if (row.time_ms > 0) s.times.push(row.time_ms);
  }

  return Array.from(map.entries())
    .map(([decompiler, s]) => ({
      decompiler,
      attempted: s.attempted,
      adapterClean: s.adapterClean,
      invalidBoundary: s.invalidBoundary,
      semanticTested: s.semanticScores.length,
      noWrapper: s.noWrapper,
      meanSemantic:
        s.semanticScores.length > 0
          ? s.semanticScores.reduce((a, b) => a + b, 0) / s.semanticScores.length
          : null,
      perfectRows: s.semanticScores.filter((v) => v >= 1).length,
      meanTimeMs:
        s.times.length > 0 ? s.times.reduce((a, b) => a + b, 0) / s.times.length : null,
      taxonomy: s.taxonomy,
      oracleSubject: null,
    }))
    .sort((a, b) => {
      if (a.decompiler === "fission") return -1;
      if (b.decompiler === "fission") return 1;
      return (b.meanSemantic ?? -1) - (a.meanSemantic ?? -1);
    });
}

/** @deprecated Use groupByDecompiler(envelope) — kept for call sites that only have rows. */
export function groupByDecompilerRows(rows: BenchmarkEnvelope["rows"]): MvpDecompilerStats[] {
  const stub = {
    schema_version: 2 as const,
    run: { official: false },
    toolchain: {},
    matrix: {
      expected_decompilers: [] as string[],
      expected_cells: [] as { decompiler: string; function_name: string; compiler_variant: string }[],
      expected_rows: 0,
      observed_rows: 0,
    },
    oracle: { mode: "example_cases" as const, valid: false },
    validity: { valid: false, publishable: false, reasons: [] as string[], publish_reasons: [] as string[] },
    rows,
  };
  return groupByDecompiler(stub as unknown as BenchmarkEnvelope);
}

export function getCrossVariantRows(data: BenchmarkEnvelope): CrossVariantRow[] {
  const raw = data.summary?.extensions?.cross_variant as
    | {
        by_decompiler_variant?: Record<
          string,
          Array<{
            compiler_variant: string;
            compiler: string;
            opt: string;
            tested_rows: number;
            mean_pass_rate: number | null;
            perfect_rows: number;
          }>
        >;
      }
    | undefined;
  if (!raw?.by_decompiler_variant) return [];
  const out: CrossVariantRow[] = [];
  for (const [decompiler, entries] of Object.entries(raw.by_decompiler_variant)) {
    for (const e of entries) {
      out.push({ decompiler, ...e });
    }
  }
  return out.sort((a, b) => {
    if (a.decompiler !== b.decompiler) {
      if (a.decompiler === "fission") return -1;
      if (b.decompiler === "fission") return 1;
      return a.decompiler.localeCompare(b.decompiler);
    }
    return a.compiler_variant.localeCompare(b.compiler_variant);
  });
}

export function getCfgSecondary(data: BenchmarkEnvelope): {
  status: string;
  byDecompiler: Record<string, { match?: number; mismatch?: number; match_rate?: number | null }>;
} {
  const cfg = data.summary?.secondary?.cfg as
    | {
        status?: string;
        by_decompiler?: Record<
          string,
          { match?: number; mismatch?: number; match_rate?: number | null }
        >;
      }
    | undefined;
  return {
    status: cfg?.status ?? "absent",
    byDecompiler: cfg?.by_decompiler ?? {},
  };
}

/** Get unique function names in the result */
export function getFunctionNames(rows: BenchmarkEnvelope["rows"]): string[] {
  return [...new Set(rows.map((r) => r.function_name))].sort();
}

/** Get rows for a specific function */
export function getRowsForFunction(rows: BenchmarkEnvelope["rows"], fn: string) {
  return rows.filter((r) => r.function_name === fn);
}

export const CORE_DECOMPILERS = ["fission", "ghidra"] as const;

export type SameFunctionToolStats = {
  decompiler: string;
  cohort: string | null;
  sameFunctionRate: number | null;
  sameFunctionLooseRate: number | null;
  byStatus: Record<string, number>;
};

export type SameFunctionSummary = {
  schema: string | null;
  coreRate: number | null;
  multiRate: number | null;
  allRate: number | null;
  coreLoose: number | null;
  multiLoose: number | null;
  byDecompiler: SameFunctionToolStats[];
  addressAnchorRate: number | null;
};

/** MVP-0 same-function matrix from envelope.summary (if present). */
export function getSameFunctionSummary(
  data: BenchmarkEnvelope
): SameFunctionSummary | null {
  const raw = (data.summary?.mvp as { same_function?: Record<string, unknown> } | undefined)
    ?.same_function;
  if (!raw || typeof raw !== "object") return null;

  const cohorts = (raw.cohorts || {}) as Record<
    string,
    {
      same_function_rate?: number | null;
      same_function_loose_rate?: number | null;
    }
  >;
  const by = (raw.by_decompiler || {}) as Record<
    string,
    {
      cohort?: string;
      same_function_rate?: number | null;
      same_function_loose_rate?: number | null;
      by_status?: Record<string, number>;
    }
  >;
  const totals = (raw.totals || {}) as {
    address_anchor_rate?: number | null;
  };

  const byDecompiler: SameFunctionToolStats[] = Object.entries(by)
    .map(([decompiler, s]) => ({
      decompiler,
      cohort: s.cohort ?? null,
      sameFunctionRate:
        s.same_function_rate === undefined || s.same_function_rate === null
          ? null
          : Number(s.same_function_rate),
      sameFunctionLooseRate:
        s.same_function_loose_rate === undefined || s.same_function_loose_rate === null
          ? null
          : Number(s.same_function_loose_rate),
      byStatus: s.by_status ?? {},
    }))
    .sort((a, b) => {
      if (a.decompiler === "fission") return -1;
      if (b.decompiler === "fission") return 1;
      if (a.decompiler === "ghidra") return -1;
      if (b.decompiler === "ghidra") return 1;
      return a.decompiler.localeCompare(b.decompiler);
    });

  return {
    schema: typeof raw.schema === "string" ? raw.schema : null,
    coreRate: cohorts.core?.same_function_rate ?? null,
    multiRate: cohorts.multi?.same_function_rate ?? null,
    allRate: cohorts.all?.same_function_rate ?? null,
    coreLoose: cohorts.core?.same_function_loose_rate ?? null,
    multiLoose: cohorts.multi?.same_function_loose_rate ?? null,
    byDecompiler,
    addressAnchorRate: totals.address_anchor_rate ?? null,
  };
}

/** Filter MVP stats / rows to the Fission + Ghidra core pair. */
export function filterCorePairStats(
  stats: MvpDecompilerStats[]
): MvpDecompilerStats[] {
  const set = new Set<string>(CORE_DECOMPILERS);
  return stats.filter((s) => set.has(s.decompiler));
}

export function filterCorePairRows(
  rows: BenchmarkEnvelope["rows"]
): BenchmarkEnvelope["rows"] {
  const set = new Set<string>(CORE_DECOMPILERS);
  return rows.filter((r) => set.has(r.decompiler));
}

export function pct(rate: number | null | undefined, digits = 1): string {
  if (rate === null || rate === undefined || Number.isNaN(rate)) return "—";
  return `${(rate * 100).toFixed(digits)}%`;
}

export function meanFmt(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

/** Non-ranking readability / similarity diagnostic row (per decompiler). */
export type ReadabilityDiagStats = {
  decompiler: string;
  rows: number;
  meanSourceSimilarity: number | null;
  meanAstSimilarity: number | null;
  meanReadabilityProxy: number | null;
  meanGotoCount: number | null;
  meanNestingDepth: number | null;
  meanTempLocRatio: number | null;
  meanGnrNormalized: number | null;
  meanFlagSoupPerLoc: number | null;
};

function meanOf(xs: number[]): number | null {
  if (xs.length === 0) return null;
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}

function astControlFlowSimilarity(row: BenchmarkEnvelope["rows"][number]): number | null {
  const ast = row.ast_similarity as
    | {
        available?: boolean;
        control_flow_normalized?: { similarity?: number };
        identifier_placeholder?: { similarity?: number };
      }
    | undefined;
  if (!ast || ast.available === false) return null;
  const cf = ast.control_flow_normalized?.similarity;
  if (typeof cf === "number" && !Number.isNaN(cf)) return cf;
  const id = ast.identifier_placeholder?.similarity;
  if (typeof id === "number" && !Number.isNaN(id)) return id;
  return null;
}

function gnrNormalized(row: BenchmarkEnvelope["rows"][number]): number | null {
  const metrics = row.readability_metrics as
    | { generic_naming_ratio?: { normalized?: number } }
    | undefined;
  const n = metrics?.generic_naming_ratio?.normalized;
  return typeof n === "number" && !Number.isNaN(n) ? n : null;
}

function tempLocRatio(row: BenchmarkEnvelope["rows"][number]): number | null {
  const metrics = row.readability_metrics as
    | {
        expression_complexity?: {
          raw?: { temporary_identifier_loc_ratio?: number };
        };
      }
    | undefined;
  const n = metrics?.expression_complexity?.raw?.temporary_identifier_loc_ratio;
  return typeof n === "number" && !Number.isNaN(n) ? n : null;
}

/**
 * Build per-decompiler readability / similarity diagnostics.
 * Prefer summary.extensions.readability_axis means when present; always
 * enrich from rows for source similarity / AST / GNR.
 * Sort is fission-first then alphabetical — never by proxy score (non-ranking).
 */
export function buildReadabilityDiagnostics(
  data: BenchmarkEnvelope,
): ReadabilityDiagStats[] {
  const ext = extractQualityExtensions(data).readabilityByDecompiler;
  const byTool = new Map<
    string,
    {
      sim: number[];
      ast: number[];
      proxy: number[];
      goto: number[];
      nesting: number[];
      temp: number[];
      gnr: number[];
      flag: number[];
    }
  >();

  const ensure = (tool: string) => {
    if (!byTool.has(tool)) {
      byTool.set(tool, {
        sim: [],
        ast: [],
        proxy: [],
        goto: [],
        nesting: [],
        temp: [],
        gnr: [],
        flag: [],
      });
    }
    return byTool.get(tool)!;
  };

  for (const tool of Object.keys(ext)) {
    ensure(tool);
  }

  for (const row of data.rows) {
    if (row.error) continue;
    const code = (row.decompiled_code || "").trim();
    if (!code && row.readability_proxy_score == null && !row.readability_metrics) {
      continue;
    }
    const slot = ensure(row.decompiler);
    if (typeof row.source_similarity === "number") {
      slot.sim.push(row.source_similarity);
    }
    const ast = astControlFlowSimilarity(row);
    if (ast != null) slot.ast.push(ast);
    if (
      row.readability_proxy_score != null &&
      typeof row.readability_proxy_score === "number"
    ) {
      slot.proxy.push(row.readability_proxy_score);
    }
    if (typeof row.goto_count === "number") slot.goto.push(row.goto_count);
    if (typeof row.nesting_depth === "number") {
      slot.nesting.push(row.nesting_depth);
    }
    const temp = tempLocRatio(row);
    if (temp != null) slot.temp.push(temp);
    const gnr = gnrNormalized(row);
    if (gnr != null) slot.gnr.push(gnr);
    // Flag-soup density from decompiled text (matches runner aggregate).
    if (code) {
      const flags = (code.match(/\b(?:zf|sf|cf|of|pf|af)\b/gi) || []).length;
      const loc = Math.max(code.split("\n").length, 1);
      slot.flag.push(flags / loc);
    }
  }

  const tools = new Set([...Object.keys(ext), ...byTool.keys()]);
  const rows: ReadabilityDiagStats[] = [...tools].map((decompiler) => {
    const fromExt = ext[decompiler] || {};
    const slot = byTool.get(decompiler) || {
      sim: [],
      ast: [],
      proxy: [],
      goto: [],
      nesting: [],
      temp: [],
      gnr: [],
      flag: [],
    };
    const extProxy =
      typeof fromExt.mean_readability_proxy === "number"
        ? fromExt.mean_readability_proxy
        : null;
    const extGoto =
      typeof fromExt.mean_goto_count === "number" ? fromExt.mean_goto_count : null;
    const extNest =
      typeof fromExt.mean_nesting_depth === "number"
        ? fromExt.mean_nesting_depth
        : null;
    const extTemp =
      typeof fromExt.mean_temp_loc_ratio === "number"
        ? fromExt.mean_temp_loc_ratio
        : null;
    const extFlag =
      typeof fromExt.mean_flag_soup_per_loc === "number"
        ? fromExt.mean_flag_soup_per_loc
        : null;
    const rowCount = Math.max(
      typeof fromExt.rows === "number" ? fromExt.rows : 0,
      slot.sim.length,
      slot.proxy.length,
      slot.goto.length,
    );
    return {
      decompiler,
      rows: rowCount,
      meanSourceSimilarity: meanOf(slot.sim),
      meanAstSimilarity: meanOf(slot.ast),
      meanReadabilityProxy: meanOf(slot.proxy) ?? extProxy,
      meanGotoCount: meanOf(slot.goto) ?? extGoto,
      meanNestingDepth: meanOf(slot.nesting) ?? extNest,
      meanTempLocRatio: meanOf(slot.temp) ?? extTemp,
      meanGnrNormalized: meanOf(slot.gnr),
      meanFlagSoupPerLoc: meanOf(slot.flag) ?? extFlag,
    };
  });

  return rows.sort((a, b) => {
    if (a.decompiler === "fission") return -1;
    if (b.decompiler === "fission") return 1;
    if (a.decompiler === "ghidra") return -1;
    if (b.decompiler === "ghidra") return 1;
    return a.decompiler.localeCompare(b.decompiler);
  });
}
