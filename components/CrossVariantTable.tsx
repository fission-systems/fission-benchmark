"use client";

import styles from "./SummaryTable.module.css";
import type { CrossVariantRow } from "@/lib/benchmark";

interface Props {
  rows: CrossVariantRow[];
}

/** Extension: semantic mean by decompiler × compiler variant. */
export function CrossVariantTable({ rows }: Props) {
  if (rows.length === 0) {
    return (
      <p className={styles.hint}>
        No cross-variant aggregate yet (envelope missing{" "}
        <code>summary.extensions.cross_variant</code>).
      </p>
    );
  }

  return (
    <div className={styles.wrap}>
      <p className={styles.hint}>
        Extension — semantic pass rate by compiler × optimization. Not a ranking
        axis; use to spot opt-level regressions. Each variant uses a shared
        subject denominator across decompilers.
      </p>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Decompiler</th>
            <th>Variant</th>
            <th>Compiler</th>
            <th>Opt</th>
            <th className={styles.num}>Observed / shared</th>
            <th className={styles.num}>Shared semantic mean</th>
            <th className={styles.num}>Perfect</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${r.decompiler}:${r.compiler_variant}`}>
              <td>
                <strong>{r.decompiler}</strong>
              </td>
              <td>
                <code>{r.compiler_variant}</code>
              </td>
              <td>{r.compiler}</td>
              <td>{r.opt || "—"}</td>
              <td className={styles.num}>
                {r.tested_rows} / {r.shared_rows ?? r.tested_rows}
              </td>
              <td className={styles.num}>
                {r.mean_pass_rate == null
                  ? "N/A"
                  : `${(r.mean_pass_rate * 100).toFixed(1)}%`}
              </td>
              <td className={styles.num}>{r.perfect_rows}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
