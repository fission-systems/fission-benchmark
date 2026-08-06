import { readFile } from "fs/promises";
import path from "path";
import { z } from "zod";

const REPO_RAW =
  "https://raw.githubusercontent.com/fission-systems/fission-benchmark/main/public";

const MetricSchema = z.object({
  tested_rows: z.number().int().nonnegative(),
  mean: z.number().nullable(),
  perfect_rows: z.number().int().nonnegative(),
  perfect_rate: z.number().nullable(),
});

const ToolSummarySchema = z.object({
  attempted_rows: z.number().int().nonnegative(),
  clean_rows: z.number().int().nonnegative(),
  clean_rate: z.number(),
  latency_ms: z.object({
    measured_rows: z.number().int().nonnegative(),
    mean: z.number().nullable(),
    p50: z.number().nullable(),
    p95: z.number().nullable(),
    total: z.number(),
  }),
  ged: MetricSchema,
  type_match: MetricSchema,
  recompilation: MetricSchema,
  failures: z.record(z.string(), z.number().int().nonnegative()),
});

export const UnofficialCorpusSchema = z.object({
  schema: z.literal("fission-unofficial-corpus-v1"),
  ranking: z.literal(false),
  publication: z.object({
    published_at: z.string(),
    source_asset: z.string(),
    source_sha256: z.string().regex(/^[0-9a-f]{64}$/),
  }),
  run: z.object({
    run_id: z.string(),
    started_at: z.string(),
    finished_at: z.string(),
    duration_ms: z.number().nullable().optional(),
    runner_commit: z.string(),
    matrix_profile: z.literal("decbench_scale_full"),
    fission_version: z.string(),
  }),
  toolchain: z.object({
    fission_source: z.literal("release"),
    fission_git_sha: z.string().nullable().optional(),
    host: z.record(z.string(), z.unknown()),
  }),
  corpus: z.object({
    schema: z.string(),
    name: z.literal("decbench"),
    repository: z.string(),
    revision: z.string().regex(/^[0-9a-f]{40}$/),
    license: z.string(),
    config: z.string(),
    selected_binaries: z.number().int().positive(),
    requested_functions: z.number().int().positive(),
    resolved_functions: z.number().int().positive(),
    source_cfg_functions: z.number().int().positive(),
    source_cfg_coverage: z.number(),
    malware_included: z.literal(false),
  }),
  matrix: z.object({
    subjects: z.number().int().positive(),
    expected_rows: z.number().int().positive(),
    observed_rows: z.number().int().positive(),
    completion_rate: z.number(),
    decompilers: z.array(z.string()),
  }),
  by_decompiler: z.record(z.string(), ToolSummarySchema),
  projects: z.array(
    z.object({
      project: z.string(),
      subjects: z.number().int().nonnegative(),
      rows: z.number().int().nonnegative(),
      clean_rows: z.number().int().nonnegative(),
      clean_rate: z.number(),
    }),
  ),
});

const HistoryIndexSchema = z.object({
  schema: z.literal("fission-unofficial-corpus-index-v1"),
  entries: z.array(
    z.object({
      version: z.string(),
      run_id: z.string(),
      finished_at: z.string(),
      path: z.string(),
      subjects: z.number().int().nonnegative(),
      rows: z.number().int().nonnegative(),
      source_sha256: z.string(),
    }),
  ),
});

export type UnofficialCorpusDocument = z.infer<typeof UnofficialCorpusSchema>;
export type UnofficialCorpusHistory = z.infer<typeof HistoryIndexSchema>["entries"];

async function localJson(relative: string): Promise<unknown | null> {
  try {
    return JSON.parse(
      await readFile(path.join(process.cwd(), "public", relative), "utf8"),
    );
  } catch {
    return null;
  }
}

async function remoteJson(relative: string): Promise<unknown | null> {
  try {
    const response = await fetch(`${REPO_RAW}/${relative}`, { cache: "no-store" });
    return response.ok ? await response.json() : null;
  } catch {
    return null;
  }
}

export async function getLatestUnofficialCorpus(): Promise<UnofficialCorpusDocument | null> {
  const local = await localJson("unofficial-corpus-latest.json");
  if (local) {
    const parsed = UnofficialCorpusSchema.safeParse(local);
    if (parsed.success) return parsed.data;
  }
  const remote = await remoteJson("unofficial-corpus-latest.json");
  const parsed = UnofficialCorpusSchema.safeParse(remote);
  return parsed.success ? parsed.data : null;
}

export async function getUnofficialCorpusHistory(): Promise<UnofficialCorpusHistory> {
  const local = await localJson("unofficial-corpus-history/index.json");
  const raw = local ?? (await remoteJson("unofficial-corpus-history/index.json"));
  const parsed = HistoryIndexSchema.safeParse(raw);
  return parsed.success ? [...parsed.data.entries].reverse() : [];
}
