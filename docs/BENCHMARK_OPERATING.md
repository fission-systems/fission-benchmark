# Benchmark-first operating guide

This repository’s job is to be a **reliable measuring instrument** for decompiler
quality. Fission product work is secondary to measurement honesty here.

## Priority order

1. **Infrastructure reliability** of the measuring instrument (adapters, oracle
   harness identity, matrix completeness, evidence linkage).
2. **Semantic evidence** (`original_binary` oracle) is the only ranking axis.
3. **Coverage + fail taxonomy** make denominators honest.
4. **Holdout + publication gate** protect against overfitting and bad publishes.
5. **CFG / runtime / extension tracks** are secondary analysis.
6. Similarity / readability proxies are diagnostics only.

## Multi-language matrix profiles

Corpus breadth is growing toward C/C++/Rust/Go × multi-opt × multi-arch. Full
Cartesian products must not run on every push.

| Profile | Use |
|---------|-----|
| `smoke` | Push CI — small C PE `-O0` slice |
| `core_c_pe` | Official default — C PE x64+m32, `-O0`/`-O2` (ranking / publish) |
| `opt_cliff` | Full opt ladder on stress functions |
| `lang_cpp` / `lang_rust` / `lang_go` | Language tracks |
| `multi_isa` | PE + ELF x64/aarch64 structural slice |
| `full_matrix` | Fan-out: core + lang_* + multi_isa, then merge |

```bash
python runner/runner.py --corpus dev --profile smoke --decompilers fission,ghidra
export BENCHMARK_PROFILE=core_c_pe

# Full multi-lang diagnostic merge (local)
ORACLE_ENDPOINT=http://localhost:8010 ./scripts/run_matrix_fanout.sh dev results/dev_latest.json
# → results/dev_core_c_pe.json  (ranking)
# → results/dev_latest.json     (merged diagnostic)

# Official helpers
./scripts/run_official_profiles.sh core
./scripts/run_official_profiles.sh full_matrix
```

**Publication rule:** gates and Pages use the **core_c_pe** ranking slice
(`results/dev_publish.json`). The merged full_matrix envelope is diagnostic
only (`results/dev_full_matrix.json` when produced by CI).

Build binaries:

```bash
CORPUS_TARGET=windows-x86_64 python scripts/build_matrix.py --split dev
# or: docker compose --profile tools run --rm --build corpus-builder
```

See `corpus/README.md` and `corpus/matrix/{profiles,toolchains}.yaml`.

### P1 reproducibility contract

Official C/C++ builds now emit one compiler-matched preprocessed translation
unit per binary variant under `corpus/<split>/preprocessed/`. The manifest field
`compiler_variants[].preprocessed_source` binds GED to that exact TU. System
header bodies are stripped, while macro expansion and corpus-local includes are
retained. `ged_metadata.source_basis=authored_source_fallback` is a visible
legacy fallback and the official eval-kit builder rejects it.

Long matrix runs are resumable by default:

```bash
# Content-addressed default under .cache/benchmark-checkpoints/
python runner/runner.py --corpus dev --profile smoke

# Explicit checkpoint; contract mismatch is rejected
python runner/runner.py --corpus dev --profile smoke \
  --checkpoint .cache/my-run.jsonl

# Deliberately discard existing rows for that checkpoint
python runner/runner.py --corpus dev --profile smoke \
  --checkpoint .cache/my-run.jsonl --no-resume
```

The checkpoint contract binds the exact expected cells, corpus manifest,
release contract, runner commit, and runner source hash. Each completed batch is
fsync'd as JSONL before the next batch completes. GED and recompilation use the
versioned content cache under `.cache/metric-cache`; set
`FISSION_BENCHMARK_NO_CACHE=1` to bypass it or
`FISSION_BENCHMARK_CACHE_DIR=/path` to relocate it. CI restores and saves both
caches even when a later benchmark step fails.

Every publishable official run builds `results/eval-kit/` with:

- `rows.jsonl` (decompiler output and metric evidence)
- `expected-cells.json` (frozen denominator)
- `binaries/` plus SHA-256 `binary-index.json`
- `preprocessed/` and serialized `source-cfgs.json`
- `manifest.json` binding every file and the source envelope

