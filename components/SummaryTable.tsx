"use client";

import styles from "./SummaryTable.module.css";
import type { MvpDecompilerStats } from "@/lib/benchmark";

interface Props {
  stats: MvpDecompilerStats[];
}

const DECOMPILER_COLORS: Record<string, string> = {
  fission: "#6366f1",
  ghidra: "#10b981",
  angr: "#f59e0b",
  radare2: "#ec4899",
  boomerang: "#14b8a6",
  snowman: "#8b5cf6",
  revng: "#f97316",
  reko: "#06b6d4",
  retdec: "#a78bfa",
};

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className={styles.barWrap}>
      <div
        className={styles.bar}
        style={{ width: `${Math.min(value * 100, 100)}%`, background: color }}
      />
      <span className={styles.barLabel}>{(value * 100).toFixed(1)}%</span>
    </div>
  );
}

function topTaxonomy(tax: Record<string, number>): string {
  const entries = Object.entries(tax).filter(([k, n]) => k !== "ok" && n > 0);
  if (entries.length === 0) return "—";
  entries.sort((a, b) => b[1] - a[1]);
  return entries
    .slice(0, 3)
    .map(([k, n]) => `${k}:${n}`)
    .join(" · ");
}

export function SummaryTable({ stats }: Props) {
  return (
    <div className={styles.wrap}>
      <p className={styles.hint}>
        MVP standard set — <strong>Semantic</strong> is the only ranking axis.
        The mean uses one shared subject denominator across tools, so missing
        peer measurements count as misses. Runtime is practicality; source
        similarity is diagnostic only.
      </p>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Decompiler</th>
            <th className={styles.num}>Attempted</th>
            <th className={styles.num}>Adapter clean</th>
            <th className={styles.num}>Boundary invalid</th>
            <th className={styles.num}>Observed / shared</th>
            <th>Shared semantic mean</th>
            <th className={styles.num}>Perfect</th>
            <th className={styles.num}>No wrapper</th>
            <th>Fail taxonomy (top)</th>
            <th className={styles.num}>Mean time</th>
          </tr>
        </thead>
        <tbody>
          {stats.map((s) => {
            const color = DECOMPILER_COLORS[s.decompiler] ?? "#94a3b8";
            const isFission = s.decompiler === "fission";
            return (
              <tr key={s.decompiler} className={isFission ? styles.fissionRow : undefined}>
                <td>
                  <span className={styles.dot} style={{ background: color }} />
                  <strong style={{ color: isFission ? color : "inherit" }}>
                    {s.decompiler}
                  </strong>
                </td>
                <td className={styles.num}>{s.attempted}</td>
                <td className={styles.num}>{s.adapterClean}</td>
                <td
                  className={`${styles.num} ${s.invalidBoundary > 0 ? styles.errorCell : ""}`}
                >
                  {s.invalidBoundary || "—"}
                </td>
                <td className={styles.num}>
                  {s.semanticTested} / {s.semanticSharedRows}
                </td>
                <td>
                  {s.meanSemantic === null ? (
                    "N/A"
                  ) : (
                    <ScoreBar value={s.meanSemantic} color={color} />
                  )}
                </td>
                <td className={styles.num}>
                  {s.semanticSharedRows > 0
                    ? `${s.perfectRows} / ${s.semanticSharedRows}`
                    : "—"}
                </td>
                <td className={styles.num}>{s.noWrapper || "—"}</td>
                <td className={styles.tax}>{topTaxonomy(s.taxonomy)}</td>
                <td className={styles.num}>
                  {s.meanTimeMs != null && s.meanTimeMs > 0
                    ? `${Math.round(s.meanTimeMs)}ms`
                    : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
