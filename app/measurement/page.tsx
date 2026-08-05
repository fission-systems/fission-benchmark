import { SiteChrome } from "@/components/SiteChrome";
import { UnavailableData } from "@/components/UnavailableData";
import { ValidityBanner } from "@/components/ValidityBanner";
import { MeasurementHealthPanel } from "@/components/MeasurementHealthPanel";
import {
  extractMeasurementHealth,
  getLatestBenchmarkOptional,
} from "@/lib/benchmark";
import styles from "../dashboard.module.css";

export const revalidate = 900;

export const metadata = {
  title: "Measurement health · Benchmark scope",
  description:
    "Preset, denominator normalization, difficulty, failures, cost, and pipeline health for the latest official benchmark.",
};

export default async function MeasurementPage() {
  const data = await getLatestBenchmarkOptional();
  if (!data) {
    return <UnavailableData title="Measurement health unavailable" />;
  }
  const health = extractMeasurementHealth(data);
  const release = data.toolchain.fission_version ?? "unknown release";
  const contract = data.run.measurement_contracts?.dashboard_health;

  return (
    <SiteChrome
      active="measurement"
      subtitle="Scope · denominator · difficulty · failures · pipeline health"
    >
      <div className={styles.frame}>
        <div className={styles.frameTitle}>Measurement health</div>
        <p className={styles.frameBody}>
          Inspect what was measured before interpreting quality. This page is
          anchored to <strong>{release}</strong>, release contract{" "}
          <code>{data.run.release_contract?.id ?? "unstamped"}</code>, run{" "}
          <code>{data.run.run_id ?? "unknown"}</code>. It does not add another
          ranking axis.
        </p>
        <p className={styles.frameNote}>
          Data contract: {contract ?? "legacy envelope — P2 health block not stamped"}
        </p>
      </div>
      <ValidityBanner validity={data.validity} run={data.run} />
      {health ? (
        <MeasurementHealthPanel health={health} />
      ) : (
        <UnavailableData title="P2 measurement-health summary unavailable" />
      )}
    </SiteChrome>
  );
}
