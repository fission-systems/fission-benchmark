"use client";

import { useMemo } from "react";
import type { VersionTrendPoint } from "@/lib/history";
import { pct } from "@/lib/format";
import {
  ReleaseMetricChart,
  type ReleaseMetricSeries,
} from "./ReleaseMetricChart";
import styles from "./VersionTrendChart.module.css";

interface Props {
  points: VersionTrendPoint[];
}

const LATENCY: ReleaseMetricSeries[] = [
  { label: "Mean", color: "#6366f1", value: (point) => point.latencyMeanMs },
  { label: "P50", color: "#22c55e", value: (point) => point.latencyP50Ms },
  { label: "P95", color: "#f59e0b", value: (point) => point.latencyP95Ms },
];
const SPEEDUP: ReleaseMetricSeries[] = [
  { label: "Median", color: "#22c55e", value: (point) => point.medianSpeedup },
  { label: "Geometric mean", color: "#38bdf8", value: (point) => point.geometricMeanSpeedup },
];
const FASTER_SHARE: ReleaseMetricSeries[] = [
  { label: "Fission faster", color: "#22c55e", value: (point) => point.fissionFasterShare === null ? null : point.fissionFasterShare * 100 },
];
const MICRO_LATENCY: ReleaseMetricSeries[] = [
  { label: "Cold mean", color: "#f59e0b", value: (point) => point.coldMeanMs },
  { label: "Cold P50", color: "#fbbf24", value: (point) => point.coldP50Ms },
  { label: "Warm mean", color: "#6366f1", value: (point) => point.warmMeanMs },
  { label: "Warm P50", color: "#a78bfa", value: (point) => point.warmP50Ms },
];
const RESOURCE_PERCENT: ReleaseMetricSeries[] = [
  { label: "CPU mean", color: "#38bdf8", value: (point) => point.meanCpuPercent },
  { label: "CPU peak", color: "#f59e0b", value: (point) => point.peakCpuPercent },
  { label: "Memory peak", color: "#a78bfa", value: (point) => point.peakMemoryPercent },
];
const MEMORY: ReleaseMetricSeries[] = [
  { label: "Sampled peak", color: "#a78bfa", value: (point) => point.peakMemoryBytes },
];
const QUALITY: ReleaseMetricSeries[] = [
  { label: "Semantic pass", color: "#6366f1", value: (point) => point.meanSemantic === null ? null : point.meanSemantic * 100 },
];

function missingPatchVersions(points: VersionTrendPoint[]): string[] {
  const parsed = points
    .map((point) => /^v?(\d+)\.(\d+)\.(\d+)$/.exec(point.version))
    .filter((match): match is RegExpExecArray => Boolean(match))
    .map((match) => [Number(match[1]), Number(match[2]), Number(match[3])] as const);
  if (parsed.length < 2) return [];
  const [major, minor] = parsed[0];
  if (!parsed.every(([ma, mi]) => ma === major && mi === minor)) return [];
  const patches = new Set(parsed.map(([, , patch]) => patch));
  const min = Math.min(...patches);
  const max = Math.max(...patches);
  const missing: string[] = [];
  for (let patch = min; patch <= max; patch += 1) {
    if (!patches.has(patch)) missing.push(`v${major}.${minor}.${patch}`);
  }
  return missing;
}

function fmtMs(value: number | null): string {
  if (value === null) return "—";
  return value >= 1000 ? `${(value / 1000).toFixed(2)}s` : `${Math.round(value)}ms`;
}

function fmtRatio(value: number | null): string {
  return value === null ? "—" : `${value.toFixed(2)}×`;
}

function fmtPercent(value: number | null): string {
  return value === null ? "—" : `${value.toFixed(1)}%`;
}

function fmtBytes(value: number | null): string {
  return value === null ? "—" : `${(value / 1024 / 1024).toFixed(1)} MiB`;
}

function classification(point: VersionTrendPoint): string {
  return point.trendEligible
    ? "official · comparable"
    : point.canonical
      ? "official · different contract"
      : "diagnostic / smoke";
}

