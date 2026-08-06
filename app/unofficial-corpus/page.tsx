import { SiteChrome } from "@/components/SiteChrome";
import { UnavailableData } from "@/components/UnavailableData";
import {
  getLatestUnofficialCorpus,
  getUnofficialCorpusHistory,
} from "@/lib/unofficial-corpus";
import tableStyles from "@/components/SummaryTable.module.css";
import styles from "../dashboard.module.css";

export const revalidate = 900;

export const metadata = {
  title: "Unofficial corpus · DecBench scale",
  description:
    "Non-ranking DecBench-scale coverage, CFG, type, recompilation, and runtime diagnostics.",
};

function integer(value: number | null | undefined): string {
  return value == null ? "—" : Math.round(value).toLocaleString("en-US");
}

function percent(value: number | null | undefined): string {
  return value == null ? "—" : `${(value * 100).toFixed(1)}%`;
}

function milliseconds(value: number | null | undefined): string {
  if (value == null) return "—";
  return value >= 1000 ? `${(value / 1000).toFixed(2)}s` : `${Math.round(value)}ms`;
}

function duration(value: number | null | undefined): string {
  if (value == null) return "—";
  const hours = value / 3_600_000;
  return hours >= 1 ? `${hours.toFixed(1)}h` : `${(value / 60_000).toFixed(1)}m`;
}

function hostLabel(host: Record<string, unknown>): string {
  const machine = String(host.machine || "unknown");
  const processor = String(host.processor || machine);
  const cpu = Number(host.cpu_count || 0);
  const memory = Number(host.memory_bytes || 0);
  const memoryGiB = memory > 0 ? `${(memory / 1024 ** 3).toFixed(1)} GiB` : "unknown memory";
  return `${String(host.system || "unknown")} · ${processor} (${machine}) · ${cpu || "?"} CPU · ${memoryGiB}`;
}

