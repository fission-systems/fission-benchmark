import { Suspense } from "react";
import Link from "next/link";
import {
  getLatestBenchmarkOptional,
  groupByDecompiler,
  filterCorePairStats,
  getSameFunctionSummary,
  pct,
} from "@/lib/benchmark";
import {
  getParityTelemetryState,
  type ParityTelemetry,
} from "@/lib/parity";
import { SiteChrome } from "@/components/SiteChrome";
import { CorePairPanel } from "@/components/CorePairPanel";
import { DualMetricsTiles } from "@/components/DualMetricsTiles";
import { ParityStageTable } from "@/components/ParityStageTable";
import { ParityDataStatus } from "@/components/ParityDataStatus";
import { SameFunctionPanel } from "@/components/SameFunctionPanel";
import styles from "../dashboard.module.css";

export const revalidate = 900;

export const metadata = {
  title: "Fission ↔ Ghidra · Layered parity",
  description:
    "Shared p-code-class IR comparison: assembly, p-code dual metrics, CFG, and function discovery with Ghidra as reference — not multi-decompiler ranking.",
};

function DualSection({ telemetry }: { telemetry: ParityTelemetry | null }) {
  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>Dual metrics at a glance</h2>
      <p className={styles.sectionLead}>
        Prefer dual rates for triage. Strict set / full equality is intentionally
        hard (CRT, space IDs, inventory heuristics).
      </p>
      <DualMetricsTiles telemetry={telemetry} />
    </section>
  );
}

function StageTableSection({ telemetry }: { telemetry: ParityTelemetry | null }) {
  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>Layer stack · full telemetry</h2>
      <p className={styles.sectionLead}>
        Primary publishable stages: assembly · p-code · CFG · function discovery.
        Decode / extension tracks are listed but not headline quality.
      </p>
      <ParityStageTable telemetry={telemetry} />
    </section>
  );
}

