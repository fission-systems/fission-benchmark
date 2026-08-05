"use client";

import { useMemo } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";
import type { VersionTrendPoint } from "@/lib/history";
import styles from "./VersionTrendChart.module.css";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

export type ReleaseMetricSeries = {
  label: string;
  color: string;
  value: (point: VersionTrendPoint) => number | null;
};

type ValueFormat = "ms" | "percent" | "ratio" | "bytes";

interface Props {
  title: string;
  description: string;
  points: VersionTrendPoint[];
  series: ReleaseMetricSeries[];
  format: ValueFormat;
}

function formatValue(value: number, format: ValueFormat): string {
  if (format === "percent") return `${value.toFixed(1)}%`;
  if (format === "ratio") return `${value.toFixed(2)}×`;
  if (format === "bytes") return `${(value / 1024 / 1024).toFixed(1)} MiB`;
  if (value >= 1000) return `${(value / 1000).toFixed(2)}s`;
  return `${Math.round(value)}ms`;
}

function releaseSlots(points: VersionTrendPoint[]) {
  const parsed = points.map((point) => ({
    point,
    match: /^v?(\d+)\.(\d+)\.(\d+)$/.exec(point.version),
  }));
  if (parsed.length < 2 || parsed.some((item) => !item.match)) {
    return points.map((point) => ({ label: point.version, point }));
  }
  const first = parsed[0].match!;
  const major = Number(first[1]);
  const minor = Number(first[2]);
  if (parsed.some((item) => Number(item.match![1]) !== major || Number(item.match![2]) !== minor)) {
    return points.map((point) => ({ label: point.version, point }));
  }
  const byPatch = new Map(parsed.map((item) => [Number(item.match![3]), item.point]));
  const patches = [...byPatch.keys()];
  const min = Math.min(...patches);
  const max = Math.max(...patches);
  return Array.from({ length: max - min + 1 }, (_, offset) => {
    const patch = min + offset;
    return { label: `v${major}.${minor}.${patch}`, point: byPatch.get(patch) ?? null };
  });
}

export function ReleaseMetricChart({ title, description, points, series, format }: Props) {
  const slots = useMemo(() => releaseSlots(points), [points]);
  const referenceContract = [...points].reverse().find((point) => point.canonical)?.contractKey
    ?? points.at(-1)?.contractKey;
  const hasValues = series.some((item) => points.some((point) => item.value(point) !== null));

  const data: ChartData<"line", (number | null)[], string> = useMemo(() => {
    const datasets = series.flatMap((item) => {
      const official = slots.map(({ point }) =>
        point?.trendEligible ? item.value(point) : null,
      );
      const diagnostic = slots.map(({ point }) =>
        point && !point.canonical && point.contractKey === referenceContract
          ? item.value(point)
          : null,
      );
      const incompatible = slots.map(({ point }) =>
        point && !point.trendEligible &&
        (point.canonical || point.contractKey !== referenceContract)
          ? item.value(point)
          : null,
      );
      const output = [];
      if (official.some((value) => value !== null)) {
        output.push({
          label: `${item.label} · official`, data: official,
          borderColor: item.color, backgroundColor: item.color,
          borderWidth: 2.5, pointRadius: 4, pointHoverRadius: 6,
          tension: 0, spanGaps: false,
        });
      }
      if (diagnostic.some((value) => value !== null)) {
        output.push({
          label: `${item.label} · diagnostic`, data: diagnostic,
          borderColor: item.color, backgroundColor: "#1e293b",
          pointBorderColor: item.color, pointBorderWidth: 2,
          borderWidth: 2, borderDash: [6, 5], pointRadius: 4,
          pointHoverRadius: 6, tension: 0, spanGaps: false,
        });
      }
      if (incompatible.some((value) => value !== null)) {
        output.push({
          label: `${item.label} · different contract`, data: incompatible,
          showLine: false, borderColor: "#64748b", backgroundColor: "#1e293b",
          pointBorderColor: "#64748b", pointBorderWidth: 2,
          pointRadius: 4, pointHoverRadius: 6,
        });
      }
      return output;
    });
    return { labels: slots.map((slot) => slot.label), datasets };
  }, [referenceContract, series, slots]);

  const options: ChartOptions<"line"> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    layout: { padding: { top: 8, right: 8 } },
    scales: {
      x: {
        grid: { display: false }, border: { display: false },
        ticks: { color: "#94a3b8", font: { size: 10 } },
      },
      y: {
        beginAtZero: false,
        border: { display: false },
        grid: { color: "#2d3748", drawTicks: false },
        ticks: {
          color: "#94a3b8", font: { size: 10 },
          callback: (value) => formatValue(Number(value), format),
        },
      },
    },
    plugins: {
      legend: {
        position: "bottom",
        labels: { color: "#94a3b8", boxWidth: 18, boxHeight: 2, font: { size: 10 } },
      },
      tooltip: {
        backgroundColor: "#0f172a", borderColor: "#2d3748", borderWidth: 1,
        displayColors: true,
        callbacks: {
          label: (item) => item.parsed.y === null
            ? `${item.dataset.label}: unmeasured`
            : `${item.dataset.label}: ${formatValue(item.parsed.y, format)}`,
        },
      },
    },
  }), [format]);

  return (
    <section className={styles.metricCard}>
      <h3>{title}</h3>
      <p>{description}</p>
      {hasValues ? (
        <div className={styles.metricCanvas} role="img" aria-label={`${title} by release`}>
          <Line data={data} options={options} />
        </div>
      ) : (
        <div className={styles.metricEmpty}>
          Not measured in any version-linked release snapshot yet.
        </div>
      )}
    </section>
  );
}
