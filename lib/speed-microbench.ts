import { readFile } from "fs/promises";
import path from "path";
import type { SpeedMicrobenchDocument } from "./speed";
import { getLatestReleaseVersion } from "./benchmark";

const REMOTE_URL =
  process.env.SPEED_MICROBENCH_REMOTE_URL ??
  "https://raw.githubusercontent.com/fission-systems/fission-benchmark/main/results/speed/microbench_latest.json";

export type LoadedSpeedMicrobench = {
  data: SpeedMicrobenchDocument;
  source: string;
};

function valid(raw: unknown): raw is SpeedMicrobenchDocument {
  if (!raw || typeof raw !== "object") return false;
  const value = raw as SpeedMicrobenchDocument;
  return (
    ["speed-microbench-v1", "speed-microbench-v2"].includes(value.schema ?? "") &&
    Boolean(value.by_decompiler) &&
    Object.keys(value.by_decompiler ?? {}).length > 0
  );
}

function finishedAt(item: LoadedSpeedMicrobench): number {
  const timestamp = Date.parse(item.data.finished_at ?? "");
  return Number.isFinite(timestamp) ? timestamp : 0;
}

export async function getLatestSpeedMicrobench(): Promise<LoadedSpeedMicrobench | null> {
  const latestRelease = await getLatestReleaseVersion();
  if (!latestRelease) return null;
  const candidates: LoadedSpeedMicrobench[] = [];
  const addCandidate = (data: SpeedMicrobenchDocument, source: string) => {
    if (data.toolchain?.fission_version !== latestRelease) return;
    candidates.push({ data, source });
  };
  try {
    const file = path.join(process.cwd(), "public", "speed-microbench-latest.json");
    const raw = JSON.parse(await readFile(file, "utf8")) as unknown;
    if (valid(raw)) addCandidate(raw, "public/speed-microbench-latest.json");
  } catch {
    // Remote fallback remains available.
  }
  try {
    const response = await fetch(REMOTE_URL, { cache: "no-store" });
    if (response.ok) {
      const raw = (await response.json()) as unknown;
      if (valid(raw)) addCandidate(raw, REMOTE_URL);
    }
  } catch {
    // Optional diagnostic artifact.
  }
  candidates.sort((a, b) => finishedAt(b) - finishedAt(a));
  return candidates[0] ?? null;
}

export function chooseNewestMicrobench(
  embedded: SpeedMicrobenchDocument | null | undefined,
  standalone: LoadedSpeedMicrobench | null,
): LoadedSpeedMicrobench | null {
  const embeddedLoaded = embedded
    ? { data: embedded, source: "benchmark envelope" }
    : null;
  if (!embeddedLoaded) return standalone;
  if (!standalone) return embeddedLoaded;
  return finishedAt(standalone) > finishedAt(embeddedLoaded)
    ? standalone
    : embeddedLoaded;
}
