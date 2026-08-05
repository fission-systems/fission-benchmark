import type { LoadedParityTelemetry } from "@/lib/parity";
import styles from "./ParityDataStatus.module.css";

function ageLabel(hours: number | null): string {
  if (hours == null) return "unknown";
  if (hours < 1) return `${Math.max(1, Math.round(hours * 60))}m`;
  if (hours < 48) return `${Math.round(hours)}h`;
  return `${Math.round(hours / 24)}d`;
}

function compactSource(source: string): string {
  try {
    return new URL(source, "http://local").pathname;
  } catch {
    return source;
  }
}

export function ParityDataStatus({ state }: { state: LoadedParityTelemetry | null }) {
  if (!state) {
    return (
      <div className={`${styles.panel} ${styles.unknown}`}>
        <div className={styles.heading}><span className={styles.title}>Parity data status</span><span className={styles.badge}>unavailable</span></div>
        <p className={styles.warning}>
          No CFG, P-code, assembly, or function-inventory telemetry is available
          for the latest Fission release. Older and unversioned artifacts are
          intentionally hidden; rerun parity for the current release.
        </p>
      </div>
    );
  }

  const { telemetry, freshness } = state;
  const provenance = telemetry.provenance;
  const sources = provenance?.sources ?? [];
  const freshnessWarning = freshness === "unknown"
    ? "This artifact has no generation timestamp or runner commit. The dashboard cannot prove that these CFG/P-code results are current; rerun parity to publish a v3 artifact."
    : freshness === "stale"
      ? "This parity artifact is older than the freshness window. Treat the metrics as historical until parity is rerun."
      : freshness === "aging"
        ? "This parity artifact is approaching the freshness limit."
        : "Artifact provenance is present and the result is inside the freshness window.";
  const commit = provenance?.runner_commit?.slice(0, 12) ?? "not recorded";
  const coverage = telemetry.publishable?.usable_coverage;
  const fetchErrorRate = telemetry.reliability?.fetch_error_rate;
  const reliable = coverage != null && coverage >= 0.9 && (fetchErrorRate ?? 1) <= 0.1;
  const reliabilityWarning = reliable
    ? ""
    : `Current telemetry is incomplete: primary coverage ${coverage == null ? "unknown" : `${(coverage * 100).toFixed(1)}%`}, fetch errors ${fetchErrorRate == null ? "unknown" : `${(fetchErrorRate * 100).toFixed(1)}%`}. Do not publish these rates.`;
  const warning = [freshnessWarning, reliabilityWarning].filter(Boolean).join(" ");

  return (
    <div className={`${styles.panel} ${styles[freshness]}`}>
      <div className={styles.heading}>
        <span className={styles.title}>Parity data status</span>
        <span className={styles.badge}>{freshness}{reliable ? "" : " · incomplete"}</span>
      </div>
      <p className={styles.warning}>{warning}</p>
      <div className={styles.grid}>
        <div className={styles.item}><span className={styles.label}>Generated</span><span className={styles.value}>{state.generatedAt ? new Date(state.generatedAt).toLocaleString("en-US", { timeZone: "UTC", timeZoneName: "short" }) : "not recorded"}</span></div>
        <div className={styles.item}><span className={styles.label}>Oldest input</span><span className={styles.value}>{state.measuredAt ? new Date(state.measuredAt).toLocaleString("en-US", { timeZone: "UTC", timeZoneName: "short" }) : "not recorded"}</span></div>
        <div className={styles.item}><span className={styles.label}>Age</span><span className={styles.value}>{ageLabel(state.ageHours)}</span></div>
        <div className={styles.item}><span className={styles.label}>Runner commit</span><code className={styles.value}>{commit}</code></div>
        <div className={styles.item}><span className={styles.label}>Source</span><code className={styles.value}>{compactSource(state.source)}</code></div>
        <div className={styles.item}><span className={styles.label}>Corpus</span><code className={styles.value}>{provenance?.corpus ?? "not recorded"}</code></div>
        <div className={styles.item}><span className={styles.label}>Fission version</span><code className={styles.value}>{provenance?.tool_versions?.fission ?? "not recorded"}</code></div>
        <div className={styles.item}><span className={styles.label}>Rows</span><span className={styles.value}>{telemetry.total_rows}</span></div>
        <div className={styles.item}><span className={styles.label}>Primary coverage</span><span className={styles.value}>{coverage == null ? "—" : `${(coverage * 100).toFixed(1)}%`}</span></div>
        <div className={styles.item}><span className={styles.label}>CI run</span><span className={styles.value}>{provenance?.github_run_id ?? "not recorded"}</span></div>
      </div>
      {sources.length > 0 && (
        <p className={styles.sources}>Inputs: {sources.map((source) => `${source.path} (${source.rows} rows, ${source.modified_at ?? "time unknown"})`).join(" · ")}</p>
      )}
    </div>
  );
}
