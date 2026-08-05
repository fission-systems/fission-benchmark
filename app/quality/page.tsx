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

function DistanceCell({ value }: { value: number | null | undefined }) {
  if (value == null || Number.isNaN(value)) return <span>—</span>;
  return <span>{value.toFixed(2)}</span>;
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
  const gedStats = groupByDecompiler(data).filter((s) => s.gedTestedRows > 0);
  const bareTools = Object.keys(ext.bareByDecompiler).sort((a, b) => {
    if (a === "fission") return -1;
    if (b === "fission") return 1;
    if (a === "ghidra") return -1;
    if (b === "ghidra") return 1;
    return a.localeCompare(b);
  });
  const recompilationTools = Object.keys(ext.recompilationByDecompiler).sort(
    (a, b) => {
      if (a === "fission") return -1;
      if (b === "fission") return 1;
      if (a === "ghidra") return -1;
      if (b === "ghidra") return 1;
      return a.localeCompare(b);
    },
  );
  const readStats = buildReadabilityDiagnostics(data);
  const tracks = Object.keys(ext.byTrack);
  const languages = Object.keys(ext.byLanguage);
  const isas = Object.keys(ext.byIsa);
  const formats = Object.keys(ext.byFormat);
  const opts = Object.keys(ext.byOpt);
  const gedProvenance = data.rows.reduce(
    (counts, row) => {
      const basis = String(row.ged_metadata?.source_basis ?? "missing");
      if (basis === "preprocessed_tu") counts.preprocessed += 1;
      else if (basis === "authored_source_fallback") counts.fallback += 1;
      else counts.missing += 1;
      return counts;
    },
    { preprocessed: 0, fallback: 0, missing: 0 },
  );
  const sourceCfgContract =
    data.run.measurement_contracts?.source_cfg ?? "legacy / unstamped";

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
        <div className={styles.frame}>
          <div className={styles.frameTitle}>Re-evaluation provenance</div>
          <p className={styles.frameBody}>
            Source-CFG contract: <code>{sourceCfgContract}</code>. Compiler-matched
            preprocessed TU rows: <strong>{gedProvenance.preprocessed}</strong>;
            authored-source fallback: <strong>{gedProvenance.fallback}</strong>;
            missing provenance: <strong>{gedProvenance.missing}</strong>. Official
            releases publish binaries, decompiler rows, expected cells, and
            serialized source CFGs in the eval kit. {" "}
            <a href="/eval-kit-latest.json">Open latest eval-kit index →</a>
          </p>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          EXT · Recompilation bytematch
        </h2>
        <p className={styles.sectionLead}>
          Decompiled C is rebuilt for the original PE/ELF ABI with the matching
          compiler family and optimization level, then compared as ordered,
          relocation-normalized assembly. Missing peer measurements stay in the
          shared denominator. This is diagnostic evidence, not a ranking axis.
        </p>
        {recompilationTools.length === 0 ? (
          <p className={styles.sectionLead}>
            No recompilation field on this envelope yet. It will appear after
            the next official benchmark publishes.
          </p>
        ) : (
          <div className={tableStyles.wrap}>
            <table className={tableStyles.table}>
              <thead>
                <tr>
                  <th>Decompiler</th>
                  <th className={tableStyles.num}>Observed / shared</th>
                  <th className={tableStyles.num}>Compilable</th>
                  <th>Observed mean</th>
                  <th>Exact / shared</th>
                </tr>
              </thead>
              <tbody>
                {recompilationTools.map((tool) => {
                  const row = ext.recompilationByDecompiler[tool] || {};
                  return (
                    <tr
                      key={tool}
                      className={
                        tool === "fission" ? tableStyles.fissionRow : undefined
                      }
                    >
                      <td>{tool}</td>
                      <td className={tableStyles.num}>
                        {row.observed_rows ?? "—"} / {row.shared_rows ?? "—"}
                      </td>
                      <td className={tableStyles.num}>
                        {row.compilable_rows ?? "—"}
                      </td>
                      <td><RateCell value={row.mean_similarity} /></td>
                      <td className={tableStyles.num}>
                        {row.perfect_rows ?? "—"} / {row.shared_rows ?? "—"}{" "}
                        (<RateCell value={row.perfect_rate} />)
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
          into each corpus binary. Mean accuracy describes observed rows;
          perfect rate uses the shared subject denominator, so a peer-measurable
          missing row is not hidden. Diagnostic evidence only, not ranking.
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
                  <th className={tableStyles.num}>Observed / shared</th>
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
                    <td className={tableStyles.num}>
                      {s.typeMatchTestedRows} / {s.typeMatchSharedRows}
                    </td>
                    <td>
                      <RateCell value={s.meanTypeMatch} />
                    </td>
                    <td className={tableStyles.num}>
                      {s.typeMatchPerfectRows} / {s.typeMatchSharedRows}{" "}
                      (<RateCell value={s.typeMatchPerfectRate} />)
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>EXT · Structural correctness (GED)</h2>
        <p className={styles.sectionLead}>
          Graph edit distance between the decompiled function&apos;s control-flow
          graph and the exact compiler-variant preprocessed TU&apos;s CFG (both
          parsed with Joern for structural comparability). Lower is better — 0.0
          means the control-flow shape matches exactly. Mean GED describes
          observed rows; exact-match rate uses the shared subject denominator.
          Diagnostic evidence only, not a ranking axis.
        </p>
        {gedStats.length === 0 ? (
          <p className={styles.sectionLead}>
            No ged field on this envelope yet (re-run the runner after the GED
            metric ship).
          </p>
        ) : (
          <div className={tableStyles.wrap}>
            <table className={tableStyles.table}>
              <thead>
                <tr>
                  <th>Decompiler</th>
                  <th className={tableStyles.num}>Observed / shared</th>
                  <th>Mean GED</th>
                  <th className={tableStyles.num}>Exact match (GED=0)</th>
                </tr>
              </thead>
              <tbody>
                {gedStats.map((s) => (
                  <tr
                    key={s.decompiler}
                    className={
                      s.decompiler === "fission" ? tableStyles.fissionRow : undefined
                    }
                  >
                    <td>{s.decompiler}</td>
                    <td className={tableStyles.num}>
                      {s.gedTestedRows} / {s.gedSharedRows}
                    </td>
                    <td>
                      <DistanceCell value={s.meanGed} />
                    </td>
                    <td className={tableStyles.num}>
                      {s.gedPerfectRows} / {s.gedSharedRows}{" "}
                      (<RateCell value={s.gedPerfectRate} />)
                    </td>
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
