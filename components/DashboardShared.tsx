import {
  getLatestBenchmarkOptional,
  groupByDecompiler,
  getFunctionNames,
  pct,
  getSameFunctionSummary,
} from "@/lib/benchmark";
import styles from "@/app/dashboard.module.css";

// Stable for a server module instance; avoids render-time clock reads while
// still making a statically generated dashboard's age explicit.
const DASHBOARD_RENDERED_AT_MS = Date.now();

export function SkeletonMeta() {
  return (
    <div className={styles.heroMeta}>
      {Array.from({ length: 4 }).map((_, i) => (
        <span key={i} className={`${styles.metaItem} ${styles.skeleton}`}>
          <span className={styles.skeletonLine} style={{ width: 48 }} />
          <span className={styles.skeletonLine} style={{ width: 64 }} />
        </span>
      ))}
    </div>
  );
}

export function SkeletonSection({ rows = 4 }: { rows?: number }) {
  return (
    <section className={styles.section}>
      <div className={`${styles.skeletonLine} ${styles.sectionTitleSkeleton}`} />
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className={`${styles.skeletonLine} ${styles.skeletonRow}`}
        />
      ))}
    </section>
  );
}

export async function MetaStrip() {
  const data = await getLatestBenchmarkOptional();
  if (!data) {
    return (
      <div className={styles.heroMeta}>
        <span className={styles.metaItem}>
          <span className={styles.metaLabel}>Status</span>
          <span className={styles.metaValue}>no publishable run</span>
        </span>
        <span className={styles.metaItem}>
          <span className={styles.metaLabel}>Corpus</span>
          <code className={styles.metaValue}>—</code>
        </span>
        <span className={styles.metaItem}>
          <span className={styles.metaLabel}>Functions</span>
          <span className={styles.metaValue}>—</span>
        </span>
        <span className={styles.metaItem}>
          <span className={styles.metaLabel}>Decompilers</span>
          <span className={styles.metaValue}>—</span>
        </span>
      </div>
    );
  }
  const functionNames = getFunctionNames(data.rows);
  const stats = groupByDecompiler(data);
  const corpus = data.run?.corpus ?? "dev";
  const measuredAt = data.run?.finished_at
    ? new Date(data.run.finished_at).toLocaleString("en-US", {
        timeZone: "UTC",
        timeZoneName: "short",
      })
    : "not recorded";
  const measuredMs = data.run?.finished_at ? Date.parse(data.run.finished_at) : NaN;
  const ageDays = Number.isFinite(measuredMs)
    ? Math.max(0, (DASHBOARD_RENDERED_AT_MS - measuredMs) / 86_400_000)
    : null;
  const freshness = ageDays == null
    ? "age unknown"
    : ageDays > 7
      ? `stale · ${Math.round(ageDays)}d`
      : ageDays > 3
        ? `aging · ${Math.round(ageDays)}d`
        : `fresh · ${Math.max(0, Math.round(ageDays * 24))}h`;
  const publication = data.validity?.publishable && data.run?.official
    ? "official"
    : data.validity?.valid
      ? "smoke / diagnostic"
      : "invalid / unverified";
  const commit = data.run?.runner_commit ?? data.toolchain?.runner_commit;

  return (
    <div className={styles.heroMeta}>
      <span className={styles.metaItem}>
        <span className={styles.metaLabel}>Status</span>
        <span className={styles.metaValue}>{publication} · {freshness}</span>
      </span>
      <span className={styles.metaItem}>
        <span className={styles.metaLabel}>Corpus</span>
        <code className={styles.metaValue}>{corpus}</code>
      </span>
      <span className={styles.metaItem}>
        <span className={styles.metaLabel}>Functions</span>
        <span className={styles.metaValue}>{functionNames.length}</span>
      </span>
      <span className={styles.metaItem}>
        <span className={styles.metaLabel}>Decompilers</span>
        <span className={styles.metaValue}>{stats.length}</span>
      </span>
      <span className={styles.metaItem}>
        <span className={styles.metaLabel}>Measured</span>
        <span className={styles.metaValue}>{measuredAt}</span>
      </span>
      <span className={styles.metaItem}>
        <span className={styles.metaLabel}>Build</span>
        <code className={styles.metaValue}>
          {data.run?.fission_version ?? data.toolchain?.fission_version ?? "?"}
          {commit ? ` @ ${commit.slice(0, 8)}` : " @ ?"}
        </code>
      </span>
    </div>
  );
}

/** Compact same-function cohort tiles for the overview hub. */
export async function SameFunctionOverviewTiles() {
  const data = await getLatestBenchmarkOptional();
  if (!data) {
    return (
      <p className={styles.sectionLead}>
        Same-function snapshot unavailable until a publishable run is published.
      </p>
    );
  }
  const sameFn = getSameFunctionSummary(data);
  if (!sameFn) {
    return (
      <p className={styles.sectionLead}>
        Same-function matrix not in this envelope yet.
      </p>
    );
  }
  return (
    <div className={styles.tileGrid}>
      <div className={`${styles.tile} ${styles.tileFission}`}>
        <div className={styles.tileLabel}>Core same-fn rate</div>
        <div className={styles.tileValue}>{pct(sameFn.coreRate)}</div>
        <div className={styles.tileSub}>
          fission + ghidra · loose {pct(sameFn.coreLoose)}
        </div>
      </div>
      <div className={styles.tile}>
        <div className={styles.tileLabel}>Multi same-fn rate</div>
        <div className={styles.tileValue}>{pct(sameFn.multiRate)}</div>
        <div className={styles.tileSub}>
          other adapters · loose {pct(sameFn.multiLoose)}
        </div>
      </div>
      <div className={styles.tile}>
        <div className={styles.tileLabel}>All · addr anchors</div>
        <div className={styles.tileValue}>{pct(sameFn.allRate)}</div>
        <div className={styles.tileSub}>
          address anchor rate {pct(sameFn.addressAnchorRate)}
        </div>
      </div>
    </div>
  );
}
