import { readFile } from "fs/promises";
import path from "path";
import { BenchmarkEnvelopeSchema, type BenchmarkEnvelope, type Row } from "./schemas";
import {
  extractSpeedExtension,
  fissionVsGhidraPaired,
  pairSummary,
  speedByDecompiler,
  type SpeedMicrobenchDocument,
} from "./speed";

const REPO_RAW =
  "https://raw.githubusercontent.com/fission-systems/fission-benchmark/main";

const VERSION_RE = /^v?(\d+)\.(\d+)\.(\d+)$/;

/** Parses "v0.1.6" -> [0, 1, 6]; unparseable versions sort lowest. */
function versionKey(version: string): [number, number, number] {
  const m = VERSION_RE.exec(version);
  if (!m) return [-1, -1, -1];
  return [Number(m[1]), Number(m[2]), Number(m[3])];
}

function compareVersions(a: string, b: string): number {
  const ka = versionKey(a);
  const kb = versionKey(b);
  for (let i = 0; i < 3; i++) {
    if (ka[i] !== kb[i]) return ka[i] - kb[i];
  }
  return 0;
}

async function readLocalJson(relPath: string): Promise<unknown | null> {
  try {
    const filePath = path.join(process.cwd(), "public", relPath);
    return JSON.parse(await readFile(filePath, "utf8"));
  } catch {
    return null;
  }
}

