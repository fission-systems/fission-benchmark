/**
 * Decompiler speed diagnostics from envelope rows and optional
 * summary.extensions.speed (row aggregate + microbench cold/warm).
 *
 * Metric: row.time_ms — adapter decompile wall time (not semantic/oracle).
 * Non-ranking: never mix into semantic MVP ranking.
 */
import type { BenchmarkEnvelope } from "./schemas";

export type ResourceStats = {
  n_trials?: number;
  samples?: number;
  mean_cpu_percent?: number | null;
  peak_cpu_percent?: number | null;
  mean_peak_memory_bytes?: number | null;
  peak_memory_bytes?: number | null;
  peak_memory_percent?: number | null;
};

export type SpeedMicrobenchDocument = {
  schema?: string;
  run_id?: string;
  started_at?: string;
  finished_at?: string;
  toolchain?: {
    fission_version?: string | null;
    runner_commit?: string | null;
    github_run_id?: string | null;
  };
  by_decompiler?: Record<
    string,
    {
      cold?: { n?: number; mean_ms?: number | null; p50_ms?: number | null };
      warm?: { n?: number; mean_ms?: number | null; p50_ms?: number | null };
      all?: { n?: number; mean_ms?: number | null };
      resources?: {
        collector?: string;
        scope?: string;
        cold?: ResourceStats;
        warm?: ResourceStats;
        all?: ResourceStats;
      };
    }
  >;
  config?: Record<string, unknown>;
  notes?: string;
};

export type SpeedExtension = {
  schema?: string;
  ranking?: boolean;
  note?: string;
  from_rows?: {
    by_decompiler?: Record<
      string,
      {
        n?: number;
        mean_ms?: number | null;
        p50_ms?: number | null;
        p95_ms?: number | null;
        min_ms?: number | null;
        max_ms?: number | null;
        sum_ms?: number | null;
      }
    >;
    fission_vs_ghidra?: {
      paired_n?: number;
      median_speedup?: number | null;
      geometric_mean_speedup?: number | null;
      fission_faster_share?: number | null;
    };
  };
  microbench?: SpeedMicrobenchDocument | null;
};

export function extractSpeedExtension(
  data: BenchmarkEnvelope,
): SpeedExtension | null {
  const summary = (data as { summary?: { extensions?: { speed?: unknown } } })
    .summary;
  const speed = summary?.extensions?.speed;
  if (!speed || typeof speed !== "object") return null;
  return speed as SpeedExtension;
}

export type TimingStats = {
  n: number;
  mean: number | null;
  p50: number | null;
  p95: number | null;
  min: number | null;
  max: number | null;
  sum: number;
};

export type DecompilerSpeedRow = TimingStats & {
  decompiler: string;
  timedRows: number;
  zeroOrMissing: number;
};

export type PairedSpeedRow = {
  function_name: string;
  compiler_variant: string;
  fission_ms: number;
  ghidra_ms: number;
  /** ghidra_ms / fission_ms — >1 means fission faster */
  speedup: number | null;
};

export type FunctionSpeedRow = {
  function_name: string;
  n: number;
  mean_ms: number;
  p95_ms: number;
  max_ms: number;
};

export type PivotSpeedRow = {
  key: string;
  n: number;
  mean_ms: number;
  p50_ms: number;
};

function percentile(sorted: number[], p: number): number | null {
  if (sorted.length === 0) return null;
  if (sorted.length === 1) return sorted[0];
  const idx = (sorted.length - 1) * p;
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo];
  const w = idx - lo;
  return sorted[lo] * (1 - w) + sorted[hi] * w;
}

export function computeTimingStats(times: number[]): TimingStats {
  const clean = times.filter((t) => Number.isFinite(t) && t > 0);
  if (clean.length === 0) {
    return { n: 0, mean: null, p50: null, p95: null, min: null, max: null, sum: 0 };
  }
  const sorted = [...clean].sort((a, b) => a - b);
  const sum = clean.reduce((a, b) => a + b, 0);
  return {
    n: clean.length,
    mean: sum / clean.length,
    p50: percentile(sorted, 0.5),
    p95: percentile(sorted, 0.95),
    min: sorted[0],
    max: sorted[sorted.length - 1],
    sum,
  };
}

function isTimedRow(row: BenchmarkEnvelope["rows"][number]): boolean {
  return typeof row.time_ms === "number" && row.time_ms > 0 && !row.error;
}

