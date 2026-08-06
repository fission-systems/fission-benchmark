import { readFile } from "fs/promises";
import path from "path";
import {
  BenchmarkEnvelopeSchema,
  type BenchmarkEnvelope,
} from "./schemas";

const REPO_RAW =
  "https://raw.githubusercontent.com/fission-systems/fission-benchmark/main";

/** Ordered release-channel candidates. Development/legacy results are excluded. */
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
    `${REPO_RAW}/public/benchmark-latest.json`,
    `${REPO_RAW}/results/latest.json`,
  );
  return urls;
}

export type MvpDecompilerStats = {
  decompiler: string;
  attempted: number;
  adapterClean: number;
  invalidBoundary: number;
  semanticTested: number;
  semanticSharedRows: number;
  noWrapper: number;
  meanSemantic: number | null;
  perfectRows: number;
  meanTimeMs: number | null;
  taxonomy: Record<string, number>;
  oracleSubject: string | null;
  // Type correctness vs DWARF ground truth (diagnostic; not ranking).
  meanTypeMatch: number | null;
  typeMatchTestedRows: number;
  typeMatchSharedRows: number;
  typeMatchPerfectRows: number;
  typeMatchPerfectRate: number | null;
  // Structural correctness vs source CFG (diagnostic; not ranking).
  // Lower is better, 0.0 = perfect structural match.
  meanGed: number | null;
  gedTestedRows: number;
  gedSharedRows: number;
  gedPerfectRows: number;
  gedPerfectRate: number | null;
};

export type CrossVariantRow = {
  decompiler: string;
  compiler_variant: string;
  compiler: string;
  opt: string;
  tested_rows: number;
  shared_rows?: number;
  mean_pass_rate: number | null;
  perfect_rows: number;
};