export default async function UnofficialCorpusPage() {
  const [data, history] = await Promise.all([
    getLatestUnofficialCorpus(),
    getUnofficialCorpusHistory(),
  ]);

  return (
    <SiteChrome
      active="unofficial-corpus"
      subtitle="DecBench scale — release-linked local measurement, CI-verified, never ranking"
    >
      <div className={`${styles.frame} ${styles.frameUnofficial}`}>
        <div className={styles.frameTitle}>Unofficial corpus · DecBench scale</div>
        <p className={styles.frameBody}>
          Tens of thousands of real-project functions stress coverage and
          structural recovery. This surface has <strong>no executable semantic
          oracle</strong>, never changes the official ranking, and accepts data
          only after CI verifies the local result against the pinned dataset and
          current Fission release.
        </p>
        <p className={styles.frameNote}>
          Non-ranking evidence: output coverage · CFG GED · DWARF type match ·
          recompilation · latency · failure taxonomy.
        </p>
      </div>

      {!data ? (
        <section className={styles.section}>
          <UnavailableData
            title="No verified unofficial-corpus result yet"
            detail="Run the full DecBench scale profile locally, upload the compressed envelope, and let the publication workflow verify and aggregate it. Official benchmark data remains available on the other tabs."
          />
        </section>
      ) : (
        <>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Latest verified snapshot</h2>
            <div className={styles.tileGrid}>
              <div className={styles.tile}>
                <div className={styles.tileLabel}>Fission release</div>
                <div className={styles.tileValue}>{data.run.fission_version}</div>
                <div className={styles.tileSub}>release binary only</div>
              </div>
              <div className={styles.tile}>
                <div className={styles.tileLabel}>Subjects</div>
                <div className={styles.tileValue}>{integer(data.matrix.subjects)}</div>
                <div className={styles.tileSub}>{integer(data.corpus.selected_binaries)} binaries</div>
              </div>
              <div className={styles.tile}>
                <div className={styles.tileLabel}>Matrix completion</div>
                <div className={styles.tileValue}>{percent(data.matrix.completion_rate)}</div>
                <div className={styles.tileSub}>{integer(data.matrix.observed_rows)} rows</div>
              </div>
              <div className={styles.tile}>
                <div className={styles.tileLabel}>Published source CFG</div>
                <div className={styles.tileValue}>{percent(data.corpus.source_cfg_coverage)}</div>
                <div className={styles.tileSub}>{integer(data.corpus.source_cfg_functions)} functions</div>
              </div>
              <div className={styles.tile}>
                <div className={styles.tileLabel}>Wall duration</div>
                <div className={styles.tileValue}>{duration(data.run.duration_ms)}</div>
                <div className={styles.tileSub}>checkpoint-resumable local run</div>
              </div>
            </div>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Decompiler diagnostics</h2>
            <p className={styles.sectionLead}>
              A lower GED is better; type and recompilation scores are better
              when higher. Untested rows remain outside each metric denominator.
            </p>
            <div className={tableStyles.wrap}>
              <table className={tableStyles.table}>
                <thead>
                  <tr>
                    <th>Decompiler</th>
                    <th className={tableStyles.num}>Output clean</th>
                    <th className={tableStyles.num}>Mean / p95</th>
                    <th className={tableStyles.num}>CFG tested</th>
                    <th className={tableStyles.num}>Mean GED</th>
                    <th className={tableStyles.num}>Type tested / mean</th>
                    <th className={tableStyles.num}>Recompile tested / mean</th>
                  </tr>
                </thead>
                <tbody>
                  {data.matrix.decompilers.map((name) => {
                    const tool = data.by_decompiler[name];
                    if (!tool) return null;
                    return (
                      <tr key={name} className={name === "fission" ? tableStyles.fissionRow : undefined}>
                        <td><strong>{name}</strong></td>
                        <td className={tableStyles.num}>
                          {percent(tool.clean_rate)} ({integer(tool.clean_rows)}/{integer(tool.attempted_rows)})
                        </td>
                        <td className={tableStyles.num}>
                          {milliseconds(tool.latency_ms.mean)} / {milliseconds(tool.latency_ms.p95)}
                        </td>
                        <td className={tableStyles.num}>{integer(tool.ged.tested_rows)}</td>
                        <td className={tableStyles.num}>{tool.ged.mean?.toFixed(3) ?? "—"}</td>
                        <td className={tableStyles.num}>
                          {integer(tool.type_match.tested_rows)} / {tool.type_match.mean?.toFixed(3) ?? "—"}
                        </td>
                        <td className={tableStyles.num}>
                          {integer(tool.recompilation.tested_rows)} / {tool.recompilation.mean?.toFixed(3) ?? "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Failure taxonomy</h2>
            <div className={tableStyles.wrap}>
              <table className={tableStyles.table}>
                <thead>
                  <tr>
                    <th>Decompiler</th>
                    <th>Category</th>
                    <th className={tableStyles.num}>Rows</th>
                  </tr>
                </thead>
                <tbody>
                  {data.matrix.decompilers.flatMap((name) =>
                    Object.entries(data.by_decompiler[name]?.failures || {}).map(
                      ([category, rows]) => (
                        <tr key={`${name}-${category}`}>
                          <td>{name}</td>
                          <td><code>{category}</code></td>
                          <td className={tableStyles.num}>{integer(rows)}</td>
                        </tr>
                      ),
                    ),
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Largest projects</h2>
            <div className={tableStyles.wrap}>
              <table className={tableStyles.table}>
                <thead>
                  <tr>
                    <th>Project</th>
                    <th className={tableStyles.num}>Subjects</th>
                    <th className={tableStyles.num}>Rows</th>
                    <th className={tableStyles.num}>Output clean</th>
                  </tr>
                </thead>
                <tbody>
                  {data.projects.slice(0, 20).map((project) => (
                    <tr key={project.project}>
                      <td><code>{project.project}</code></td>
                      <td className={tableStyles.num}>{integer(project.subjects)}</td>
                      <td className={tableStyles.num}>{integer(project.rows)}</td>
                      <td className={tableStyles.num}>{percent(project.clean_rate)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Provenance</h2>
            <div className={styles.frame}>
              <p className={styles.frameBody}>
                <strong>Dataset:</strong> {data.corpus.repository} · {data.corpus.config} · revision <code>{data.corpus.revision.slice(0, 12)}</code><br />
                <strong>Host:</strong> {hostLabel(data.toolchain.host)}<br />
                <strong>Measured:</strong> {new Date(data.run.finished_at).toLocaleString("en-US", { timeZone: "UTC", timeZoneName: "short" })}<br />
                <strong>Runner:</strong> <code>{data.run.runner_commit.slice(0, 12)}</code> · run <code>{data.run.run_id}</code><br />
                <strong>Source evidence:</strong> <code>{data.publication.source_asset}</code> · SHA-256 <code>{data.publication.source_sha256.slice(0, 16)}…</code>
              </p>
            </div>
          </section>
        </>
      )}

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Verified history</h2>
        {history.length === 0 ? (
          <p className={styles.sectionLead}>No unofficial release snapshots have been published yet.</p>
        ) : (
          <div className={tableStyles.wrap}>
            <table className={tableStyles.table}>
              <thead>
                <tr>
                  <th>Release</th>
                  <th>Measured</th>
                  <th className={tableStyles.num}>Subjects</th>
                  <th className={tableStyles.num}>Rows</th>
                  <th>Run</th>
                </tr>
              </thead>
              <tbody>
                {history.map((entry) => (
                  <tr key={entry.run_id}>
                    <td><strong>{entry.version}</strong></td>
                    <td>{new Date(entry.finished_at).toLocaleDateString("en-US", { timeZone: "UTC" })}</td>
                    <td className={tableStyles.num}>{integer(entry.subjects)}</td>
                    <td className={tableStyles.num}>{integer(entry.rows)}</td>
                    <td><code>{entry.run_id.slice(0, 12)}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </SiteChrome>
  );
}