export function VersionTrendChart({ points }: Props) {
  const eligible = useMemo(() => points.filter((point) => point.trendEligible), [points]);
  const diagnostics = useMemo(() => points.filter((point) => !point.canonical), [points]);
  const missing = useMemo(() => missingPatchVersions(points), [points]);

  if (points.length === 0) {
    return <p className={styles.empty}>No archived releases with multi-decomp data yet.</p>;
  }

  return (
    <div className={styles.wrap}>
      {eligible.length < 2 && (
        <div className={styles.warning}>
          <strong>Official trend unavailable.</strong> This archive contains{" "}
          {eligible.length} comparable official point{eligible.length === 1 ? "" : "s"}
          {diagnostics.length > 0 ? ` and ${diagnostics.length} diagnostic/smoke snapshots` : ""}.
          Dashed diagnostic lines show engineering history only; they are not an
          official release-performance claim.
        </div>
      )}

      <h3 className={styles.groupTitle}>Performance trend</h3>
      <p className={styles.groupLead}>
        Accuracy saturates near 100%, so release progress is led by latency,
        paired speedup, cold/warm behavior, CPU, and memory. Lower is better for
        latency and memory; higher is better for paired speedup.
      </p>
      <div className={styles.metricGrid}>
        <ReleaseMetricChart
          title="Adapter latency"
          description="Fission row timing: mean, P50, and P95. Lower is better."
          points={points} series={LATENCY} format="ms"
        />
        <ReleaseMetricChart
          title="Paired speedup vs Ghidra"
          description="Same function and compiler cell; Ghidra time divided by Fission time."
          points={points} series={SPEEDUP} format="ratio"
        />
        <ReleaseMetricChart
          title="Fission-faster share"
          description="Share of paired cells where Fission latency is lower than Ghidra."
          points={points} series={FASTER_SHARE} format="percent"
        />
        <ReleaseMetricChart
          title="Cold vs warm microbench"
          description="Version-linked isolated trials. Missing history is shown as unmeasured."
          points={points} series={MICRO_LATENCY} format="ms"
        />
        <ReleaseMetricChart
          title="CPU and memory utilization"
          description="Container-cgroup CPU mean/peak and peak memory share. CPU can exceed 100%."
          points={points} series={RESOURCE_PERCENT} format="percent"
        />
        <ReleaseMetricChart
          title="Sampled peak memory"
          description="Largest Docker memory sample during timed requests; not an OS high-water mark."
          points={points} series={MEMORY} format="bytes"
        />
      </div>

      <h3 className={styles.groupTitle}>Quality guardrail</h3>
      <p className={styles.groupLead}>
        Semantic pass rate remains visible as a guardrail, but no longer carries
        the entire release story once it reaches saturation.
      </p>
      <div className={styles.qualityGrid}>
        <ReleaseMetricChart
          title="Semantic pass rate"
          description="Executable-oracle pass rate. Higher is better; 100% is the ceiling."
          points={points} series={QUALITY} format="percent"
        />
      </div>

      <p className={styles.hint}>
        Solid lines = valid, publishable official runs with the same contract and
        Fission cells. Dashed hollow lines = comparable diagnostic history.
        Grey isolated points = a different contract.
        {missing.length > 0 ? ` Missing archives break the line: ${missing.join(", ")}.` : ""}
      </p>

      <h3 className={styles.tableTitle}>Release performance audit</h3>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead><tr>
            <th>Version</th><th>Mean</th><th>P50</th><th>P95</th>
            <th>Speedup median</th><th>Geo mean</th><th>Faster share</th>
            <th>Cold mean</th><th>Warm mean</th><th>CPU mean</th><th>CPU peak</th>
            <th>Memory peak</th><th>Memory %</th><th>Samples</th>
          </tr></thead>
          <tbody>{points.map((point) => <tr key={point.version}>
            <td><code>{point.version}</code></td>
            <td>{fmtMs(point.latencyMeanMs)}</td><td>{fmtMs(point.latencyP50Ms)}</td>
            <td>{fmtMs(point.latencyP95Ms)}</td><td>{fmtRatio(point.medianSpeedup)}</td>
            <td>{fmtRatio(point.geometricMeanSpeedup)}</td>
            <td>{point.fissionFasterShare === null ? "—" : pct(point.fissionFasterShare)}</td>
            <td>{fmtMs(point.coldMeanMs)}</td><td>{fmtMs(point.warmMeanMs)}</td>
            <td>{fmtPercent(point.meanCpuPercent)}</td><td>{fmtPercent(point.peakCpuPercent)}</td>
            <td>{fmtBytes(point.peakMemoryBytes)}</td><td>{fmtPercent(point.peakMemoryPercent)}</td>
            <td>{point.resourceSamples || "—"}</td>
          </tr>)}</tbody>
        </table>
      </div>

      <h3 className={styles.tableTitle}>Measurement contract audit</h3>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead><tr>
            <th>Version</th><th>Classification</th><th>Profile</th><th>Corpus</th>
            <th>Rows</th><th>Tested</th><th>Semantic</th><th>Paired</th><th>Measured</th>
          </tr></thead>
          <tbody>{points.map((point) => <tr key={point.version}>
            <td><code>{point.version}</code></td><td>{classification(point)}</td>
            <td><code>{point.profile ?? "—"}</code></td><td><code>{point.corpus ?? "—"}</code></td>
            <td>{point.totalRows}</td><td>{point.semanticTestedRows}</td>
            <td>{pct(point.meanSemantic)}</td><td>{point.pairedRows}</td>
            <td>{point.finishedAt ? new Date(point.finishedAt).toLocaleDateString("en-CA", { timeZone: "UTC" }) : "—"}</td>
          </tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}
