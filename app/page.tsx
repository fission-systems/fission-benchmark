import { Suspense } from "react";
import Link from "next/link";
import {
  getLatestBenchmarkOptional,
  groupByDecompiler,
  buildReadabilityDiagnostics,
  extractQualityExtensions,
  pct,
} from "@/lib/benchmark";
import { SiteChrome } from "@/components/SiteChrome";
import { ValidityBanner } from "@/components/ValidityBanner";
import { SummaryTable } from "@/components/SummaryTable";
import { UnavailableData } from "@/components/UnavailableData";
import { ReadabilityDiagnosticsPanel } from "@/components/ReadabilityDiagnosticsPanel";
import {
  MetaStrip,
  SameFunctionOverviewTiles,
  SkeletonMeta,
  SkeletonSection,
} from "@/components/DashboardShared";
import tableStyles from "@/components/SummaryTable.module.css";
import styles from "./dashboard.module.css";

export const revalidate = 900;

export const metadata = {
  title: "Overview · Multi-decompiler quality",
  description:
    "Fission multi-decompiler semantic ranking, coverage, and navigation hub.",
};

async function BannerSection() {
  const data = await getLatestBenchmarkOptional();
  if (!data) return null;
  return <ValidityBanner validity={data.validity} run={data.run} />;
}

async function SummarySection() {
  const data = await getLatestBenchmarkOptional();
  if (!data) {
    return (
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>MVP · Semantic ranking</h2>
        <UnavailableData />
      </section>
    );
  }
  const stats = groupByDecompiler(data);
  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>MVP · Semantic ranking</h2>
      <p className={styles.sectionLead}>
        Only <strong>semantic pass rate</strong> ranks tools. Coverage and fail
        taxonomy keep denominators honest. Drill into same-function, per-function
        code, and compiler variants on dedicated pages.
      </p>
      <SummaryTable stats={stats} />
    </section>
  );
}

export default function Home() {
  return (
    <SiteChrome
      active="overview"
      subtitle="Overview — semantic ranking hub; detail pages keep questions separate"
    >
      <div className={styles.frame}>
        <div className={styles.frameTitle}>Multi-decompiler quality</div>
        <p className={styles.frameBody}>
          Compare <strong>Fission</strong> against open decompilers under an{" "}
          <strong>original_binary</strong> oracle. Ranking axis is semantic pass
          rate only. Boundary honesty, per-function code, compiler pivots, and
          Ghidra IR parity each have their own route.
        </p>
      </div>

      <div className={styles.cardGrid}>
        <Link href="/same-function" className={styles.card}>
          <div className={styles.cardKicker}>MVP-0</div>
          <div className={styles.cardTitle}>Same-function matrix</div>
          <p className={styles.cardBody}>
            Request contract <code>(binary, addr)</code> — did we get that
            function unit?
          </p>
          <div className={styles.cardCta}>Open matrix →</div>
        </Link>
        <Link href="/functions" className={styles.card}>
          <div className={styles.cardKicker}>Browse</div>
          <div className={styles.cardTitle}>Per-function results</div>
          <p className={styles.cardBody}>
            Side-by-side decompiled code grid for every corpus function.
          </p>
          <div className={styles.cardCta}>Open grid →</div>
        </Link>
        <Link href="/nir-vs-hir" className={styles.card}>
          <div className={styles.cardKicker}>Fission layers</div>
          <div className={styles.cardTitle}>Source · NIR · HIR</div>
          <p className={styles.cardBody}>
            Original C next to Fission NIR (semantic) and HIR (readability) —
            dual-layer diagnostic, not ranking.
          </p>
          <div className={styles.cardCta}>Open comparison →</div>
        </Link>
        <Link href="/variants" className={styles.card}>
          <div className={styles.cardKicker}>Extension</div>
          <div className={styles.cardTitle}>Compiler × opt</div>
          <p className={styles.cardBody}>
            Semantic means pivoted by gcc / gcc-m32 and optimization level.
          </p>
          <div className={styles.cardCta}>Open variants →</div>
        </Link>
        <Link href="/quality" className={styles.card}>
          <div className={styles.cardKicker}>Diagnostics</div>
          <div className={styles.cardTitle}>Quality extensions</div>
          <p className={styles.cardBody}>
            Bare-compile rate, readability proxies (goto / temps / flag soup),
            and realworld · multi-ISA track pivots — never ranking.
          </p>
          <div className={styles.cardCta}>Open diagnostics →</div>
        </Link>
        <Link href="/measurement" className={styles.card}>
          <div className={styles.cardKicker}>P2 · Measurement contract</div>
          <div className={styles.cardTitle}>Scope & pipeline health</div>
          <p className={styles.cardBody}>
            Presets, common-denominator normalization, structural difficulty,
            compile/error/cost, and CFG · oracle pipeline health in one view.
          </p>
          <div className={styles.cardCta}>Inspect measurement →</div>
        </Link>
        <Link href="/fission-vs-ghidra" className={styles.card}>
          <div className={styles.cardKicker}>Shared IR</div>
          <div className={styles.cardTitle}>Fission ↔ Ghidra</div>
          <p className={styles.cardBody}>
            Layered parity (asm / p-code / CFG / discovery) — not ranking.
          </p>
          <div className={styles.cardCta}>Open parity →</div>
        </Link>
        <Link href="/hir-vs-ghidra" className={styles.card}>
          <div className={styles.cardKicker}>Readability</div>
          <div className={styles.cardTitle}>HIR vs Ghidra</div>
          <p className={styles.cardBody}>
            Fission&apos;s readable HIR next to Ghidra&apos;s own decompiled
            output, side by side — not ranking.
          </p>
          <div className={styles.cardCta}>Open comparison →</div>
        </Link>
        <Link href="/releases" className={styles.card}>
          <div className={styles.cardKicker}>Trend</div>
          <div className={styles.cardTitle}>Releases</div>
          <p className={styles.cardBody}>
            Fission&apos;s semantic pass rate release over release, plus
            what changed since the last one.
          </p>
          <div className={styles.cardCta}>Open releases →</div>
        </Link>
      </div>

      <Suspense fallback={<SkeletonMeta />}>
        <MetaStrip />
      </Suspense>

      <Suspense fallback={<div className={styles.bannerSkeleton} />}>
        <BannerSection />
      </Suspense>

      <Suspense fallback={<SkeletonSection rows={5} />}>
        <SummarySection />
      </Suspense>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Same-function · snapshot</h2>
        <p className={styles.sectionLead}>
          Core vs multi boundary rates at a glance. Full status table on{" "}
          <Link href="/same-function">Same-function</Link>.
        </p>
        <Suspense fallback={<SkeletonSection rows={2} />}>
          <SameFunctionOverviewTiles />
        </Suspense>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          Diagnostics · language · ISA (non-ranking)
        </h2>
        <p className={styles.sectionLead}>
          Multi-corpus pivots from the latest envelope. Full tables on{" "}
          <Link href="/quality">Quality EXT</Link>. Ranking remains semantic on
          core C PE only.
        </p>
        <Suspense fallback={<SkeletonSection rows={3} />}>
          <CorpusPivotsOverviewSection />
        </Suspense>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Diagnostics · readability (non-ranking)</h2>
        <p className={styles.sectionLead}>
          Source similarity, AST tree-edit proxies, and readability proxies are
          shown here for investigation only — they never rank tools. Per-function
          code detail remains on <Link href="/functions">Functions</Link>.
        </p>
        <Suspense fallback={<SkeletonSection rows={6} />}>
          <ReadabilityOverviewSection />
        </Suspense>
      </section>
    </SiteChrome>
  );
}

