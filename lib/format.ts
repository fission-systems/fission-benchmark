// Pure formatting helpers with no server-only dependencies (no `fs`, no
// `path`) -- safe to import from both Server Components and Client
// Components. `lib/benchmark.ts` re-exports these for existing call sites;
// new Client Component code should import directly from here instead of
// pulling in `lib/benchmark.ts`'s `fs/promises` usage.

export function pct(rate: number | null | undefined, digits = 1): string {
  if (rate === null || rate === undefined || Number.isNaN(rate)) return "—";
  return `${(rate * 100).toFixed(digits)}%`;
}

export function meanFmt(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}