/** Non-ranking extension pivots from envelope.summary. */
export type QualityExtensions = {
  bareByDecompiler: Record<string, Record<string, number | null | undefined>>;
  recompilationByDecompiler: Record<
    string,
    Record<string, number | null | undefined>
  >;
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

export type MeasurementMetric = {
  shared_rows: number;
  observed_rows: number;
  perfect_rows: number;
  perfect_rate: number | null;
  shared_mean?: number | null;
  observed_mean: number | null;
};

export type MeasurementToolHealth = {
  attempted: number;
  output_clean: number;
  output_clean_rate: number | null;
  semantic: MeasurementMetric;
  ged: MeasurementMetric;
  type_match: MeasurementMetric;
  compile: {
    measured_rows: number;
    compilable_rows: number;
    compilable_rate: number | null;
    byte_match_rows: number;
    byte_match_rate: number | null;
  };
  failures: Record<string, number>;
  cost: {
    basis: string;
    rows_with_time: number;
    total_ms: number;
    mean_ms: number | null;
    p50_ms: number | null;
    p95_ms: number | null;
    usd: number | null;
  };
  by_difficulty: Record<
    string,
    { rows: number; semantic_perfect: number; compilable: number }
  >;
};

export type MeasurementView = {
  scope: {
    rows: number;
    subjects: number;
    decompilers: number;
    difficulty: Record<string, number>;
  };
  by_decompiler: Record<string, MeasurementToolHealth>;
  pipeline: {
    source_cfg: {
      subjects: number;
      available: number;
      rate: number | null;
      by_basis: Record<string, number>;
    };
    decompiled_cfg: Record<
      string,
      { attempted: number; available: number; rate: number | null }
    >;
    oracle: { attempted: number; tested: number; no_wrapper: number };
  };
};

export type MeasurementHealth = {
  schema: "measurement-health-v1";
  ranking: false;
  default_preset: string;
  default_normalization: "shared" | "intersection";
  normalization_contract: Record<string, string>;
  difficulty_contract: string;
  cost_contract: string;
  presets: Array<{
    id: string;
    label: string;
    views: { shared: MeasurementView; intersection: MeasurementView };
  }>;
};

export function extractMeasurementHealth(
  data: BenchmarkEnvelope | null | undefined,
): MeasurementHealth | null {
  const health = data?.summary?.mvp?.measurement_health as
    | MeasurementHealth
    | undefined;
  return health?.schema === "measurement-health-v1" &&
    Array.isArray(health.presets)
    ? health
    : null;
}

export function extractQualityExtensions(
  data: BenchmarkEnvelope | null | undefined,
): QualityExtensions {
  const empty: QualityExtensions = {
    bareByDecompiler: {},
    recompilationByDecompiler: {},
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
  const recompilation =
    (extensions.recompilation as Record<string, unknown> | undefined) ||
    (diagnostics.recompilation as Record<string, unknown> | undefined) ||
    {};
  const tracks =
    (extensions.tracks as Record<string, unknown> | undefined) ||
    (diagnostics.tracks as Record<string, unknown> | undefined) ||
    {};
  return {
    bareByDecompiler: (bare.by_decompiler as QualityExtensions["bareByDecompiler"]) || {},
    recompilationByDecompiler:
      (recompilation.by_decompiler as QualityExtensions["recompilationByDecompiler"]) ||
      {},
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

async function loadFromFile(relPath: string): Promise<BenchmarkEnvelope | null> {
  try {
    const filePath = path.join(process.cwd(), relPath);
    const text = await readFile(filePath, "utf8");
    return tryParseEnvelope(JSON.parse(text));
  } catch {
    return null;
  }
}

function versionKey(version: string): [number, number, number] | null {
  const match = /^v?(\d+)\.(\d+)\.(\d+)$/.exec(version);
  return match
    ? [Number(match[1]), Number(match[2]), Number(match[3])]
    : null;
}

function compareReleaseVersions(a: string, b: string): number {
  const left = versionKey(a);
  const right = versionKey(b);
  if (!left || !right) return a.localeCompare(b);
  for (let index = 0; index < left.length; index += 1) {
    if (left[index] !== right[index]) return left[index] - right[index];
  }
  return 0;
}

function isReleaseArtifact(envelope: BenchmarkEnvelope): boolean {
  return (
    Boolean(envelope.toolchain?.fission_version) &&
    envelope.toolchain?.fission_source === "release" &&
    envelope.run?.legacy_source !== true
  );
}

function isCanonicalPublication(envelope: BenchmarkEnvelope): boolean {
  const releaseContract = envelope.run?.release_contract;
  // v0.1.8 was published before release_contract became a required runner
  // field.  Preserve that verified release artifact, but fail closed when a
  // newer envelope declares a different contract instead of silently treating
  // it as the canonical baseline.
  const hasCompatibleContract =
    releaseContract == null || releaseContract.id === "release-baseline-v1";
  return (
    isReleaseArtifact(envelope) &&
    hasCompatibleContract &&
    envelope.run?.official === true &&
    envelope.validity?.valid === true &&
    envelope.validity?.publishable === true
  );
}

function decompilerCount(envelope: BenchmarkEnvelope): number {
  return new Set(envelope.rows.map((row) => row.decompiler)).size;
}

function finishedAt(envelope: BenchmarkEnvelope): number {
  const timestamp = Date.parse(envelope.run?.finished_at ?? "");
  return Number.isFinite(timestamp) ? timestamp : 0;
}

/**
 * Select only artifacts anchored to the newest canonical Fission release.
 * This is intentionally fail-closed: dev_latest, legacy_source, local builds,
 * and older release data can never become the default dashboard dataset.
 */
export function selectLatestReleaseEnvelope(
  candidates: BenchmarkEnvelope[],
  options?: { requirePublishable?: boolean; allowUnanchoredDevelopment?: boolean },
): BenchmarkEnvelope | null {
  const canonical = candidates.filter(isCanonicalPublication);
  let latestVersion = canonical
    .map((envelope) => envelope.toolchain.fission_version!)
    .sort(compareReleaseVersions)
    .at(-1);

  if (!latestVersion && options?.allowUnanchoredDevelopment) {
    latestVersion = candidates
      .filter(isReleaseArtifact)
      .map((envelope) => envelope.toolchain.fission_version!)
      .sort(compareReleaseVersions)
      .at(-1);
  }
  if (!latestVersion) return null;

  const eligible = candidates.filter((envelope) => {
    if (!isReleaseArtifact(envelope)) return false;
    if (envelope.toolchain.fission_version !== latestVersion) return false;
    if (options?.requirePublishable && !isCanonicalPublication(envelope)) return false;
    return envelope.validity?.valid === true && envelope.rows.length > 0;
  });

  eligible.sort((a, b) => {
    // A diagnostic/smoke envelope must never shadow the canonical publication
    // for the same release.  This matters for extension metrics such as GED:
    // broad smoke matrices may contain more tools while carrying no GED rows.
    // Keep those envelopes only as a development/failure fallback, then prefer
    // matrix breadth and recency within the same publication class.
    const publication =
      Number(isCanonicalPublication(b)) - Number(isCanonicalPublication(a));
    if (publication !== 0) return publication;
    const tools = decompilerCount(b) - decompilerCount(a);
    if (tools !== 0) return tools;
    return finishedAt(b) - finishedAt(a);
  });
  return eligible[0] ?? null;
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

  const candidates: BenchmarkEnvelope[] = [];

  const [localPublic, localOfficial] = await Promise.all([
    loadFromFile("public/benchmark-latest.json"),
    loadFromFile("results/latest.json"),
  ]);
  if (localPublic) candidates.push(localPublic);
  if (localOfficial) candidates.push(localOfficial);

  // `next dev` locally: skip the network candidates entirely once a local
  // public/benchmark-latest.json parses. Otherwise the remote-published
  // envelope (scored higher whenever it's `publishable`) always wins the
  // ranking below regardless of what's on disk, making it impossible to
  // preview a fresh local runner output without pushing it to GitHub first.
  // Production/build (`next build` / `next start`, where NODE_ENV is
  // "production") is unaffected -- it always fetches, same as before.
  const skipNetwork = process.env.NODE_ENV === "development" && localPublic !== null;

  if (!skipNetwork) {
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
  }

  return selectLatestReleaseEnvelope(candidates, {
    requirePublishable,
    allowUnanchoredDevelopment: process.env.NODE_ENV === "development",
  });
}

export async function getLatestReleaseVersion(): Promise<string | null> {
  const envelope = await getLatestBenchmarkOptional({ requirePublishable: true });
  return envelope?.toolchain.fission_version ?? null;
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
            shared_rows?: number;
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
          type_match?: {
            mean_accuracy?: number | null;
            perfect_rows?: number;
            tested_rows?: number;
            shared_rows?: number;
            perfect_rate?: number | null;
          };
          ged?: {
            mean_ged?: number | null;
            perfect_rows?: number;
            tested_rows?: number;
            shared_rows?: number;
            perfect_rate?: number | null;
          };
        }
      >
    | undefined;

  if (fromSummary && Object.keys(fromSummary).length > 0) {
    const gedSharedRows = new Set(
      data.rows
        .filter((row) => row.ged_score !== null && row.ged_score !== undefined)
        .map((row) => `${row.function_name}\u0000${row.compiler_variant}`),
    ).size;
    const typeMatchSharedRows = new Set(
      data.rows
        .filter(
          (row) =>
            row.type_match_score !== null && row.type_match_score !== undefined,
        )
        .map((row) => `${row.function_name}\u0000${row.compiler_variant}`),
    ).size;
    return Object.entries(fromSummary)
      .map(([decompiler, s]) => {
        const resolvedTypeSharedRows =
          s.type_match?.shared_rows ?? typeMatchSharedRows;
        const typePerfectRows = s.type_match?.perfect_rows ?? 0;
        const resolvedGedSharedRows = s.ged?.shared_rows ?? gedSharedRows;
        const gedPerfectRows = s.ged?.perfect_rows ?? 0;
        return {
          decompiler,
          attempted: s.coverage?.attempted ?? 0,
          adapterClean: s.coverage?.adapter_clean ?? 0,
          invalidBoundary: s.coverage?.invalid_boundary ?? 0,
          semanticTested: s.coverage?.semantic_tested ?? s.semantic?.tested_rows ?? 0,
          semanticSharedRows: s.semantic?.shared_rows ?? s.semantic?.tested_rows ?? 0,
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
          meanTypeMatch:
            s.type_match?.mean_accuracy === undefined || s.type_match?.mean_accuracy === null
              ? null
              : Number(s.type_match.mean_accuracy),
          typeMatchTestedRows: s.type_match?.tested_rows ?? 0,
          typeMatchSharedRows: resolvedTypeSharedRows,
          typeMatchPerfectRows: typePerfectRows,
          typeMatchPerfectRate:
            s.type_match?.perfect_rate !== undefined &&
            s.type_match?.perfect_rate !== null
              ? Number(s.type_match.perfect_rate)
              : resolvedTypeSharedRows > 0
                ? typePerfectRows / resolvedTypeSharedRows
                : null,
          meanGed:
            s.ged?.mean_ged === undefined || s.ged?.mean_ged === null
              ? null
              : Number(s.ged.mean_ged),
          gedTestedRows: s.ged?.tested_rows ?? 0,
          gedSharedRows: resolvedGedSharedRows,
          gedPerfectRows,
          gedPerfectRate:
            s.ged?.perfect_rate !== undefined && s.ged?.perfect_rate !== null
              ? Number(s.ged.perfect_rate)
              : resolvedGedSharedRows > 0
                ? gedPerfectRows / resolvedGedSharedRows
                : null,
        };
      })
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
      typeMatchScores: number[];
      gedScores: number[];
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
        typeMatchScores: [],
        gedScores: [],
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
    if (row.type_match_score !== null && row.type_match_score !== undefined) {
      s.typeMatchScores.push(row.type_match_score);
    }
    if (row.ged_score !== null && row.ged_score !== undefined) {
      s.gedScores.push(row.ged_score);
    }
  }

  return Array.from(map.entries())
    .map(([decompiler, s]) => ({
      decompiler,
      attempted: s.attempted,
      adapterClean: s.adapterClean,
      invalidBoundary: s.invalidBoundary,
      semanticTested: s.semanticScores.length,
      semanticSharedRows: s.semanticScores.length,
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
      meanTypeMatch:
        s.typeMatchScores.length > 0
          ? s.typeMatchScores.reduce((a, b) => a + b, 0) / s.typeMatchScores.length
          : null,
      typeMatchTestedRows: s.typeMatchScores.length,
      typeMatchSharedRows: s.typeMatchScores.length,
      typeMatchPerfectRows: s.typeMatchScores.filter((v) => v >= 1).length,
      typeMatchPerfectRate:
        s.typeMatchScores.length > 0
          ? s.typeMatchScores.filter((v) => v >= 1).length / s.typeMatchScores.length
          : null,
      meanGed:
        s.gedScores.length > 0
          ? s.gedScores.reduce((a, b) => a + b, 0) / s.gedScores.length
          : null,
      gedTestedRows: s.gedScores.length,
      gedSharedRows: s.gedScores.length,
      gedPerfectRows: s.gedScores.filter((v) => v === 0).length,
      gedPerfectRate:
        s.gedScores.length > 0
          ? s.gedScores.filter((v) => v === 0).length / s.gedScores.length
          : null,
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
            shared_rows?: number;
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

export { pct, meanFmt } from "./format";

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