async function CorpusPivotsOverviewSection() {
  const data = await getLatestBenchmarkOptional();
  if (!data) return <UnavailableData />;
  const ext = extractQualityExtensions(data);
  const languages = Object.keys(ext.byLanguage);
  const isas = Object.keys(ext.byIsa);
  if (languages.length === 0 && isas.length === 0) {
    return (
      <p className={styles.sectionLead}>
        No language/ISA pivots on this envelope yet.
      </p>
    );
  }
  return (
    <div className={tableStyles.wrap}>
      <table className={tableStyles.table}>
        <thead>
          <tr>
            <th>Pivot</th>
            <th>Key</th>
            <th className={tableStyles.num}>Rows</th>
            <th className={tableStyles.num}>Mean pass</th>
          </tr>
        </thead>
        <tbody>
          {languages.map((name) => {
            const row = ext.byLanguage[name] || {};
            return (
              <tr key={`lang-${name}`}>
                <td>language</td>
                <td>
                  <code>{name}</code>
                </td>
                <td className={tableStyles.num}>{row.rows ?? "—"}</td>
                <td className={tableStyles.num}>
                  {pct(row.mean_pass_rate as number | null | undefined)}
                </td>
              </tr>
            );
          })}
          {isas.map((name) => {
            const row = ext.byIsa[name] || {};
            return (
              <tr key={`isa-${name}`}>
                <td>isa</td>
                <td>
                  <code>{name}</code>
                </td>
                <td className={tableStyles.num}>{row.rows ?? "—"}</td>
                <td className={tableStyles.num}>
                  {pct(row.mean_pass_rate as number | null | undefined)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

async function ReadabilityOverviewSection() {
  const data = await getLatestBenchmarkOptional();
  if (!data) return <UnavailableData />;
  const stats = buildReadabilityDiagnostics(data);
  return <ReadabilityDiagnosticsPanel stats={stats} compact showStudyNote />;
}