CI stores it permanently as the versioned GitHub Release asset
`fission-eval-kit-<version>.tar.gz`, also uploads the per-run Actions artifact
`benchmark-eval-kit-<github_run_id>`, and commits the lightweight
`public/eval-kit-latest.json` index with the direct release URL. The build fails
if row, subject, tool, binary, or source-CFG coverage falls below the prior
release using the same release contract.

### P2 measurement-health contract

New runner envelopes stamp
`run.measurement_contracts.dashboard_health=measurement-health-v1` and include
`summary.mvp.measurement_health`. The `/measurement` dashboard uses that one
block for five questions that must be answered together before comparing tools:

- Which preset and how many subject cells are selected?
- Is the denominator the shared missing-as-miss scope, or the all-tool clean
  output intersection?
- How many subjects are easy, medium, hard, or structurally unmeasured?
- Which failures came from adapters, boundaries, recompilation, or the oracle?
- Did source CFG, decompiled CFG, semantic oracle, and wall-time collection run?

The default remains `shared`: if any active tool measures a metric for a
subject, missing peer measurements remain misses. `intersection` is an
investigative normalization that first requires every active decompiler to
produce usable requested-function output. Difficulty is explicitly a proxy
from exact GED agreement (`easy >= 2/3`, `hard <= 1/3`, otherwise `medium`), not
a ranking metric. Runtime cost is per-function wall time; USD stays `null`/N/A
unless a priced execution source is recorded.

The dashboard data gate is backward-compatible for archived envelopes, but
fail-closed once the P2 contract is stamped: a missing health block or missing
`all.shared` / `all.intersection` views rejects publication.

### Infra non-negotiables

- Oracle rows that reach the harness must carry **`oracle_evidence.valid=true`**
  with `oracle_subject=original_binary` when the PE fixture is sound — even if
  the candidate renames poorly or fails to compile (those are quality buckets:
  `compile_error` / `boundary_mismatch`, not `oracle_error`).
- Synthetic decompiler names (`proc_0x…`, `FUN_…`) are renamed onto the harness
  symbol so multi-decompiler matrices do not collapse evidence validity.
- **Core adapters** (fission, ghidra) enforce per-backend clean-rate thresholds.
  Other backends may be marked `backend_weak:*` without invalidating the whole
  multi-decompiler run; systemic collapse still fails via overall coverage.
- Full multi-decompiler official is a **matrix width** goal; core fission+ghidra
  remains the publication-proven profile until non-core adapter residuals drop.

## Standard set contract

Every modern result envelope should carry:

```json
"summary": {
  "schema": "standard-set-v1",
  "mvp": {
    "same_function": { "...": "infra honesty axis" },
    "by_decompiler": { "...": "semantic + coverage + taxonomy" },
    "measurement_health": { "schema": "measurement-health-v1" }
  }
}
```

Built by `runner/standard_summary.py` and attached in `build_envelope()`.

| Tier | Metric |
|------|--------|
| **MVP-0** | **Same-function matrix** (request `(binary, addr)`; core vs multi) |
| MVP-1 | Semantic pass rate |
| MVP-2 | Coverage |
| MVP-3 | Fail taxonomy |
| MVP-4 | CFG match (optional) |
| MVP-5 | Runtime |
| EXT-6 | Holdout / overfit |
| EXT-7 | Cross-compiler × opt |
| EXT-8 | Human study pack |
| EXT-9 | `corpus/realworld/` track |

### MVP-0 Same-function matrix (infra honesty)

**Contract:** each result row is one request for a **single function entry**
`(binary, addr)`.  This is deliberately stricter than Dogbolt /
decompiler-explorer (whole-program C dumps).

| `output_diagnostics.status` | Meaning |
|-----------------------------|---------|
| `direct_function` | Single target-like unit with name and/or address anchor |
| `needs_normalization` | Target-like but soft harness blockers remain |
| `boundary_mismatch` | Output is not the requested function |
| `whole_program_output` | Multi-function / truncated dump |
| `no_output` | Empty / sentinel / failed extract |

**Primary rate (publication auxiliary table):**

```text
same_function_rate =
  direct_function
  / (direct_function + boundary_mismatch + whole_program_output + no_output)
```

