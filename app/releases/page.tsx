import { Suspense } from "react";
import { SiteChrome } from "@/components/SiteChrome";
import { UnavailableData } from "@/components/UnavailableData";
import { SkeletonSection } from "@/components/DashboardShared";
import { ReleaseComparisonPanel } from "@/components/ReleaseComparisonPanel";
import { VersionTrendChart } from "@/components/VersionTrendChart";
import { getLatestBenchmarkOptional } from "@/lib/benchmark";
import { getReleaseComparison, getVersionTrend } from "@/lib/history";
import styles from "../dashboard.module.css";

export const revalidate = 900;

export const metadata = {
  title: "Releases · What changed",
  description:
    "Fission quality, latency, paired speedup, CPU, and memory trends across releases.",
};

async function ComparisonSection() {
  const data = await getLatestBenchmarkOptional();
  if (!data) return <UnavailableData title="Release comparison unavailable" />;
  const comparison = await getReleaseComparison(data);
  if (!comparison) {
    return (
      <p className={styles.sectionLead}>
        No comparable official release pair is archived yet. Diagnostic/smoke
        snapshots are intentionally excluded from release-over-release deltas.
      </p>
    );
  }
  return <ReleaseComparisonPanel comparison={comparison} />;
}

async function TrendSection() {
  const points = await getVersionTrend();
  return <VersionTrendChart points={points} />;
}

export default function ReleasesPage() {
  return (
    <SiteChrome active="releases" subtitle="Release-over-release — Fission's own trend, not a re-ranking">
      <div className={styles.frame}>
        <div className={styles.frameTitle}>Releases</div>
        <p className={styles.frameBody}>
          Archives are keyed by <code>toolchain.fission_version</code>, but an
          archived file is not automatically an official measurement. The
          canonical trend includes only valid, publishable, official envelopes
          with the same benchmark contract. Smoke snapshots remain visible for
          engineering history as dashed lines, never as an official claim.
        </p>
      </div>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Quality and performance by release</h2>
        <p className={styles.sectionLead}>
          Semantic quality is a guardrail, not the whole story. The dashboard
          also tracks Fission mean/P50/P95 latency, paired speedup, cold/warm
          trials, CPU, and memory. Contract changes and missing releases break
          the relevant line instead of being interpolated.
        </p>
        <Suspense fallback={<SkeletonSection rows={4} />}>
          <TrendSection />
        </Suspense>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Latest release vs. previous</h2>
        <Suspense fallback={<SkeletonSection rows={5} />}>
          <ComparisonSection />
        </Suspense>
      </section>
    </SiteChrome>
  );
}