function OptCliffSection({ telemetry }: { telemetry: ParityTelemetry | null }) {
  const oc = telemetry?.stages?.opt_cliff;
  const byCand = oc?.by_candidate as Record<
    string,
    Record<string, { n: number; mean_correctness: number }>
  > | undefined;
  if (!byCand || Object.keys(byCand).length === 0) return null;

  const candidates = Object.keys(byCand).sort((a, b) =>
    a === "fission" ? -1 : b === "fission" ? 1 : a.localeCompare(b)
  );
  const opts = [...new Set(Object.values(byCand).flatMap((o) => Object.keys(o)))].sort();

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>Opt cliff · correctness by optimization level</h2>
      <p className={styles.sectionLead}>
        Mean correctness (oracle pass rate) per candidate × optimization level.
        Higher = fewer regressions at aggressive optimization.
      </p>
      <table className={styles.table ?? ""}>
        <thead>
          <tr>
            <th>Candidate</th>
            {opts.map((o) => (
              <th key={o} className={styles.num ?? ""}><code>{o}</code></th>
            ))}
            <th className={styles.num ?? ""}>Δ (O2−O0)</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((cand) => {
            const byOpt = byCand[cand] ?? {};
            const o0 = byOpt["O0"]?.mean_correctness ?? null;
            const o2 = byOpt["O2"]?.mean_correctness ?? null;
            const delta = o0 != null && o2 != null ? o2 - o0 : null;
            return (
              <tr key={cand} className={cand === "fission" ? styles.fissionRow ?? "" : ""}>
                <td><strong style={{ color: cand === "fission" ? "#6366f1" : cand === "ghidra" ? "#10b981" : undefined }}>{cand}</strong></td>
                {opts.map((o) => {
                  const v = byOpt[o]?.mean_correctness;
                  return (
                    <td key={o} className={styles.num ?? ""}>
                      {v != null ? `${(v * 100).toFixed(1)}%` : "—"}
                    </td>
                  );
                })}
                <td className={styles.num ?? ""} style={{ color: delta != null && delta >= 0 ? "#10b981" : "#f87171" }}>
                  {delta != null ? `${delta >= 0 ? "+" : ""}${(delta * 100).toFixed(1)}%` : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

function ThroughputSection({ telemetry }: { telemetry: ParityTelemetry | null }) {
  const tp = telemetry?.stages?.throughput;
  const byCand = tp?.throughput_by_candidate as Record<
    string,
    { mean_ms: number; n: number }
  > | undefined;
  if (!byCand || Object.keys(byCand).length === 0) return null;

  const sorted = Object.entries(byCand).sort(([a], [b]) =>
    a === "fission" ? -1 : b === "fission" ? 1 : a.localeCompare(b)
  );

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>Throughput · decompile time per binary</h2>
      <p className={styles.sectionLead}>
        Mean wall-clock time to decompile one binary. Lower = faster adapter.
      </p>
      <table className={styles.table ?? ""}>
        <thead>
          <tr>
            <th>Candidate</th>
            <th className={styles.num ?? ""}>Mean time</th>
            <th className={styles.num ?? ""}>Binaries</th>
            <th>Speed comparison</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(([cand, v]) => {
            const fastest = Math.min(...Object.values(byCand).map((x) => x.mean_ms));
            const ratio = fastest > 0 ? v.mean_ms / fastest : 1;
            return (
              <tr key={cand} className={cand === "fission" ? styles.fissionRow ?? "" : ""}>
                <td><strong style={{ color: cand === "fission" ? "#6366f1" : cand === "ghidra" ? "#10b981" : undefined }}>{cand}</strong></td>
                <td className={styles.num ?? ""}>
                  {v.mean_ms >= 1000 ? `${(v.mean_ms / 1000).toFixed(1)}s` : `${Math.round(v.mean_ms)}ms`}
                </td>
                <td className={styles.num ?? ""}>{v.n}</td>
                <td>
                  {ratio <= 1.01 ? "⚡ fastest" : `${ratio.toFixed(0)}× slower`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

async function LayeredParitySections() {
  const state = await getParityTelemetryState();
  const telemetry = state?.telemetry ?? null;
  return (
    <>
      <ParityDataStatus state={state} />
      <DualSection telemetry={telemetry} />
      <StageTableSection telemetry={telemetry} />
      <OptCliffSection telemetry={telemetry} />
      <ThroughputSection telemetry={telemetry} />
    </>
  );
}

async function CoreSemanticSection() {
  const data = await getLatestBenchmarkOptional({ requirePublishable: false });
  if (!data) {
    return (
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Core pair · semantic side-by-side</h2>
        <p className={styles.sectionLead}>
          Official multi-decomp envelope not available — parity tiles above still
          stand alone. Publish an official run to populate semantic cards.
        </p>
      </section>
    );
  }
  const stats = filterCorePairStats(groupByDecompiler(data));
  const sameFn = getSameFunctionSummary(data);
  const corpus = data.run?.corpus ?? "?";
  return (
    <>
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Core pair · semantic side-by-side</h2>
        <p className={styles.sectionLead}>
          From the multi-decomp envelope (<code>{corpus}</code>), filtered to
          Fission + Ghidra only. Useful context —{" "}
          <strong>not</strong> the ranking surface for other tools (see{" "}
          <Link href="/">Multi-decompiler</Link>).
        </p>
        <CorePairPanel stats={stats} />
      </section>
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Core · same-function rates</h2>
        <p className={styles.sectionLead}>
          Boundary contract on the core pair (expected ~1.0 after address anchors).
          {sameFn?.coreRate != null
            ? ` Core cohort rate: ${pct(sameFn.coreRate)}.`
            : ""}
        </p>
        <SameFunctionPanel summary={sameFn} compact />
      </section>
    </>
  );
}

function SkeletonSection({ rows = 4 }: { rows?: number }) {
  return (
    <section className={styles.section}>
      <div className={`${styles.skeletonLine} ${styles.sectionTitleSkeleton}`} />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className={`${styles.skeletonLine} ${styles.skeletonRow}`} />
      ))}
    </section>
  );
}

export default function FissionVsGhidraPage() {
  return (
    <SiteChrome
      active="parity"
      subtitle="Shared p-code-class IR · Ghidra reference · Fission candidate"
    >
      <div className={`${styles.frame} ${styles.frameParity}`}>
        <div className={styles.frameTitle}>Fission ↔ Ghidra layered parity</div>
        <p className={styles.frameBody}>
          Fission and Ghidra share a <strong>p-code-class intermediate
          representation</strong>. This page measures structural agreement —
          assembly bytes, p-code ops (strict/loose dual), CFG topology, and
          function inventories — with <strong>Ghidra as reference</strong> and{" "}
          <strong>Fission as candidate</strong>.
        </p>
        <p className={styles.frameNote}>
          Match rates here are not multi-decompiler quality rankings. Oracle
          semantic pass rate lives on the Multi-decompiler page.
        </p>
      </div>

      <div className={styles.cardGrid}>
        <Link href="/" className={styles.card}>
          <div className={styles.cardKicker}>Ranking surface</div>
          <div className={styles.cardTitle}>Multi-decompiler quality →</div>
          <p className={styles.cardBody}>
            Semantic oracle, coverage, same-function matrix, and full tool grid.
          </p>
        </Link>
        <div className={styles.card} style={{ cursor: "default" }}>
          <div className={styles.cardKicker}>Reference contract</div>
          <div className={styles.cardTitle}>Ghidra inventory &amp; IR</div>
          <p className={styles.cardBody}>
            Unified runner: <code>python -m runner.run_parity</code> with
            decompilers fission,ghidra.
          </p>
        </div>
      </div>

      <Suspense fallback={<SkeletonSection rows={6} />}>
        <LayeredParitySections />
      </Suspense>

      <Suspense fallback={<SkeletonSection rows={4} />}>
        <CoreSemanticSection />
      </Suspense>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Reproduce</h2>
        <div className={styles.repro}>
          <pre>{`export FISSION_HOST_PORT=8007
python -m runner.run_parity --corpus dev --limit 20 --decompilers fission,ghidra
python -m benchmark.telemetry.aggregate
# → public/parity-telemetry.json

python -m benchmark.function_discovery.run --limit 10
python scripts/check_parity_smoke.py public/parity-telemetry.json --require-provenance
python scripts/check_reliability.py public/parity-telemetry.json`}</pre>
        </div>
      </section>
    </SiteChrome>
  );
}