`needs_normalization` is reported separately and included only in
`same_function_loose_rate`.

**Cohorts:**

- **core** — `fission`, `ghidra` (publication / validity core)
- **multi** — all other adapters (matrix width; may be `backend_weak`)
- **all** — every decompiler in the run

```bash
# From any result envelope (holdout multi preferred for multi-cohort table)
python -m runner.same_function_matrix results/holdout_infra_multi.json \
  -o results/same_function_matrix.json \
  --markdown results/same_function_matrix.md --print

# Also embedded under summary.mvp.same_function when envelopes are built
python scripts/check_benchmark_path.py --repair results/holdout_infra_multi.json
```

## Local loop (measurement quality)

```bash
pip install -e ".[dev]"
docker compose build oracle   # after oracle changes
docker compose up -d          # decompilers + oracle as needed

# Candidate runs — never overwrite official latest without the gate
ORACLE_ENDPOINT=http://localhost:8010 python runner/runner.py \
  --corpus dev --run-mode smoke --output results/dev_latest.json

python scripts/check_benchmark_path.py results/dev_latest.json

# Official path (full matrix, no --limit)
ORACLE_ENDPOINT=http://localhost:8010 python runner/runner.py \
  --corpus dev --run-mode official --output results/dev_latest.json
ORACLE_ENDPOINT=http://localhost:8010 python runner/runner.py \
  --corpus holdout --run-mode official --output results/holdout_latest.json
python runner/holdout_report.py \
  --dev results/dev_latest.json --holdout results/holdout_latest.json \
  --json-output results/overfitting_report.json
python -m runner.publication_gate \
  --dev results/dev_latest.json \
  --holdout results/holdout_latest.json \
  --overfitting results/overfitting_report.json \
  --output results/publication-verdict.json
```

## Do / don’t

| Do | Don’t |
|----|--------|
| Fix adapters, boundaries, wrappers, oracle | Rank by source similarity |
| Keep `no_wrapper` visible | Treat untested as decompiler fail |
| Use holdout only for release evaluation | Tune Fission against holdout |
| Commit standard-set summary in envelopes | Promote `results/local_*.json` or legacy lists |
| Prefer taxonomy buckets for triage | Hide whole-program rows as “clean” |

## Offline contract check

```bash
python scripts/check_benchmark_path.py results/dev_latest.json
python scripts/check_benchmark_path.py --repair results/dev_latest.envelope.json
```

## Layered parity (Ghidra reference)

```bash
export FISSION_HOST_PORT=8007
# Smoke (CI default): 3 subjects
python -m runner.run_parity --corpus dev --limit 3 --decompilers fission,ghidra
python scripts/check_parity_smoke.py results/telemetry/latest.json

# Larger batch
python -m runner.run_parity --corpus dev --limit 20 --decompilers fission,ghidra
python -m benchmark.telemetry.aggregate  # → public/parity-telemetry.json

# Freeze known CFG/pcode gaps
python scripts/extract_golden_repros.py \
  --inputs results/cfg_parity/latest.jsonl results/pcode_parity/latest.jsonl
python -m benchmark.golden_repros.run
```

### Dashboard IA (split surfaces)

| Route | Purpose |
|-------|---------|
| `/` | **Overview** — validity, semantic ranking, same-function snapshot, nav hub |
| `/same-function` | **MVP-0 same-function matrix** — `(binary, addr)` boundary honesty |
| `/functions` | **Per-function code grid** (heavy browse surface) |
| `/variants` | **Compiler × opt** semantic pivots |
| `/fission-vs-ghidra` | **Shared IR / layered parity** — Ghidra reference vs Fission |

Do not mix IR match rates into multi-tool ranking. Parity telemetry is served from
`public/parity-telemetry.json` (or remote fallback).

**Empty / core-only multi-decomp UI is a CI failure.** Gate:

```bash
python scripts/check_dashboard_data.py \
  --min-rows 1 --min-decompilers 8 --require-valid --check-remote
```

Requires a displayable envelope in
`public/benchmark-latest.json` **or** `results/latest.json` **or**
`results/dev_latest.json` (rows ≥ 1, `validity.valid=true`, **≥ 8 decompilers**).
Publishable is not required for smoke display; empty or fission+ghidra-only is
never allowed on main.

