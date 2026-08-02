import { Suspense } from "react";
import { SiteChrome } from "@/components/SiteChrome";
import { ValidityBanner } from "@/components/ValidityBanner";
import { UnavailableData } from "@/components/UnavailableData";
import {
  MetaStrip,
  SkeletonMeta,
  SkeletonSection,
} from "@/components/DashboardShared";
import {
  getLatestBenchmarkOptional,
  extractQualityExtensions,
  buildReadabilityDiagnostics,
  groupByDecompiler,
} from "@/lib/benchmark";
import { ReadabilityDiagnosticsPanel } from "@/components/ReadabilityDiagnosticsPanel";
import styles from "../dashboard.module.css";
import tableStyles from "@/components/SummaryTable.module.css";

export const revalidate = 900;

export const metadata = {
  title: "Quality extensions · Diagnostics",
  description:
    "Bare-compile rate, readability proxies, and track/ISA pivots — non-ranking diagnostics.",
};

async function BannerSection() {
  const data = await getLatestBenchmarkOptional();
  if (!data) return null;
  return <ValidityBanner validity={data.validity} run={data.run} />;
}

function RateCell({ value }: { value: number | null | undefined }) {
  if (value == null || Number.isNaN(value)) return <span>—</span>;
  return <span>{(value * 100).toFixed(1)}%</span>;
}

