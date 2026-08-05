import { Suspense } from "react";
import { SiteChrome } from "@/components/SiteChrome";
import { ValidityBanner } from "@/components/ValidityBanner";
import { UnavailableData } from "@/components/UnavailableData";
import {
  MetaStrip,
  SkeletonMeta,
  SkeletonSection,
} from "@/components/DashboardShared";
import { getLatestBenchmarkOptional } from "@/lib/benchmark";
import {
  extractSpeedExtension,
  fissionByVariant,
  fissionSlowestFunctions,
  fissionVsGhidraPaired,
  pairSummary,
  speedByDecompiler,
} from "@/lib/speed";
import {
  chooseNewestMicrobench,
  getLatestSpeedMicrobench,
} from "@/lib/speed-microbench";
import {
  DecompilerSpeedTable,
  PairedSpeedTable,
  SlowestFunctionsTable,
  VariantSpeedTable,
} from "@/components/SpeedPanel";
import tableStyles from "@/components/SummaryTable.module.css";
import styles from "../dashboard.module.css";

export const revalidate = 900;

export const metadata = {
  title: "Speed · Decompile latency",
  description:
    "Fission and multi-decompiler decompile wall times (time_ms) — non-ranking diagnostics.",
};

async function BannerSection() {
  const data = await getLatestBenchmarkOptional();
  if (!data) return null;
  return <ValidityBanner validity={data.validity} run={data.run} />;
}

function Tile({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className={styles.frame}>
      <div className={styles.frameTitle}>{label}</div>
      <p className={styles.frameBody} style={{ fontSize: "1.35rem", fontWeight: 700 }}>
        {value}
      </p>
      {hint ? (
        <p className={styles.sectionLead} style={{ marginTop: "0.35rem", marginBottom: 0 }}>
          {hint}
        </p>
      ) : null}
    </div>
  );
}

function fmtMs(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  if (v >= 1000) return `${(v / 1000).toFixed(2)}s`;
  return `${Math.round(v)}ms`;
}

function fmtX(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  return `${v.toFixed(2)}×`;
}

function fmtPct(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  return `${v.toFixed(1)}%`;
}

function fmtBytes(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  const units = ["B", "KiB", "MiB", "GiB"];
  let value = v;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}