export function speedByDecompiler(
  data: BenchmarkEnvelope,
): DecompilerSpeedRow[] {
  const map = new Map<string, { times: number[]; total: number; zero: number }>();
  for (const row of data.rows) {
    const d = row.decompiler;
    if (!map.has(d)) map.set(d, { times: [], total: 0, zero: 0 });
    const s = map.get(d)!;
    s.total++;
    if (isTimedRow(row)) s.times.push(row.time_ms);
    else s.zero++;
  }
  return Array.from(map.entries())
    .map(([decompiler, s]) => {
      const stats = computeTimingStats(s.times);
      return {
        decompiler,
        timedRows: s.times.length,
        zeroOrMissing: s.zero,
        ...stats,
      };
    })
    .sort((a, b) => {
      if (a.decompiler === "fission") return -1;
      if (b.decompiler === "fission") return 1;
      if (a.decompiler === "ghidra") return -1;
      if (b.decompiler === "ghidra") return 1;
      return (a.mean ?? 1e12) - (b.mean ?? 1e12);
    });
}

/** Same function × variant cells present for both fission and ghidra with times. */
export function fissionVsGhidraPaired(
  data: BenchmarkEnvelope,
): PairedSpeedRow[] {
  type Cell = { fission?: number; ghidra?: number };
  const cells = new Map<string, Cell>();
  for (const row of data.rows) {
    if (!isTimedRow(row)) continue;
    if (row.decompiler !== "fission" && row.decompiler !== "ghidra") continue;
    const key = `${row.function_name}\0${row.compiler_variant}`;
    if (!cells.has(key)) cells.set(key, {});
    const c = cells.get(key)!;
    if (row.decompiler === "fission") c.fission = row.time_ms;
    else c.ghidra = row.time_ms;
  }
  const out: PairedSpeedRow[] = [];
  for (const [key, c] of cells) {
    if (c.fission == null || c.ghidra == null) continue;
    const [function_name, compiler_variant] = key.split("\0");
    out.push({
      function_name,
      compiler_variant,
      fission_ms: c.fission,
      ghidra_ms: c.ghidra,
      speedup: c.fission > 0 ? c.ghidra / c.fission : null,
    });
  }
  out.sort((a, b) => b.fission_ms - a.fission_ms);
  return out;
}

export function fissionSlowestFunctions(
  data: BenchmarkEnvelope,
  limit = 25,
): FunctionSpeedRow[] {
  const map = new Map<string, number[]>();
  for (const row of data.rows) {
    if (row.decompiler !== "fission" || !isTimedRow(row)) continue;
    const list = map.get(row.function_name) ?? [];
    list.push(row.time_ms);
    map.set(row.function_name, list);
  }
  return Array.from(map.entries())
    .map(([function_name, times]) => {
      const stats = computeTimingStats(times);
      return {
        function_name,
        n: stats.n,
        mean_ms: stats.mean ?? 0,
        p95_ms: stats.p95 ?? 0,
        max_ms: stats.max ?? 0,
      };
    })
    .sort((a, b) => b.mean_ms - a.mean_ms)
    .slice(0, limit);
}

/** Pivot Fission times by compiler_variant (e.g. "gcc -O0"). */
export function fissionByVariant(data: BenchmarkEnvelope): PivotSpeedRow[] {
  const map = new Map<string, number[]>();
  for (const row of data.rows) {
    if (row.decompiler !== "fission" || !isTimedRow(row)) continue;
    const list = map.get(row.compiler_variant) ?? [];
    list.push(row.time_ms);
    map.set(row.compiler_variant, list);
  }
  return Array.from(map.entries())
    .map(([key, times]) => {
      const stats = computeTimingStats(times);
      return {
        key,
        n: stats.n,
        mean_ms: stats.mean ?? 0,
        p50_ms: stats.p50 ?? 0,
      };
    })
    .sort((a, b) => b.mean_ms - a.mean_ms);
}

export function pairSummary(pairs: PairedSpeedRow[]): {
  n: number;
  meanFission: number | null;
  meanGhidra: number | null;
  medianSpeedup: number | null;
  geometricMeanSpeedup: number | null;
  fissionFasterShare: number | null;
} {
  if (pairs.length === 0) {
    return {
      n: 0,
      meanFission: null,
      meanGhidra: null,
      medianSpeedup: null,
      geometricMeanSpeedup: null,
      fissionFasterShare: null,
    };
  }
  const fSum = pairs.reduce((a, p) => a + p.fission_ms, 0);
  const gSum = pairs.reduce((a, p) => a + p.ghidra_ms, 0);
  const speedups = pairs
    .map((p) => p.speedup)
    .filter((s): s is number => s != null && s > 0)
    .sort((a, b) => a - b);
  const faster = pairs.filter((p) => p.fission_ms < p.ghidra_ms).length;
  let geo: number | null = null;
  if (speedups.length > 0) {
    const logSum = speedups.reduce((a, s) => a + Math.log(s), 0);
    geo = Math.exp(logSum / speedups.length);
  }
  return {
    n: pairs.length,
    meanFission: fSum / pairs.length,
    meanGhidra: gSum / pairs.length,
    medianSpeedup: percentile(speedups, 0.5),
    geometricMeanSpeedup: geo,
    fissionFasterShare: faster / pairs.length,
  };
}
