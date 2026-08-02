"use client";

import { useMemo } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
  type ChartOptions,
  type ChartData,
  type Plugin,
  type ScriptableContext,
  type TooltipItem,
} from "chart.js";
import { Line } from "react-chartjs-2";
import type { VersionTrendPoint } from "@/lib/history";
import { pct } from "@/lib/format";
import styles from "./VersionTrendChart.module.css";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

interface Props {
  points: VersionTrendPoint[];
}

const ACCENT = "#6366f1";
const ACCENT_FILL_TOP = "rgba(99, 102, 241, 0.28)";
const ACCENT_FILL_BOTTOM = "rgba(99, 102, 241, 0)";
const GRID = "#2d3748";
const AXIS_TEXT = "#94a3b8";
const CORPUS_CHANGED = "#f59e0b";
const DOT_HOLLOW_FILL = "#1e293b"; // matches --bg-elevated, so a "hollow" point reads as an outline

const MIN_RADIUS = 3;
const MAX_RADIUS_BONUS = 7;

/** Same sqrt-area scaling as the original hand-rolled SVG: area (not radius)
 * scales with row count, so a 4x bigger corpus reads as a 2x bigger dot,
 * not a 4x bigger one -- otherwise small corpora vanish and big ones
 * swallow the chart. */
function dotRadius(rows: number, maxRows: number): number {
  if (maxRows <= 0) return MIN_RADIUS;
  const scale = Math.sqrt(Math.max(rows, 1) / maxRows);
  return MIN_RADIUS + scale * MAX_RADIUS_BONUS;
}

/** Draws the small amber "corpus N→M" callouts under releases where the
 * measured corpus size changed from the previous release -- Chart.js has no
 * built-in per-point sub-label, so this is a plugin that reaches into the
 * already-laid-out x scale and paints directly on the canvas after the
 * chart finishes its own draw pass. */
function makeCorpusChangePlugin(points: VersionTrendPoint[]): Plugin<"line"> {
  return {
    id: "corpusChangeLabels",
    afterDraw(chart) {
      const xScale = chart.scales.x;
      if (!xScale) return;
      const { ctx } = chart;
      ctx.save();
      ctx.font = "600 9px system-ui, sans-serif";
      ctx.fillStyle = CORPUS_CHANGED;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      points.forEach((point, index) => {
        if (index === 0) return;
        const prev = points[index - 1];
        if (prev.totalRows === point.totalRows) return;
        const x = xScale.getPixelForValue(index);
        ctx.fillText(`corpus ${prev.totalRows}→${point.totalRows}`, x, xScale.bottom + 14);
      });
      ctx.restore();
    },
  };
}

export function VersionTrendChart({ points }: Props) {
  const maxRows = useMemo(() => Math.max(1, ...points.map((p) => p.totalRows)), [points]);
  const minRows = useMemo(
    () => (points.length ? Math.min(...points.map((p) => p.totalRows)) : 0),
    [points],
  );

  const data: ChartData<"line", (number | null)[], string> = useMemo(
    () => ({
      labels: points.map((p) => p.version),
      datasets: [
        {
          data: points.map((p) => (p.meanSemantic !== null ? p.meanSemantic : null)),
          borderColor: ACCENT,
          borderWidth: 2.5,
          cubicInterpolationMode: "monotone",
          tension: 0.35,
          spanGaps: false,
          fill: true,
          backgroundColor: (context: ScriptableContext<"line">) => {
            const { chart } = context;
            const { ctx, chartArea } = chart;
            if (!chartArea) return ACCENT_FILL_BOTTOM;
            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            gradient.addColorStop(0, ACCENT_FILL_TOP);
            gradient.addColorStop(1, ACCENT_FILL_BOTTOM);
            return gradient;
          },
          pointRadius: (context: ScriptableContext<"line">) => {
            const point = points[context.dataIndex];
            if (!point || point.meanSemantic === null) return 0;
            return dotRadius(point.totalRows, maxRows);
          },
          pointHoverRadius: (context: ScriptableContext<"line">) => {
            const point = points[context.dataIndex];
            if (!point || point.meanSemantic === null) return 0;
            return dotRadius(point.totalRows, maxRows) + 2;
          },
          pointBackgroundColor: (context: ScriptableContext<"line">) => {
            const point = points[context.dataIndex];
            return point?.official ? ACCENT : DOT_HOLLOW_FILL;
          },
          pointBorderColor: ACCENT,
          pointBorderWidth: 2,
          pointHoverBorderWidth: 2,
        },
      ],
    }),
    [points, maxRows],
  );

  const options: ChartOptions<"line"> = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { bottom: 20, right: 12, top: 8 } },
      interaction: { mode: "index", intersect: false },
      scales: {
        x: {
          grid: { display: false },
          border: { display: false },
          ticks: { color: AXIS_TEXT, font: { size: 11 } },
        },
        y: {
          min: 0,
          max: 1,
          border: { display: false },
          grid: { color: GRID, drawTicks: false },
          ticks: {
            color: AXIS_TEXT,
            font: { size: 11 },
            stepSize: 0.25,
            callback: (value) => `${Math.round(Number(value) * 100)}%`,
          },
        },
      },
      plugins: {
        tooltip: {
          backgroundColor: "#0f172a",
          borderColor: GRID,
          borderWidth: 1,
          cornerRadius: 8,
          padding: 10,
          displayColors: false,
          titleColor: "#e2e8f0",
          titleFont: { size: 12, weight: 600 },
          bodyColor: AXIS_TEXT,
          bodyFont: { size: 11 },
          callbacks: {
            title: (items: TooltipItem<"line">[]) => points[items[0].dataIndex]?.version ?? "",
            label: (item: TooltipItem<"line">) => {
              const point = points[item.dataIndex];
              if (!point || point.meanSemantic === null) return "no data";
              return [
                `${pct(point.meanSemantic)} semantic pass rate`,
                `${point.perfectRows}/${point.totalRows} perfect rows`,
                point.official ? "official run" : "smoke run",
              ];
            },
          },
        },
      },
    }),
    [points],
  );

  const plugins = useMemo(() => [makeCorpusChangePlugin(points)], [points]);

  if (points.length === 0) {
    return (
      <p className={styles.empty}>No archived releases with multi-decomp data yet.</p>
    );
  }

  return (
    <div className={styles.wrap}>
      <div
        className={styles.canvasFrame}
        role="img"
        aria-label={`Fission semantic pass rate by release, from ${points[0].version} to ${points[points.length - 1].version}`}
      >
        <Line data={data} options={options} plugins={plugins} />
      </div>
      <p className={styles.hint}>
        Dot size ∝ corpus size measured at that release ({minRows}–{maxRows} Fission rows).
        Hollow dots are smoke-profile runs; filled dots are official publications.
      </p>
    </div>
  );
}