async function SpeedBody() {
  const [data, standaloneMicrobench] = await Promise.all([
    getLatestBenchmarkOptional(),
    getLatestSpeedMicrobench(),
  ]);
  if (!data) {
    return (
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Speed</h2>
        <UnavailableData title="Speed diagnostics unavailable" />
      </section>
    );
  }

  const byDec = speedByDecompiler(data);
  const fission = byDec.find((r) => r.decompiler === "fission");
  const ghidra = byDec.find((r) => r.decompiler === "ghidra");
  const pairs = fissionVsGhidraPaired(data);
  const pair = pairSummary(pairs);
  const slowest = fissionSlowestFunctions(data, 30);
  const variants = fissionByVariant(data);
  const ext = extractSpeedExtension(data);
  const loadedMicro = chooseNewestMicrobench(ext?.microbench, standaloneMicrobench);
  const micro = loadedMicro?.data;
  const microBy = micro?.by_decompiler ?? {};
  const microNames = Object.keys(microBy).sort((a, b) => {
    if (a === "fission") return -1;
    if (b === "fission") return 1;
    return a.localeCompare(b);
  });

  return (
    <>
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Decompile speed</h2>
        <p className={styles.sectionLead}>
          Wall time from the decompiler adapter (<code>time_ms</code> on each
          row) — typically one binary batch decompile, amortized per function.
          Semantic / wine / oracle time is <strong>not</strong> included. This
          page is a <strong>non-ranking</strong> practicality diagnostic (same
          policy as Quality EXT). Optional{" "}
          <code>summary.extensions.speed.microbench</code> cold/warm trials come
          from the isolated <strong>Speed Smoke</strong> CI job.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
            gap: "0.75rem",
            marginBottom: "1.25rem",
          }}
        >
          <Tile
            label="Fission mean"
            value={fmtMs(fission?.mean)}
            hint={fission ? `n=${fission.timedRows} · p95 ${fmtMs(fission.p95)}` : undefined}
          />
          <Tile
            label="Fission p50"
            value={fmtMs(fission?.p50)}
            hint="Median decompile latency"
          />
          <Tile
            label="Ghidra mean"
            value={fmtMs(ghidra?.mean)}
            hint={ghidra ? `n=${ghidra.timedRows} · p95 ${fmtMs(ghidra.p95)}` : undefined}
          />
          <Tile
            label="Paired speedup"
            value={fmtX(pair.medianSpeedup)}
            hint={
              pair.n
                ? `median ghidra/fission · n=${pair.n} pairs · geo ${fmtX(pair.geometricMeanSpeedup)}`
                : "Need both tools on same cells"
            }
          />
          <Tile
            label="Fission faster"
            value={
              pair.fissionFasterShare != null
                ? `${(pair.fissionFasterShare * 100).toFixed(0)}%`
                : "—"
            }
            hint="Share of paired cells with fission_ms < ghidra_ms"
          />
        </div>
      </section>

      {microNames.length > 0 ? (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Micro-bench (cold vs warm)</h2>
          <p className={styles.sectionLead}>
            Same binary × addresses, N timed <code>/decompile_batch</code>{" "}
            requests. Cold = trial 0; warm = trials 1..N−1 (no container
            restart). Schema:{" "}
            <code>{micro?.schema ?? "speed-microbench-v2"}</code>
            {loadedMicro?.source ? ` · source: ${loadedMicro.source}` : ""}
            {micro?.toolchain?.fission_version
              ? ` · Fission ${micro.toolchain.fission_version}`
              : " · Fission version not recorded"}
            {micro?.finished_at
              ? ` · measured: ${new Date(micro.finished_at).toLocaleString("en-US", { timeZone: "UTC", timeZoneName: "short" })}`
              : ""}
            {micro?.notes ? ` — ${micro.notes}` : ""}
          </p>
          <div className={styles.frame}>
            <div className={tableStyles.wrap}>
              <table className={tableStyles.table}>
                <thead>
                  <tr>
                    <th>Decompiler</th>
                    <th className={tableStyles.num}>Cold mean</th>
                    <th className={tableStyles.num}>Cold p50</th>
                    <th className={tableStyles.num}>Cold n</th>
                    <th className={tableStyles.num}>Warm mean</th>
                    <th className={tableStyles.num}>Warm p50</th>
                    <th className={tableStyles.num}>Warm n</th>
                    <th className={tableStyles.num}>CPU mean</th>
                    <th className={tableStyles.num}>CPU peak</th>
                    <th className={tableStyles.num}>Memory peak</th>
                    <th className={tableStyles.num}>Memory %</th>
                    <th className={tableStyles.num}>Samples</th>
                  </tr>
                </thead>
                <tbody>
                  {microNames.map((name) => {
                    const s = microBy[name] || {};
                    const cold = s.cold || {};
                    const warm = s.warm || {};
                    const resources = s.resources?.all || {};
                    return (
                      <tr
                        key={name}
                        className={
                          name === "fission" ? tableStyles.fissionRow : undefined
                        }
                      >
                        <td>
                          <strong>{name}</strong>
                        </td>
                        <td className={tableStyles.num}>{fmtMs(cold.mean_ms)}</td>
                        <td className={tableStyles.num}>{fmtMs(cold.p50_ms)}</td>
                        <td className={tableStyles.num}>{cold.n ?? "—"}</td>
                        <td className={tableStyles.num}>{fmtMs(warm.mean_ms)}</td>
                        <td className={tableStyles.num}>{fmtMs(warm.p50_ms)}</td>
                        <td className={tableStyles.num}>{warm.n ?? "—"}</td>
                        <td className={tableStyles.num}>{fmtPct(resources.mean_cpu_percent)}</td>
                        <td className={tableStyles.num}>{fmtPct(resources.peak_cpu_percent)}</td>
                        <td className={tableStyles.num}>{fmtBytes(resources.peak_memory_bytes)}</td>
                        <td className={tableStyles.num}>{fmtPct(resources.peak_memory_percent)}</td>
                        <td className={tableStyles.num}>{resources.samples ?? "—"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          <p className={styles.sectionLead}>
            Resource scope is the whole adapter container cgroup, including the
            long-lived runtime and child processes. CPU may exceed 100% on
            multicore runners. Memory peak is the largest Docker sample observed
            during timed requests, not an operating-system high-water mark.
          </p>
        </section>
      ) : (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Micro-bench (cold vs warm)</h2>
          <p className={styles.sectionLead}>
            No version-linked <code>summary.extensions.speed.microbench</code>{" "}
            is available for the latest Fission release. Older and unversioned
            microbench artifacts are intentionally hidden. {" "}
            Run{" "}
            <code>python -m runner.speed_microbench …</code> or the{" "}
            <strong>Speed Smoke</strong> GitHub Action; attach via{" "}
            <code>attach_summary_to_envelope</code> (auto-loads{" "}
            <code>results/speed/microbench_latest.json</code>).
          </p>
        </section>
      )}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>By decompiler (envelope rows)</h2>
        <div className={styles.frame}>
          <DecompilerSpeedTable rows={byDec} />
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Fission ↔ Ghidra (paired)</h2>
        <div className={styles.frame}>
          <PairedSpeedTable pairs={pairs} limit={40} />
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Slowest Fission functions</h2>
        <div className={styles.frame}>
          <SlowestFunctionsTable rows={slowest} />
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Fission by compiler variant</h2>
        <div className={styles.frame}>
          <VariantSpeedTable rows={variants} />
        </div>
      </section>
    </>
  );
}

export default function SpeedPage() {
  return (
    <SiteChrome active="speed" subtitle="Decompile latency · non-ranking">
      <Suspense fallback={<div className={styles.bannerSkeleton} />}>
        <BannerSection />
      </Suspense>
      <Suspense fallback={<SkeletonMeta />}>
        <MetaStrip />
      </Suspense>
      <Suspense fallback={<SkeletonSection />}>
        <SpeedBody />
      </Suspense>
    </SiteChrome>
  );
}