async function QualitySection() {
  const data = await getLatestBenchmarkOptional();
  if (!data) {
    return (
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Quality extensions</h2>
        <UnavailableData />
      </section>
    );
  }

  const ext = extractQualityExtensions(data);
  const typeMatchStats = groupByDecompiler(data).filter((s) => s.typeMatchTestedRows > 0);
  const bareTools = Object.keys(ext.bareByDecompiler).sort((a, b) => {
    if (a === "fission") return -1;
    if (b === "fission") return 1;
    if (a === "ghidra") return -1;
    if (b === "ghidra") return 1;
    return a.localeCompare(b);
  });
  const readStats = buildReadabilityDiagnostics(data);
  const tracks = Object.keys(ext.byTrack);
  const languages = Object.keys(ext.byLanguage);
  const isas = Object.keys(ext.byIsa);
  const formats = Object.keys(ext.byFormat);
  const opts = Object.keys(ext.byOpt);

  return (
    <>
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Non-ranking diagnostics</h2>
        <p className={styles.sectionLead}>
          Semantic pass rate on the <strong>original_binary</strong> / native
          oracle remains the only ranking axis (core C PE headline). The tables
          below are form quality, readability proxies, and{" "}
          <strong>language · ISA · format · opt</strong> pivots for multi-corpus
          investigation only.
        </p>
        <div className={styles.frame}>
          <div className={styles.frameTitle}>Policy</div>
          <p className={styles.frameBody}>
            Bare-compile uses minimal headers + <code>gcc -c</code>. Readability
            reports source similarity, AST tree-edit similarity, proxy score,
            generic naming, goto / nest / temp / flag density. For Fission,
            semantic rows use NIR; readability proxies prefer HIR when dual
            layers are present. ELF uses host/qemu recompile ABI (not wine).
            Study pack: <code>benchmark/readability/</code>.
          </p>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>EXT · Bare-compile rate</h2>
        {bareTools.length === 0 ? (
          <p className={styles.sectionLead}>
            No bare-compile field on this envelope yet (re-run runner after the
            quality-extensions ship).
          </p>
        ) : (
          <div className={tableStyles.wrap}>
            <table className={tableStyles.table}>
              <thead>
                <tr>
                  <th>Decompiler</th>
                  <th>Attempted</th>
                  <th>OK</th>
                  <th>Fail</th>
                  <th>OK rate</th>
                </tr>
              </thead>
              <tbody>
                {bareTools.map((tool) => {
                  const row = ext.bareByDecompiler[tool] || {};
                  return (
                    <tr
                      key={tool}
                      className={
                        tool === "fission" ? tableStyles.fissionRow : undefined
                      }
                    >
                      <td>{tool}</td>
                      <td className={tableStyles.num}>{row.attempted ?? "—"}</td>
                      <td className={tableStyles.num}>{row.ok ?? "—"}</td>
                      <td className={tableStyles.num}>{row.fail ?? "—"}</td>
                      <td className={tableStyles.num}>
                        <RateCell value={row.ok_rate as number | null} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>EXT · Type correctness (DWARF)</h2>
        <p className={styles.sectionLead}>
          Recovered variable types checked against the DWARF debug info baked
          into each corpus binary (rows without ground truth — no debug info,
          or no matched function — are excluded rather than counted as a
          miss). Diagnostic evidence only, not a ranking axis.
        </p>
        {typeMatchStats.length === 0 ? (
          <p className={styles.sectionLead}>
            No type_match field on this envelope yet (re-run the runner after
            the type_match metric ship).
          </p>
        ) : (
          <div className={tableStyles.wrap}>
            <table className={tableStyles.table}>
              <thead>
                <tr>
                  <th>Decompiler</th>
                  <th className={tableStyles.num}>Tested</th>
                  <th>Mean accuracy</th>
                  <th className={tableStyles.num}>Perfect</th>
                </tr>
              </thead>
              <tbody>
                {typeMatchStats.map((s) => (
                  <tr
                    key={s.decompiler}
                    className={
                      s.decompiler === "fission" ? tableStyles.fissionRow : undefined
                    }
                  >
                    <td>{s.decompiler}</td>
                    <td className={tableStyles.num}>{s.typeMatchTestedRows}</td>
                    <td>
                      <RateCell value={s.meanTypeMatch} />
                    </td>
                    <td className={tableStyles.num}>{s.typeMatchPerfectRows}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          EXT · Readability · source sim · AST
        </h2>
        <ReadabilityDiagnosticsPanel
          stats={readStats}
          compact={false}
          showStudyNote
        />
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          EXT · Language · ISA · format · opt
        </h2>
        {tracks.length === 0 &&
        languages.length === 0 &&
        isas.length === 0 ? (
          <p className={styles.sectionLead}>
            No language/ISA pivot data on this envelope. Re-run multi-decomp
            after the multi-corpus track ship.
          </p>
        ) : (
          <>
            {languages.length > 0 ? (
              <div className={tableStyles.wrap}>
                <h3 className={styles.sectionTitle}>By language</h3>
                <table className={tableStyles.table}>
                  <thead>
                    <tr>
                      <th>Language</th>
                      <th>Rows</th>
                      <th>Tested</th>
                      <th>Mean pass</th>
                      <th>Perfect</th>
                      <th>Timeouts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {languages.map((name) => {
                      const row = ext.byLanguage[name] || {};
                      return (
                        <tr key={name}>
                          <td>
                            <code>{name}</code>
                          </td>
                          <td className={tableStyles.num}>{row.rows ?? "—"}</td>
                          <td className={tableStyles.num}>
                            {row.semantic_tested ?? "—"}
                          </td>
                          <td className={tableStyles.num}>
                            <RateCell
                              value={row.mean_pass_rate as number | null}
                            />
                          </td>
                          <td className={tableStyles.num}>
                            {row.perfect_rows ?? "—"}
                          </td>
                          <td className={tableStyles.num}>
                            {row.timeout_rows ?? "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : null}
            {tracks.length > 0 ? (
              <div className={tableStyles.wrap}>
                <h3 className={styles.sectionTitle}>By track</h3>
                <table className={tableStyles.table}>
                  <thead>
                    <tr>
                      <th>Track</th>
                      <th>Rows</th>
                      <th>Tested</th>
                      <th>Mean pass</th>
                      <th>Perfect</th>
                      <th>Timeouts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tracks.map((name) => {
                      const row = ext.byTrack[name] || {};
                      return (
                        <tr key={name}>
                          <td>{name}</td>
                          <td className={tableStyles.num}>{row.rows ?? "—"}</td>
                          <td className={tableStyles.num}>
                            {row.semantic_tested ?? "—"}
                          </td>
                          <td className={tableStyles.num}>
                            <RateCell
                              value={row.mean_pass_rate as number | null}
                            />
                          </td>
                          <td className={tableStyles.num}>
                            {row.perfect_rows ?? "—"}
                          </td>
                          <td className={tableStyles.num}>
                            {row.timeout_rows ?? "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : null}
            {isas.length > 0 ? (
              <div className={tableStyles.wrap}>
                <h3 className={styles.sectionTitle}>By ISA</h3>
                <table className={tableStyles.table}>
                  <thead>
                    <tr>
                      <th>ISA</th>
                      <th>Rows</th>
                      <th>Mean pass</th>
                      <th>Timeouts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {isas.map((name) => {
                      const row = ext.byIsa[name] || {};
                      return (
                        <tr key={name}>
                          <td>
                            <code>{name}</code>
                          </td>
                          <td className={tableStyles.num}>{row.rows ?? "—"}</td>
                          <td className={tableStyles.num}>
                            <RateCell
                              value={row.mean_pass_rate as number | null}
                            />
                          </td>
                          <td className={tableStyles.num}>
                            {row.timeout_rows ?? "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : null}
            {formats.length > 0 ? (
              <div className={tableStyles.wrap}>
                <h3 className={styles.sectionTitle}>By format</h3>
                <table className={tableStyles.table}>
                  <thead>
                    <tr>
                      <th>Format</th>
                      <th>Rows</th>
                      <th>Mean pass</th>
                    </tr>
                  </thead>
                  <tbody>
                    {formats.map((name) => {
                      const row = ext.byFormat[name] || {};
                      return (
                        <tr key={name}>
                          <td>
                            <code>{name}</code>
                          </td>
                          <td className={tableStyles.num}>{row.rows ?? "—"}</td>
                          <td className={tableStyles.num}>
                            <RateCell
                              value={row.mean_pass_rate as number | null}
                            />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : null}
            {opts.length > 0 ? (
              <div className={tableStyles.wrap}>
                <h3 className={styles.sectionTitle}>By opt</h3>
                <table className={tableStyles.table}>
                  <thead>
                    <tr>
                      <th>Opt</th>
                      <th>Rows</th>
                      <th>Tested</th>
                      <th>Mean pass</th>
                      <th>Perfect</th>
                    </tr>
                  </thead>
                  <tbody>
                    {opts.map((name) => {
                      const row = ext.byOpt[name] || {};
                      return (
                        <tr key={name}>
                          <td>
                            <code>{name}</code>
                          </td>
                          <td className={tableStyles.num}>{row.rows ?? "—"}</td>
                          <td className={tableStyles.num}>
                            {row.semantic_tested ?? "—"}
                          </td>
                          <td className={tableStyles.num}>
                            <RateCell
                              value={row.mean_pass_rate as number | null}
                            />
                          </td>
                          <td className={tableStyles.num}>
                            {row.perfect_rows ?? "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : null}
          </>
        )}
      </section>
    </>
  );
}

export default function QualityPage() {
  return (
    <SiteChrome
      active="quality"
      subtitle="Quality extensions — diagnostics only, never ranking"
    >
      <Suspense fallback={<SkeletonMeta />}>
        <BannerSection />
      </Suspense>
      <Suspense fallback={<SkeletonMeta />}>
        <MetaStrip />
      </Suspense>
      <Suspense fallback={<SkeletonSection />}>
        <QualitySection />
      </Suspense>
    </SiteChrome>
  );
}
