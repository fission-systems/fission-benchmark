"use client";

import { useMemo, useState } from "react";
import type {
  MeasurementHealth,
  MeasurementToolHealth,
} from "@/lib/benchmark";
import tableStyles from "./SummaryTable.module.css";
import styles from "./MeasurementHealthPanel.module.css";

function percent(value: number | null | undefined): string {
  return value == null || Number.isNaN(value) ? "—" : `${(value * 100).toFixed(1)}%`;
}

function millis(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value >= 1000 ? `${(value / 1000).toFixed(2)}s` : `${Math.round(value)}ms`;
}

function toolOrder(left: string, right: string): number {
  if (left === "fission") return -1;
  if (right === "fission") return 1;
  return left.localeCompare(right);
}

function metricCell(
  tool: MeasurementToolHealth,
  metric: "semantic" | "ged" | "type_match",
): string {
  const data = tool[metric];
  const value = metric === "semantic" ? data.shared_mean : data.perfect_rate;
  return `${percent(value)} · ${data.observed_rows}/${data.shared_rows}`;
}

export function MeasurementHealthPanel({ health }: { health: MeasurementHealth }) {
  const [presetId, setPresetId] = useState(health.default_preset);
  const [normalization, setNormalization] = useState<"shared" | "intersection">(
    health.default_normalization,
  );
  const preset =
    health.presets.find((candidate) => candidate.id === presetId) ?? health.presets[0];
  const view = preset?.views[normalization];
  const tools = useMemo(
    () => Object.keys(view?.by_decompiler ?? {}).sort(toolOrder),
    [view],
  );

  if (!preset || !view) {
    return <p className={styles.empty}>No measurement-health preset is available.</p>;
  }

  const source = view.pipeline.source_cfg;
  const oracle = view.pipeline.oracle;
  return (
    <>
      <div className={styles.controls}>
        <label className={styles.field}>
          <span>Preset</span>
          <select value={preset.id} onChange={(event) => setPresetId(event.target.value)}>
            {health.presets.map((candidate) => (
              <option value={candidate.id} key={candidate.id}>
                {candidate.label}
              </option>
            ))}
          </select>
        </label>
        <fieldset className={styles.toggle}>
          <legend>Denominator</legend>
          <button
            type="button"
            aria-pressed={normalization === "shared"}
            onClick={() => setNormalization("shared")}
          >
            Shared scope
          </button>
          <button
            type="button"
            aria-pressed={normalization === "intersection"}
            onClick={() => setNormalization("intersection")}
          >
            Normalize intersection
          </button>
        </fieldset>
        <p className={styles.contract}>{health.normalization_contract[normalization]}</p>
      </div>

      <div className={styles.tiles}>
        <ScopeTile label="Subjects" value={String(view.scope.subjects)} hint={`${view.scope.rows} tool rows`} />
        <ScopeTile label="Decompilers" value={String(view.scope.decompilers)} hint="active in preset" />
        <ScopeTile label="Source CFG" value={percent(source.rate)} hint={`${source.available}/${source.subjects} subjects`} />
        <ScopeTile label="Oracle tested" value={percent(oracle.attempted ? oracle.tested / oracle.attempted : null)} hint={`${oracle.tested}/${oracle.attempted} rows`} />
      </div>

      <section className={styles.block}>
        <h2>Comparable outcomes</h2>
        <p>
          Semantic uses the shared missing-as-miss denominator. GED and type show exact
          diagnostic matches. Compile is decompiled-C recompilation, not semantic ranking.
        </p>
        <div className={tableStyles.wrap}>
          <table className={tableStyles.table}>
            <thead>
              <tr>
                <th>Decompiler</th>
                <th className={tableStyles.num}>Output clean</th>
                <th className={tableStyles.num}>Semantic · observed/shared</th>
                <th className={tableStyles.num}>GED exact · observed/shared</th>
                <th className={tableStyles.num}>Type exact · observed/shared</th>
                <th className={tableStyles.num}>Compiles</th>
                <th className={tableStyles.num}>Byte match</th>
              </tr>
            </thead>
            <tbody>
              {tools.map((toolName) => {
                const tool = view.by_decompiler[toolName];
                return (
                  <tr key={toolName} className={toolName === "fission" ? tableStyles.fissionRow : undefined}>
                    <td><strong>{toolName}</strong></td>
                    <td className={tableStyles.num}>{percent(tool.output_clean_rate)} · {tool.output_clean}/{tool.attempted}</td>
                    <td className={tableStyles.num}>{metricCell(tool, "semantic")}</td>
                    <td className={tableStyles.num}>{metricCell(tool, "ged")}</td>
                    <td className={tableStyles.num}>{metricCell(tool, "type_match")}</td>
                    <td className={tableStyles.num}>{percent(tool.compile.compilable_rate)} · {tool.compile.compilable_rows}/{tool.compile.measured_rows}</td>
                    <td className={tableStyles.num}>{percent(tool.compile.byte_match_rate)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <div className={styles.twoColumn}>
        <section className={styles.block}>
          <h2>Difficulty mix</h2>
          <p>{health.difficulty_contract}</p>
          <div className={styles.difficultyGrid}>
            {(["easy", "medium", "hard", "unmeasured"] as const).map((name) => (
              <div className={styles.difficulty} key={name}>
                <span>{name}</span>
                <strong>{view.scope.difficulty[name] ?? 0}</strong>
              </div>
            ))}
          </div>
          <div className={tableStyles.wrap}>
            <table className={tableStyles.table}>
              <thead><tr><th>Tool</th><th>Easy semantic</th><th>Medium</th><th>Hard</th></tr></thead>
              <tbody>
                {tools.map((toolName) => (
                  <tr key={toolName}>
                    <td>{toolName}</td>
                    {(["easy", "medium", "hard"] as const).map((bucket) => {
                      const row = view.by_decompiler[toolName].by_difficulty[bucket];
                      return <td key={bucket}>{row?.semantic_perfect ?? 0}/{row?.rows ?? 0}</td>;
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className={styles.block}>
          <h2>Pipeline health</h2>
          <p>Source and decompiled CFG extraction are separate so parser loss cannot masquerade as tool quality.</p>
          <dl className={styles.pipelineList}>
            <div><dt>Source CFG</dt><dd>{source.available}/{source.subjects} ({percent(source.rate)})</dd></div>
            <div><dt>Source basis</dt><dd>{Object.entries(source.by_basis).map(([name, count]) => `${name} ${count}`).join(" · ") || "—"}</dd></div>
            <div><dt>Oracle</dt><dd>{oracle.tested}/{oracle.attempted} tested · {oracle.no_wrapper} no wrapper</dd></div>
          </dl>
          <div className={tableStyles.wrap}>
            <table className={tableStyles.table}>
              <thead><tr><th>Tool</th><th className={tableStyles.num}>Output CFG</th></tr></thead>
              <tbody>
                {tools.map((toolName) => {
                  const cfg = view.pipeline.decompiled_cfg[toolName];
                  return <tr key={toolName}><td>{toolName}</td><td className={tableStyles.num}>{cfg.available}/{cfg.attempted} · {percent(cfg.rate)}</td></tr>;
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <div className={styles.twoColumn}>
        <section className={styles.block}>
          <h2>Failure causes</h2>
          <p>Exclusive row taxonomy; successful rows are omitted from the cause list.</p>
          <div className={tableStyles.wrap}>
            <table className={tableStyles.table}>
              <thead><tr><th>Tool</th><th>Non-zero causes</th></tr></thead>
              <tbody>
                {tools.map((toolName) => {
                  const failures = Object.entries(view.by_decompiler[toolName].failures)
                    .filter(([name, count]) => name !== "ok" && count > 0)
                    .map(([name, count]) => `${name} ${count}`)
                    .join(" · ");
                  return <tr key={toolName}><td>{toolName}</td><td className={tableStyles.tax}>{failures || "none"}</td></tr>;
                })}
              </tbody>
            </table>
          </div>
        </section>

        <section className={styles.block}>
          <h2>Execution cost</h2>
          <p>{health.cost_contract}</p>
          <div className={tableStyles.wrap}>
            <table className={tableStyles.table}>
              <thead><tr><th>Tool</th><th className={tableStyles.num}>Mean</th><th className={tableStyles.num}>p50</th><th className={tableStyles.num}>p95</th><th className={tableStyles.num}>Total</th><th className={tableStyles.num}>USD</th></tr></thead>
              <tbody>
                {tools.map((toolName) => {
                  const cost = view.by_decompiler[toolName].cost;
                  return <tr key={toolName}><td>{toolName}</td><td className={tableStyles.num}>{millis(cost.mean_ms)}</td><td className={tableStyles.num}>{millis(cost.p50_ms)}</td><td className={tableStyles.num}>{millis(cost.p95_ms)}</td><td className={tableStyles.num}>{millis(cost.total_ms)}</td><td className={tableStyles.num}>{cost.usd == null ? "N/A" : `$${cost.usd.toFixed(4)}`}</td></tr>;
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </>
  );
}

function ScopeTile({ label, value, hint }: { label: string; value: string; hint: string }) {
  return <div className={styles.tile}><span>{label}</span><strong>{value}</strong><small>{hint}</small></div>;
}