**CI auto-refresh (no manual multi re-run):** on every successful measurement
(`MEASUREMENT_VALID=true`), Benchmark & Deploy:

1. Runs the full `BENCHMARK_DECOMPILERS` list (includes retdec, etc.)
2. Attaches `summary.mvp.same_function`
3. Commits `results/dev_latest.json` + `public/benchmark-latest.json` with
   `[skip ci]` so Vercel picks up multi-tool tables without a local force-add

### CI speed profile (push vs official)

| Trigger | Semantic matrix | Parity subjects | Notes |
|---------|-----------------|-----------------|-------|
| **push → main** | smoke: limit 10 × 1 variant × 9 tools | `PARITY_LIMIT=20` | Fast path; gates need ≥5 comparable |
| **schedule / fission-release** | full official | full (`0`) | Publication-quality |
| **workflow_dispatch** | inputs (default full limits) | inputs (default `0`) | Override freely |

Other push-path speedups (no quality gate regression):

- **Parallel image pull** (×6) then sequential build only for miss/changed
- **Parallel container health waits**
- **Corpus binary + preprocessed-TU cache** (`actions/cache` on corpus artifacts)
- **Row checkpoint + metric content cache** (`.cache/benchmark-*`, restored in CI)
- **pip cache** via `setup-python`
- **`BENCHMARK_HTTP_CONCURRENCY=12`** for I/O-bound multi-adapter batches
- **`paths-ignore`**: `**.md`, `docs/**`, `LICENSE` skip the full workflow

Official/full runs are unchanged: no subject caps, same reliability thresholds.

### Oracle harness freshness

The differential oracle image bakes `runner/` at build time, but compose **bind-mounts**
`./runner → /app/runner` so harness fixes (`differential_oracle.py`, `semantic.py`)
apply on the next Benchmark run without waiting for ghcr republish. Publish-images
still rebuilds `oracle` when those files change; Benchmark also force-rebuilds
oracle locally when the same paths (or `docker-compose.yml`) change on push.

If multi-tool rows show mass `compile_error` with errors like
`unknown type name 'word32'` or `undefined reference to oracle_candidate_*`
after a harness fix, the run used a **stale oracle** (pre-mount race). Re-run
Benchmark; do not treat that as decompiler quality.

### Function discovery (function *finding*)

Primary layered stage: **whole-binary function inventory** (`GET /functions`).

| Axis | Definition |
|------|------------|
| Unit | Binary variant (compiler × opt) |
| Primary | Address-set equality vs reference |
| Dual | recall / precision / F1 / Jaccard + optional manifest_recall |
| Refs | Ghidra inventory (default), PE symbols, corpus manifests |

```bash
export FISSION_HOST_PORT=8007
# Core pair
python -m benchmark.function_discovery.run --corpus dev --limit 5

# Multi-tool discovery matrix + summary
python -m benchmark.function_discovery.run \
  --corpus holdout \
  --candidates fission,radare2,snowman,boomerang \
  --limit 10

# Standalone report from JSONL
python -m runner.function_discovery_report \
  results/function_discovery/latest.jsonl --print
```

Do **not** confuse with **MVP-0 same-function matrix** (decompile request
`(binary, addr)` boundary). Discovery asks “which functions exist?”; same-function
asks “did we decompile *this* entry?”

Ideas for the next axes: `docs/NEXT_BENCHMARK_IDEAS.md`.

## Related files

- `runner/standard_summary.py` — MVP aggregation (includes `mvp.same_function`)
- `runner/same_function_matrix.py` — same-function matrix builder + CLI
- `runner/function_discovery_report.py` — function-finding report + CLI
- `benchmark/function_discovery/` — inventory parity runner + PE oracle
- `runner/output_diagnostics.py` — `direct_function` / boundary statuses
- `runner/run_parity.py` / `benchmark/*_parity` — layered stages
- `runner/run_validity.py` / `publication_gate.py` — quality gates
- `runner/differential_oracle.py` + `docker/oracle/` — original_binary
- `benchmark/KNOWN_ISSUES.md` — freeze policy
- `docs/NEXT_BENCHMARK_IDEAS.md` — roadmap
