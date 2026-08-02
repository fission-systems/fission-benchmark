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
};

const LOCAL_URL =
  process.env.PARITY_TELEMETRY_URL ?? "/parity-telemetry.json";

const REMOTE_FALLBACK =
  process.env.PARITY_TELEMETRY_REMOTE_URL ??
  "https://raw.githubusercontent.com/fission-systems/fission-benchmark/main/results/telemetry/latest.json";

export async function getParityTelemetry(): Promise<ParityTelemetry | null> {
  for (const url of [LOCAL_URL, REMOTE_FALLBACK]) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) continue;
      const data = (await res.json()) as ParityTelemetry;
      if (typeof data.total_rows === "number") return data;
    } catch {
      // try next source
    }
  }
  return null;
}