async function fetchRemoteJson(relPath: string): Promise<unknown | null> {
  try {
    const res = await fetch(`${REPO_RAW}/public/${relPath}`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** Version-sorted list of archived releases (oldest first). */
export async function getHistoryIndex(): Promise<string[]> {
  const local = await readLocalJson("benchmark-history/index.json");
  const raw = local ?? (await fetchRemoteJson("benchmark-history/index.json"));
  if (!Array.isArray(raw)) return [];
  return [...(raw as string[])].sort(compareVersions);
}

export async function getArchivedEnvelope(
  version: string,
): Promise<BenchmarkEnvelope | null> {
  const relPath = `benchmark-history/${version}.json`;
  const raw = (await readLocalJson(relPath)) ?? (await fetchRemoteJson(relPath));
  if (!raw) return null;
  const parsed = BenchmarkEnvelopeSchema.safeParse(raw);
  return parsed.success ? parsed.data : null;
}

async function getArchivedSpeed(
  version: string,
): Promise<SpeedMicrobenchDocument | null> {
  const relPath = `speed-history/${version}.json`;
  const raw = (await readLocalJson(relPath)) ?? (await fetchRemoteJson(relPath));
  if (!raw || typeof raw !== "object") return null;
  const candidate = raw as SpeedMicrobenchDocument;
  if (!candidate.schema?.startsWith("speed-microbench-v")) return null;
  if (!candidate.by_decompiler || typeof candidate.by_decompiler !== "object") {
    return null;
  }
  return candidate;
}

async function getSpeedHistoryIndex(): Promise<Set<string>> {
  const raw = (await readLocalJson("speed-history/index.json"))
    ?? (await fetchRemoteJson("speed-history/index.json"));
  return new Set(Array.isArray(raw) ? raw.filter((value): value is string => typeof value === "string") : []);
}

/**
 * Per-decompiler stats restricted to the (function_name, compiler_variant)
 * pairs present in *both* envelopes. Two releases can measure very
 * different corpus sizes (an archived smoke run vs. a later full official
 * run) -- comparing each envelope's own full-population mean would silently
 * compare different populations. Everything here is scoped to the
 * intersection so "did this get better" is always apples-to-apples.
 */
export type MetricDelta = {
  decompiler: string;
  rowsCompared: number;
  previousMeanSemantic: number | null;
  currentMeanSemantic: number | null;
  meanSemanticDelta: number | null;
  previousPerfectRows: number;
  currentPerfectRows: number;
  perfectRowsDelta: number;
};

export type FunctionMovement = {
  functionName: string;
  compilerVariant: string;
  previousScore: number | null;
  currentScore: number | null;
};

export type ReleaseComparison = {
  currentVersion: string;
  previousVersion: string;
  currentRun: BenchmarkEnvelope["run"];
  previousRun: BenchmarkEnvelope["run"];
  deltas: MetricDelta[];
  fissionNewlyPassing: FunctionMovement[];
  fissionNewlyFailing: FunctionMovement[];
  fissionRowsCompared: number;
};

const PASS_THRESHOLD = 1;

function rowKey(row: Row): string {
  return `${row.function_name} ${row.compiler_variant}`;
}

function isPassing(score: number | null | undefined): boolean {
  return typeof score === "number" && score >= PASS_THRESHOLD;
}

function rowsByDecompilerAndKey(envelope: BenchmarkEnvelope): Map<string, Map<string, Row>> {
  const byDecompiler = new Map<string, Map<string, Row>>();
  for (const row of envelope.rows) {
    let byKey = byDecompiler.get(row.decompiler);
    if (!byKey) {
      byKey = new Map();
      byDecompiler.set(row.decompiler, byKey);
    }
    byKey.set(rowKey(row), row);
  }
  return byDecompiler;
}

/** Mean of non-null semantic_score across a set of rows (null = untested, excluded). */
function meanSemantic(rows: Row[]): number | null {
  const scored = rows
    .map((r) => r.semantic_score)
    .filter((s): s is number => typeof s === "number");
  if (scored.length === 0) return null;
  return scored.reduce((a, b) => a + b, 0) / scored.length;
}

function isCanonicalRelease(envelope: BenchmarkEnvelope): boolean {
  return (
    envelope.run?.official === true &&
    envelope.validity?.valid === true &&
    envelope.validity?.publishable === true
  );
}

function measurementContract(envelope: BenchmarkEnvelope): string {
  return JSON.stringify({
    corpus: envelope.run?.corpus ?? null,
    profile: envelope.run?.profile ?? null,
    oracleMode: envelope.oracle?.mode ?? null,
    oracleSubject: envelope.oracle?.oracle_subject ?? null,
    targetAbi: envelope.oracle?.target_abi ?? null,
  });
}

function trendContract(envelope: BenchmarkEnvelope): string {
  const fissionCells = envelope.rows
    .filter((row) => row.decompiler === "fission")
    .map(rowKey)
    .sort();
  return JSON.stringify({
    measurement: measurementContract(envelope),
    fissionCells,
  });
}

/**
 * Per-decompiler delta computed only over (function_name, compiler_variant)
 * pairs present in both envelopes -- see MetricDelta's doc comment for why.
 */
function computeMetricDeltas(
  previous: BenchmarkEnvelope,
  current: BenchmarkEnvelope,
): MetricDelta[] {
  const prevByDecompiler = rowsByDecompilerAndKey(previous);
  const curByDecompiler = rowsByDecompilerAndKey(current);
  const decompilers = new Set([...prevByDecompiler.keys(), ...curByDecompiler.keys()]);

  const deltas: MetricDelta[] = [];
  for (const decompiler of decompilers) {
    const prevByKey = prevByDecompiler.get(decompiler);
    const curByKey = curByDecompiler.get(decompiler);
    if (!prevByKey || !curByKey) continue;

    const sharedKeys = [...prevByKey.keys()].filter((k) => curByKey.has(k));
    if (sharedKeys.length === 0) continue;

    const prevRows = sharedKeys.map((k) => prevByKey.get(k)!);
    const curRows = sharedKeys.map((k) => curByKey.get(k)!);
    const prevMean = meanSemantic(prevRows);
    const curMean = meanSemantic(curRows);
    const prevPerfect = prevRows.filter((r) => isPassing(r.semantic_score)).length;
    const curPerfect = curRows.filter((r) => isPassing(r.semantic_score)).length;

    deltas.push({
      decompiler,
      rowsCompared: sharedKeys.length,
      previousMeanSemantic: prevMean,
      currentMeanSemantic: curMean,
      meanSemanticDelta: prevMean !== null && curMean !== null ? curMean - prevMean : null,
      previousPerfectRows: prevPerfect,
      currentPerfectRows: curPerfect,
      perfectRowsDelta: curPerfect - prevPerfect,
    });
  }

  return deltas.sort((a, b) => {
    if (a.decompiler === "fission") return -1;
    if (b.decompiler === "fission") return 1;
    return b.rowsCompared - a.rowsCompared;
  });
}

function diffFissionRows(
  previous: BenchmarkEnvelope,
  current: BenchmarkEnvelope,
): {
  newlyPassing: FunctionMovement[];
  newlyFailing: FunctionMovement[];
  compared: number;
} {
  const prevByKey = new Map<string, Row>();
  for (const row of previous.rows) {
    if (row.decompiler === "fission") prevByKey.set(rowKey(row), row);
  }

  const newlyPassing: FunctionMovement[] = [];
  const newlyFailing: FunctionMovement[] = [];
  let compared = 0;

  for (const row of current.rows) {
    if (row.decompiler !== "fission") continue;
    const prevRow = prevByKey.get(rowKey(row));
    if (!prevRow) continue;
    compared += 1;
    const wasPassing = isPassing(prevRow.semantic_score);
    const nowPassing = isPassing(row.semantic_score);
    if (wasPassing === nowPassing) continue;
    const movement: FunctionMovement = {
      functionName: row.function_name,
      compilerVariant: row.compiler_variant,
      previousScore: prevRow.semantic_score,
      currentScore: row.semantic_score,
    };
    if (nowPassing) newlyPassing.push(movement);
    else newlyFailing.push(movement);
  }

  return { newlyPassing, newlyFailing, compared };
}

/**
 * Compares the currently-displayed envelope against the most recent
 * *older* archived release. Returns null when there's nothing to compare
 * against yet (first release, or history isn't archived).
 */
export async function getReleaseComparison(
  current: BenchmarkEnvelope,
): Promise<ReleaseComparison | null> {
  if (!isCanonicalRelease(current)) return null;
  const currentVersion = current.toolchain?.fission_version;
  if (!currentVersion) return null;

  const index = await getHistoryIndex();
  const older = index.filter((v) => compareVersions(v, currentVersion) < 0);
  if (older.length === 0) return null;
  let previousVersion: string | null = null;
  let previous: BenchmarkEnvelope | null = null;
  for (const version of [...older].reverse()) {
    const candidate = await getArchivedEnvelope(version);
    if (
      candidate &&
      isCanonicalRelease(candidate) &&
      measurementContract(candidate) === measurementContract(current)
    ) {
      previousVersion = version;
      previous = candidate;
      break;
    }
  }
  if (!previousVersion || !previous) return null;

  const deltas = computeMetricDeltas(previous, current);
  const { newlyPassing, newlyFailing, compared } = diffFissionRows(previous, current);

  return {
    currentVersion,
    previousVersion,
    currentRun: current.run,
    previousRun: previous.run,
    deltas,
    fissionNewlyPassing: newlyPassing,
    fissionNewlyFailing: newlyFailing,
    fissionRowsCompared: compared,
  };
}

/**
 * One audit point per archived version, oldest first. Canonical trend points
 * are selected separately: they must be official, valid, publishable, and
 * share both the benchmark contract and exact Fission cell matrix with the
 * latest canonical release. Comparable diagnostics remain available to the UI
 * as explicitly dashed engineering history, never as an official series.
 */
export type VersionTrendPoint = {
  version: string;
  meanSemantic: number | null;
  perfectRows: number;
  totalRows: number;
  finishedAt: string | null;
  official: boolean;
  publishable: boolean;
  canonical: boolean;
  trendEligible: boolean;
  semanticTestedRows: number;
  profile: string | null;
  corpus: string | null;
  runId: string | null;
  contractKey: string;
  latencyMeanMs: number | null;
  latencyP50Ms: number | null;
  latencyP95Ms: number | null;
  pairedRows: number;
  medianSpeedup: number | null;
  geometricMeanSpeedup: number | null;
  fissionFasterShare: number | null;
  coldMeanMs: number | null;
  coldP50Ms: number | null;
  warmMeanMs: number | null;
  warmP50Ms: number | null;
  meanCpuPercent: number | null;
  peakCpuPercent: number | null;
  peakMemoryBytes: number | null;
  peakMemoryPercent: number | null;
  resourceSamples: number;
  speedRunId: string | null;
};

export async function getVersionTrend(): Promise<VersionTrendPoint[]> {
  const index = await getHistoryIndex();
  const speedHistory = await getSpeedHistoryIndex();
  const points: VersionTrendPoint[] = [];
  for (const version of index) {
    const envelope = await getArchivedEnvelope(version);
    if (!envelope) continue;
    const fissionRows = envelope.rows.filter((r) => r.decompiler === "fission");
    const canonical = isCanonicalRelease(envelope);
    const fissionSpeed = speedByDecompiler(envelope).find(
      (item) => item.decompiler === "fission",
    );
    const paired = pairSummary(fissionVsGhidraPaired(envelope));
    const embeddedSpeed = extractSpeedExtension(envelope)?.microbench ?? null;
    const speedDocument = (speedHistory.has(version) ? await getArchivedSpeed(version) : null)
      ?? embeddedSpeed;
    const micro = speedDocument?.by_decompiler?.fission;
    const resources = micro?.resources?.all;
    points.push({
      version,
      meanSemantic: meanSemantic(fissionRows),
      perfectRows: fissionRows.filter((r) => isPassing(r.semantic_score)).length,
      totalRows: fissionRows.length,
      finishedAt: envelope.run?.finished_at ?? null,
      official: envelope.run?.official === true,
      publishable: envelope.validity?.publishable === true,
      canonical,
      trendEligible: false,
      semanticTestedRows: fissionRows.filter(
        (row) => typeof row.semantic_score === "number",
      ).length,
      profile: envelope.run?.profile ?? null,
      corpus: envelope.run?.corpus ?? null,
      runId: envelope.run?.run_id ?? null,
      contractKey: trendContract(envelope),
      latencyMeanMs: fissionSpeed?.mean ?? null,
      latencyP50Ms: fissionSpeed?.p50 ?? null,
      latencyP95Ms: fissionSpeed?.p95 ?? null,
      pairedRows: paired.n,
      medianSpeedup: paired.medianSpeedup,
      geometricMeanSpeedup: paired.geometricMeanSpeedup,
      fissionFasterShare: paired.fissionFasterShare,
      coldMeanMs: micro?.cold?.mean_ms ?? null,
      coldP50Ms: micro?.cold?.p50_ms ?? null,
      warmMeanMs: micro?.warm?.mean_ms ?? null,
      warmP50Ms: micro?.warm?.p50_ms ?? null,
      meanCpuPercent: resources?.mean_cpu_percent ?? null,
      peakCpuPercent: resources?.peak_cpu_percent ?? null,
      peakMemoryBytes: resources?.peak_memory_bytes ?? null,
      peakMemoryPercent: resources?.peak_memory_percent ?? null,
      resourceSamples: resources?.samples ?? 0,
      speedRunId: speedDocument?.run_id ?? null,
    });
  }
  const latestCanonical = [...points].reverse().find((point) => point.canonical);
  if (latestCanonical) {
    for (const point of points) {
      point.trendEligible =
        point.canonical && point.contractKey === latestCanonical.contractKey;
    }
  }
  return points;
}
