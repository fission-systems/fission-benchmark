import { readFile } from "fs/promises";
import path from "path";
import { getLatestReleaseVersion } from "./benchmark";

export type ParityStageDetail = {
  total: number;
  match: number;
  mismatch: number;
  error_or_other: number;
  match_rate: number | null;
  mismatch_rate: number | null;
  match_rate_attempted?: number | null;
  usable_coverage?: number | null;
  skipped?: number;
  fetch_error?: number;
  primary_quality?: boolean;
  reliability_note?: string;
  dual?: ParityPcodeDual;
  by_status: Record<string, number>;
  by_mismatch_kind: Record<string, number>;
  /** opt_cliff: per-opt correctness means keyed by candidate then opt level */
  by_candidate?: Record<string, Record<string, { n: number; mean_correctness: number }>>;
  /** throughput: per-candidate timing summary */
  throughput_by_candidate?: Record<string, { mean_ms: number; p50_ms?: number; p95_ms?: number; n: number }>;
};

export type ParityReliability = {
  usable_coverage?: number | null;
  match_rate_comparable?: number | null;
  match_rate_attempted?: number | null;
  fetch_error_rate?: number | null;
  skipped_rate?: number | null;
};

export type ParityPcodeDual = {
  n?: number;
  opcode_sequence_match_rate?: number | null;
  loose_full_match_rate?: number | null;
  strict_full_match_rate?: number | null;
  literal_full_match_rate?: number | null;
  // CFG dual (reuses same bag on stage.dual)
  mean_block_start_jaccard?: number | null;
  mean_edge_pair_jaccard?: number | null;
  // Function discovery dual
  mean_presence_recall?: number | null;
  mean_manifest_recall?: number | null;
  note?: string;
};

export type ParityPublishable = {
  stages?: Record<string, ParityStageDetail>;
  total_rows?: number;
  match?: number;
  mismatch?: number;
  match_rate_comparable?: number | null;
  usable_coverage?: number | null;
  definition?: string;
  pcode_dual?: ParityPcodeDual | null;
};

export type ParityTelemetry = {
  schema?: string;
  total_rows: number;
  by_stage: Record<string, number>;
  by_status: Record<string, number>;
  by_mismatch_kind: Record<string, number>;
  by_variant?: Record<string, number>;
  by_pair?: Record<string, number>;
  stages?: Record<string, ParityStageDetail>;
  sources?: string[];
  reliability?: ParityReliability;
  reliability_critique?: { warnings?: string[]; headline_stages?: string[] };
  canonicalize_mode?: string;
  non_publishable_stages?: string[];
  primary_quality_stages?: string[];
  publishable?: ParityPublishable;
  provenance?: ParityProvenance;
};

export type ParitySourceDetail = {
  path: string;
  stage?: string;
  rows: number;
  bytes?: number;
  sha256?: string;
  modified_at?: string;
};

export type ParityProvenance = {
  generated_at?: string;
  runner_commit?: string | null;
  github_run_id?: string | null;
  github_run_attempt?: string | null;
  corpus?: string | null;
  decompilers?: string | null;
  tool_versions?: Record<string, string | null | undefined>;
  oldest_source_at?: string | null;
  newest_source_at?: string | null;
  sources?: ParitySourceDetail[];
};

export type ParityFreshness = "fresh" | "aging" | "stale" | "unknown";

export type LoadedParityTelemetry = {
  telemetry: ParityTelemetry;
  source: string;
  generatedAt: string | null;
  measuredAt: string | null;
  ageHours: number | null;
  freshness: ParityFreshness;
};

const LOCAL_URL =
  process.env.PARITY_TELEMETRY_URL ?? "/parity-telemetry.json";

const REMOTE_FALLBACK =
  process.env.PARITY_TELEMETRY_REMOTE_URL ??
  "https://raw.githubusercontent.com/fission-systems/fission-benchmark/main/results/telemetry/latest.json";

export function classifyParityFreshness(
  measuredAt: string | null | undefined,
  nowMs = Date.now(),
): Pick<LoadedParityTelemetry, "ageHours" | "freshness"> {
  if (!measuredAt) {
    return { ageHours: null, freshness: "unknown" };
  }
  const generatedMs = Date.parse(measuredAt);
  if (!Number.isFinite(generatedMs)) {
    return { ageHours: null, freshness: "unknown" };
  }
  const ageHours = Math.max(0, (nowMs - generatedMs) / 3_600_000);
  const staleAfter = Number(process.env.PARITY_STALE_AFTER_HOURS ?? 72);
  const agingAfter = Number(process.env.PARITY_AGING_AFTER_HOURS ?? 24);
  const freshness: ParityFreshness =
    ageHours > staleAfter ? "stale" : ageHours > agingAfter ? "aging" : "fresh";
  return { ageHours, freshness };
}

function loadedState(telemetry: ParityTelemetry, source: string): LoadedParityTelemetry {
  const generatedAt = telemetry.provenance?.generated_at ?? null;
  const sourceTimes = (telemetry.provenance?.sources ?? [])
    .map((item) => item.modified_at)
    .filter(
      (value): value is string =>
        typeof value === "string" && Number.isFinite(Date.parse(value)),
    );
  const measuredAt = sourceTimes.length > 0
    ? sourceTimes.sort((a, b) => Date.parse(a) - Date.parse(b))[0]
    : generatedAt;
  return {
    telemetry,
    source,
    generatedAt,
    measuredAt,
    ...classifyParityFreshness(measuredAt),
  };
}

export async function getParityTelemetryState(): Promise<LoadedParityTelemetry | null> {
  const latestRelease = await getLatestReleaseVersion();
  if (!latestRelease) return null;
  const candidates: LoadedParityTelemetry[] = [];

  const addCandidate = (data: ParityTelemetry, source: string) => {
    const measuredRelease = data.provenance?.tool_versions?.fission;
    if (measuredRelease !== latestRelease) return;
    candidates.push(loadedState(data, source));
  };

  // Server Components cannot reliably fetch a same-origin relative URL.
  // Read the dashboard artifact directly so a fresh local/CI copy does not
  // silently lose to an older GitHub fallback.
  try {
    const localPath = path.join(process.cwd(), "public", "parity-telemetry.json");
    const data = JSON.parse(await readFile(localPath, "utf8")) as ParityTelemetry;
    if (typeof data.total_rows === "number") {
      addCandidate(data, "public/parity-telemetry.json");
    }
  } catch {
    // Network sources remain available below.
  }

  const urls = LOCAL_URL.startsWith("http")
    ? [LOCAL_URL, REMOTE_FALLBACK]
    : [REMOTE_FALLBACK];
  for (const url of urls) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) continue;
      const data = (await res.json()) as ParityTelemetry;
      if (typeof data.total_rows !== "number") continue;
      addCandidate(data, url);
    } catch {
      // try next source
    }
  }
  if (candidates.length === 0) return null;
  candidates.sort((a, b) => {
    if (a.generatedAt && b.generatedAt) {
      return Date.parse(b.generatedAt) - Date.parse(a.generatedAt);
    }
    if (a.generatedAt) return -1;
    if (b.generatedAt) return 1;
    return 0;
  });
  return candidates[0];
}

export async function getParityTelemetry(): Promise<ParityTelemetry | null> {
  return (await getParityTelemetryState())?.telemetry ?? null;
}
