<div align="center">

# fission-benchmark

**Multi-decompiler comparison benchmark for [Fission](https://github.com/fission-systems/Fission)**

Fission · Ghidra · Radare2+r2ghidra · angr · Snowman · rev.ng · Boomerang · Reko

[![Benchmark](https://github.com/fission-systems/fission-benchmark/actions/workflows/benchmark.yml/badge.svg)](https://github.com/fission-systems/fission-benchmark/actions/workflows/benchmark.yml)
[![Docker Build](https://github.com/fission-systems/fission-benchmark/actions/workflows/build-check.yml/badge.svg)](https://github.com/fission-systems/fission-benchmark/actions/workflows/build-check.yml)

📊 **[Live Dashboard →](https://fission-benchmark.vercel.app)**  
⏱️ **Speed tab** (`/speed`): decompile latency (`time_ms`) + optional cold/warm micro-bench — non-ranking

</div>

---

## Overview

Each decompiler runs in an isolated Docker container exposing a uniform HTTP API.
A Python runner sends decompile requests in parallel, scores results against original C source, and generates a comparative report.

**Benchmark-first:** this repo’s primary job is measurement honesty, not shipping Fission features. See [docs/BENCHMARK_OPERATING.md](docs/BENCHMARK_OPERATING.md) for the operating guide and standard-set contract.

**Dashboard (split):**

| Route | Surface |
|-------|---------|
| `/` | Overview — semantic ranking hub + nav |
| `/same-function` | Same-function matrix (boundary honesty) |
| `/functions` | Per-function code grid |
| `/variants` | Compiler × opt pivots |
| `/measurement` | Preset, denominator, difficulty, failure/cost, and pipeline health |
| `/quality` | Non-ranking compile, readability, and corpus diagnostics |
| `/speed` | Latency, CPU, and memory diagnostics |
| `/fission-vs-ghidra` | Fission ↔ Ghidra layered parity (shared IR; not ranking) |

```
Binary + Source (ground truth)
        ↓
┌──────────────────────────────────────────────────────────────┐
│  runner.py  (parallel httpx requests)                        │
│  Fission :8000 · Ghidra :8001 · Boomerang :8002 · Radare2 :8003 │
│  angr :8004 · Snowman :8005 · rev.ng :8006 · Reko :8008 · RetDec :8009 │
└──────────────────────────────┬───────────────────────────────┘
                               │
                     ↓
              scoring.py  (correctness score + consensus)
                     ↓
              render_report.py → results/latest.md + docs/index.html
                     ↓
              Vercel (official runs only) → fission-benchmark.vercel.app
```

## Run Validity

Every result file is evaluated by a two-tier verdict:

| Tier | Meaning | CLI exit |
|---|---|---|
| `valid` | Measurement quality OK — matrix complete, Fission ≥ 90%, all-backend ≥ 90% | — |
| `publishable` | `valid` AND `--run-mode official` AND no provenance issues | required for Vercel deploy |

A **smoke run** (`--run-mode smoke`, default on push) produces `valid=True, publishable=False` — workflow is green but nothing is published. An **official run** (`--run-mode official`, weekly schedule or manual dispatch) must also pass the publishability gate before deploying.

```bash
# Evaluate a result file directly
python -m runner.run_validity results/dev_latest.json \
  --github-env "$GITHUB_ENV" \
  --github-summary "$GITHUB_STEP_SUMMARY"
# Emits: MEASUREMENT_VALID=true/false, RUN_PUBLISHABLE=true/false
```

## Overfitting Prevention (3-Layer)

| Layer | Mechanism |
|---|---|
| **Train/Holdout** | 80/20 function-level split (fixed seed). Use `--corpus holdout` for holdout evaluation. |
| **Cross-compiler** | Same source compiled with gcc -O0 and gcc -O2 — evaluated independently |
| **Multi-decompiler consensus** | If all decompilers score low → `⚪ Universally low (harness)`. Only Fission low → quality gap. |

> **Holdout split**: function-level 80/20 with fixed seed (`HOLDOUT_SEED=42`).
> Populate or re-lock with `python scripts/populate_holdout.py`, then rebuild
> binaries (`python scripts/build_corpus.py --split holdout` or the
> `corpus-builder` Docker profile). Official publication requires a non-empty
> holdout run linked through `publication_gate`.

## Quick Start

### Requirements

- Docker + Docker Compose
- Python 3.11+
- GCC-compatible C compiler + `nm` (for corpus binary/address generation), or the Dockerized corpus builder below
- `pip install -e ".[dev]"`

### Run

```bash
# Build decompiler containers
docker compose build

# Build corpus binaries and populate per-function addresses
python scripts/build_corpus.py --split dev

# On macOS/Apple Silicon, build Windows x86-64 PE corpus binaries instead.
docker compose --profile tools run --rm corpus-builder

# Start containers
docker compose up -d

# Wait for health checks
curl http://localhost:8001/health  # Ghidra
curl http://localhost:8003/health  # Radare2
curl http://localhost:8010/health  # MinGW/Wine semantic oracle

# Run benchmark (smoke, candidate JSON only — does not overwrite latest.*)
ORACLE_ENDPOINT=http://localhost:8010 python runner/runner.py --corpus dev

# Official publishable path (requires containers + full matrix, no limits):
#   ORACLE_ENDPOINT=http://localhost:8010 python runner/runner.py \
#     --corpus dev --run-mode official --output results/dev_latest.json
#   ORACLE_ENDPOINT=http://localhost:8010 python runner/runner.py \
#     --corpus holdout --run-mode official --output results/holdout_latest.json
#   python runner/holdout_report.py \
#     --dev results/dev_latest.json --holdout results/holdout_latest.json \
#     --json-output results/overfitting_report.json
#   python -m runner.publication_gate \
#     --dev results/dev_latest.json \
#     --holdout results/holdout_latest.json \
#     --overfitting results/overfitting_report.json \
#     --output results/publication-verdict.json
```

### Options

```bash
# Single function smoke test
python runner/runner.py --corpus dev --limit 1

# Specific decompilers only
python runner/runner.py --corpus dev --decompilers fission,ghidra

# Full core decompiler set
python runner/runner.py --corpus dev \
  --decompilers fission,ghidra,boomerang,radare2,angr,snowman,revng,reko,retdec

# Skip a specific decompiler via environment variable
FISSION_ENDPOINT=skip python runner/runner.py --corpus dev
GHIDRA_ENDPOINT=skip python runner/runner.py --corpus dev

# Point a decompiler at a custom endpoint
GHIDRA_ENDPOINT=http://localhost:9001 python runner/runner.py --corpus dev
FISSION_ENDPOINT=http://localhost:9000 python runner/runner.py --corpus dev

# Any {NAME}_ENDPOINT variable is supported:
# BOOMERANG_ENDPOINT, RADARE2_ENDPOINT, ANGR_ENDPOINT,
# SNOWMAN_ENDPOINT, REVNG_ENDPOINT, REKO_ENDPOINT

# Holdout evaluation (release only — never during development)
python runner/runner.py --corpus holdout

# Full corpus (dev + holdout combined)
python runner/runner.py --corpus full

# Explicit run mode
python runner/runner.py --corpus dev --run-mode official  # marks as publishable candidate
python runner/runner.py --corpus dev --run-mode smoke     # default, no publish gate
python runner/runner.py --corpus dev --run-mode local     # local dev, non-official

# Save to a custom path (never overwrites latest.*)
python runner/runner.py --corpus dev \
  --output results/dev_latest.json

# Final publication gate (requires independently valid evidence)
python -m runner.publication_gate \
  --dev results/dev_latest.json \
  --holdout results/holdout_latest.json \
  --overfitting results/overfitting_report.json \
  --output results/publication-verdict.json

# Promote only with the linked final verdict
python runner/render_report.py \
  --input results/dev_latest.json \
  --corpus dev \
  --publication-verdict results/publication-verdict.json \
  --update-latest   # promotes to latest.json + latest.md + docs/index.html
```

### Local Fission build (quality loop only)

CI always uses a **GitHub Release** Fission bake (`FISSION_SOURCE=release`).
For day-to-day decompiler work you can mount a **current Linux `fission_cli` + `utils/`** into the same adapter:

```bash
# 1) Build / collect a Linux ELF CLI + utils (not macOS Mach-O).
scripts/prepare_local_fission.sh
#    optional: FISSION_ROOT=/path/to/Fission
#    optional: FISSION_LINUX_CLI=/path/to/linux/fission_cli
#    optional: FISSION_FORCE_DOCKER_BUILD=1
#    macOS tip: brew install zig && cargo install cargo-zigbuild --locked

# 2) Start only the Fission adapter with the local overlay
set -a && source .env.local && set +a
docker compose -f docker-compose.yml -f docker-compose.local.yml \
  --profile local up -d --build fission

# 3) Confirm provenance
curl -s "http://localhost:${FISSION_HOST_PORT:-8007}/health"
# → "source": "local", "git_sha": "...", "release_version": "local-<sha>"

# 4) Measure into a non-latest path (do not overwrite official latest)
python runner/runner.py --corpus dev --decompilers fission \
  --output "results/local_${FISSION_GIT_SHA}.json"
```

**Rules**

| Path | Fission binary | Results |
|---|---|---|
| CI official run → Vercel | Release tag only | Official timeline |
| Local quality loop | Current build (Linux ELF) | `results/local_<sha>.json` only |

## Repository Layout

```
fission-benchmark/
├── benchmark/
│   ├── KNOWN_ISSUES.md   Infrastructure freeze policy and remaining trust gaps
│   ├── decode_parity/    Instruction decoder parity runner
│   ├── assembly_parity/  Instruction listing parity runner
│   ├── pcode_parity/     Raw p-code parity runner
│   ├── cfg_parity/       Basic block/edge parity runner
│   ├── function_discovery/  Binary-level function discovery parity
│   ├── ir_invariants/    Fission-internal IR invariant checks
│   ├── golden_repros/    Fixed regression canary runner
│   ├── telemetry/        JSONL result aggregation
│   ├── readability/      Readability proxy metrics and human-study plan
│   ├── decompiler_quality/  Current output-quality stage marker
│   └── common/           Shared schemas, providers, JSONL helpers
├── docker/
│   ├── ghidra/      Ghidra 12.x headless + FastAPI
│   ├── boomerang/   Boomerang + FastAPI
│   ├── radare2/     Radare2 + r2ghidra + FastAPI
│   ├── fission/     Fission CLI + FastAPI (release bake; local mount overlay)
│   ├── angr/        angr decompiler + FastAPI
│   ├── snowman/     Snowman/nocode + FastAPI
│   ├── revng/       rev.ng + FastAPI
│   ├── reko/        Reko + FastAPI
│   └── retdec/      RetDec v5 + FastAPI
├── runner/
│   ├── runner.py         Candidate-run orchestrator (--corpus, --run-mode)
│   ├── corpus.py         Corpus management + holdout split
│   ├── scoring.py        Correctness score + structural metrics
│   ├── run_validity.py   Shared validity engine (measurement_valid / publishable)
│   ├── publication_gate.py Final dev + holdout + oracle evidence gate
│   ├── render_report.py  Non-destructive report renderer (--update-latest)
│   ├── readability.py    AST-based readability proxy metrics
│   └── report.py         Markdown + HTML report generation
├── scripts/
│   ├── build_corpus.py      Compile corpus binaries + update function addresses
│   ├── populate_holdout.py  Deterministic 80/20 holdout lock from dev manifests
│   └── migrate_legacy_results.py  Wrap legacy flat-list JSON as envelope v2
├── corpus/
│   ├── dev/         80% — development corpus (source + manifests)
│   └── holdout/     20% — holdout corpus (release evaluation only)
├── docs/            Dashboard static files (committed by CI, served via Vercel)
├── results/         Benchmark results (auto-committed by official CI runs)
├── tests/           Unit and integration tests
│   ├── test_run_validity.py      Validity engine tests (28 cases)
│   ├── test_render_report.py     Legacy correctness migration tests
│   └── test_report_integration.py  Report generation integration tests
├── vercel.json      Vercel static site config (serves docs/)
└── .github/
    └── workflows/
        ├── benchmark.yml     Smoke (push) + official (schedule/dispatch) runs
        └── build-check.yml   Docker build validation
```

## Fission Release Tracking

CI sets `FISSION_SOURCE=release` and pins `FISSION_VERSION=v0.1.6` by default.
This keeps scheduled, push, and manual runs reproducible until the repository's
declared baseline is deliberately advanced. The `/health` probe must report
`"source": "release"` (CI fails on `local-*`).

### Preferred operator path (GitHub CLI)

Bake the release CLI into GHCR, then chain an official benchmark (Publish Images
does the chain automatically after a successful fission bake):

```bash
# 1) Bake fission image for a SemVer tag (also chains Benchmark & Deploy)
gh workflow run "Publish Images" \
  --repo fission-systems/fission-benchmark \
  -f services=fission \
  -f fission_version=v0.1.6

# 2) Official ranking + Pages (fast path: fission+ghidra only)
gh workflow run "Benchmark & Deploy" \
  --repo fission-systems/fission-benchmark \
  -f fission_version=v0.1.6 \
  -f corpus=dev \
  -f run_mode=official \
  -f publish_results=true \
  -f matrix_profile=core_c_pe \
  -f decompilers=fission,ghidra \
  -f parity_limit=40

# 3) Multi-decomp UI snapshot (slow: 9 tools; smoke or core as needed)
gh workflow run "Benchmark & Deploy" \
  --repo fission-systems/fission-benchmark \
  -f fission_version=v0.1.6 \
  -f run_mode=official \
  -f publish_results=false \
  -f matrix_profile=smoke \
  -f decompilers=fission,ghidra,boomerang,radare2,angr,snowman,revng,reko,retdec

# 4) Language pivots (weekly default: full_matrix, 2-tool parallel fan-out)
gh workflow run "Benchmark & Deploy" \
  --repo fission-systems/fission-benchmark \
  -f fission_version=v0.1.6 \
  -f run_mode=official \
  -f publish_results=true \
  -f matrix_profile=full_matrix \
  -f decompilers=fission,ghidra
```

### Performance tiers

| Path | Profile | Decompilers | Typical wall-clock | Publishes ranking? |
|------|---------|-------------|--------------------|--------------------|
| push | smoke | 9-tool | ~15–40m | No (multi envelope only) |
| release / manual | core_c_pe | **fission+ghidra** | ~30–70m | Yes |
| weekly schedule | full_matrix | fission+ghidra | ~1–3h (parallel slices) | Yes + lang pivots |
| optional multi | smoke/core | 9-tool | long | Multi UI only |

Runner already batches decompile by `(decompiler, binary)`. Ghidra reuses a **content-hash project cache** for batch decompile (no per-request cold import).

### Cross-repo dispatch from Fission

`repository_dispatch` (`fission-release`) starts **Publish Images** only (avoids
racing Benchmark before the image exists). After bake, CI runs
`gh workflow run "Benchmark & Deploy"` with the same version.

```bash
# Correct client_payload shape (must be a JSON object, not a string):
gh api repos/fission-systems/fission-benchmark/dispatches --input - <<'EOF'
{
  "event_type": "fission-release",
  "client_payload": { "fission_version": "v0.1.6" }
}
EOF
```

Manual workflow runs can override `fission_version` with another specific tag,
or with `latest` to resolve the newest GitHub Release dynamically.

## CI Workflow

| Trigger | Run mode | Publishes? |
|---|---|---|
| `push` to `main` | `smoke` (9-tool) | No — multi envelope only |
| Weekly schedule (`cron`) | `official` full_matrix (2-tool) | Yes — ranking + lang pivots |
| Manual ranking | `official` core_c_pe (2-tool) | Yes — if gate valid |
| Manual multi | 9-tool smoke/core | Multi UI (optional) |
| `fission-release` dispatch | Publish Images → chained ranking | Yes — 2-tool core_c_pe |

Official runs that pass the validity gate commit `results/` + `docs/` and deploy to **https://fission-benchmark.vercel.app** via Vercel CLI.

## API Contract

All decompiler containers expose:

```
POST /decompile
Body:     { "binary_b64": "<base64>", "addr": "0x1400010a0" }
Response: { "decompiler": "ghidra", "name": "fibonacci", "code": "...", "time_ms": 120, "error": null }

GET /health
Response: { "status": "ok", "decompiler": "ghidra", "version": "12.0" }

# Fission also reports provenance:
# { "status": "ok", "decompiler": "fission", "version": "...",
#   "release_version": "v0.1.6"|"local-<sha>",
#   "source": "release"|"local", "git_sha": "<optional>" }
```

## Adding a New Decompiler

1. Create `docker/<name>/Dockerfile` + `server.py` implementing the API contract above
2. Add the service to `docker-compose.yml` on the next available port
3. Add to `DECOMPILERS` dict in `runner/runner.py`
4. Add to `build-check.yml` matrix

## Core Open-Source Backends

The benchmark treats every configured open-source backend as part of the core
comparison set. Individual services can still be skipped explicitly for local
debugging with `*_ENDPOINT=skip` or by passing a narrower `--decompilers` list.

| Backend | Port | Notes |
|---|---:|---|
| `ghidra` | 8001 | Ghidra 12.x headless, primary reference baseline |
| `boomerang` | 8002 | Boomerang CLI, function-entry oriented |
| `radare2` | 8003 | Radare2 + r2ghidra |
| `angr` | 8004 | Python API, function-address oriented |
| `snowman` | 8005 | Uses `nocode`; legacy baseline, amd64-only |
| `revng` | 8006 | Uses `emit-c-as-single-file` (legacy: `decompile-to-single-file`); whole-program oriented |
| `reko` | 8008 | Reko decompiler |
| `retdec` | 8009 | RetDec v5 (range-comment slice + address anchors) |

Hosted CI runs the full core set by default and pulls prebuilt GHCR images when
available before falling back to local builds.

## Layered Quality Gates

Decompiler similarity is the final benchmark layer. Lower-level gates should be
run first when diagnosing Fission regressions:

1. `benchmark/assembly_parity` compares instruction bytes, mnemonics, operands,
   lengths, and branch targets from two assembly-listing providers.
2. `benchmark/decode_parity` compares decode fields such as instruction length,
   prefixes, ModRM/SIB, displacement, and immediate values.
3. `benchmark/pcode_parity` compares raw p-code op sequences from two providers,
   typically Ghidra raw p-code vs Fission SLEIGH runtime output.
4. `benchmark/cfg_parity` compares basic blocks and control-flow edges.
5. `benchmark/function_discovery` is the **function-finding** benchmark
   (inventory parity: address-set + dual recall/precision; Ghidra / PE / manifest refs).
6. `benchmark/ir_invariants` checks Fission internal IR/NIR/HIR invariants
   without an external reference provider.
7. `benchmark/golden_repros` runs fixed regression canaries.
8. `benchmark/telemetry` aggregates JSONL rows by stage, status, mismatch kind,
   compiler, and optimization level.
9. `runner/` remains the decompiler-output quality benchmark.

Benchmark infrastructure is currently in reliability-maintenance mode. Before
adding new axes, default decompilers, or composite rankings, check
`benchmark/KNOWN_ISSUES.md`.

Parity stages default to **Ghidra vs Fission over Docker HTTP** (see
`benchmark/README.md`). Command templates remain optional for custom tools.

```bash
# Prerequisites: docker compose up -d ghidra fission
export FISSION_HOST_PORT=8007   # if local overlay maps fission to 8007

# Single stages (HTTP defaults)
python -m benchmark.assembly_parity.run --limit 5
python -m benchmark.decode_parity.run --limit 5
python -m benchmark.pcode_parity.run --limit 5
python -m benchmark.cfg_parity.run --limit 5
python -m benchmark.function_discovery.run --limit 5
# Multi-tool + summary:
# python -m benchmark.function_discovery.run --candidates fission,radare2 --limit 5
# python -m runner.function_discovery_report results/function_discovery/latest.jsonl --print

# Unified runner → results/*_parity/latest.jsonl + telemetry
python -m runner.run_parity --corpus dev --limit 5 --decompilers fission,ghidra

python -m benchmark.telemetry.aggregate \
  results/assembly_parity/latest.jsonl \
  results/cfg_parity/latest.jsonl \
  results/pcode_parity/latest.jsonl
```

## Adding Corpus Cases

1. Add a C source file under `corpus/dev/source/`
2. Add a manifest under `corpus/dev/manifests/` with one entry per function
3. Use stable compiler variants such as `gcc -O0` and `gcc -O2`
4. Run `python scripts/build_corpus.py --split dev` before benchmarking

The build script compiles ignored local binaries under `corpus/dev/binaries/`
and refreshes each variant `addr` using `nm`. The runner scores against the
matching source function, not the whole source file.

## Standard metric set

Public reporting follows a fixed architecture (`summary.schema = standard-set-v1`):

### MVP (primary surfaces)

| # | Metric | Description |
|---|---|---|
| 0 | **Same-function matrix** | Request contract `(binary, addr)`; `same_function_rate = direct / (direct + boundary_*)`; core (fission+ghidra) vs multi; **infra honesty**, not a ranking substitute for semantic |
| 1 | **Semantic pass rate** | Oracle test pass rate under `original_binary` when PE+addr are supplied; sole ranking axis (`correctness_score`) |
| 2 | **Coverage** | attempted / adapter clean / invalid boundary / semantic tested / no_wrapper |
| 3 | **Fail taxonomy** | Exclusive buckets (`adapter_error`, `whole_program_output`, `compile_error`, …) |
| 4 | **CFG match** | Optional secondary from `benchmark/cfg_parity` (not ranking) |
| 5 | **Runtime** | Mean `time_ms` |

### Extensions

| # | Metric | Description |
|---|---|---|
| 6 | **Holdout + overfit** | Locked 80/20 split + `holdout_report` / `publication_gate` |
| 7 | **Cross-compiler / opt** | Semantic pivot by `compiler_variant` |
| 8 | **Human readability** | Study plan + `benchmark/readability/study_pack/` (no final score yet) |
| 9 | **Real-world strip** | Reserved `corpus/realworld/` track |

### Diagnostics only (non-ranking)

| Metric | Description |
|---|---|
| **Source Similarity** | `difflib.SequenceMatcher` on normalized text — **not** semantic accuracy |
| **Structural Penalty** | Relative goto / nesting vs source |
| **Readability proxies** | Unvalidated until human study |

Builder: `runner/standard_summary.py`. Dashboard primary table omits similarity.

The oracle service supports two subjects under the matching Windows
x86/x86-64 MinGW ABI + Wine:

| `oracle_subject` | Reference side | When used |
|---|---|---|
| `original_binary` | Calls the function at `function_addr` inside the provided corpus PE (manual PE map + relocations/imports) | Runner always supplies `reference_binary_b64` + `function_addr` — **required for publishable runs** |
| `source_recompile` | Recompiles extracted C source as the reference | Fallback when PE bytes/address are omitted (diagnostics only) |

Publication validity (`oracle_evidence_valid`) accepts only aggregate evidence with
`oracle_subject: original_binary`. Official runs also require `profile: realistic`,
full matrix (no `--limit` / `--function`), non-empty holdout, linked overfitting
report, and `publication_gate` success.

## Result Envelope Format

All result files use a versioned envelope (`schema_version: 2`):

```json
{
  "schema_version": 2,
  "run": {
    "started_at": "2026-07-11T00:00:00Z",
    "finished_at": "2026-07-11T00:05:00Z",
    "duration_ms": 300000,
    "runner_commit": "abc1234",
    "corpus": "dev",
    "official": true
  },
  "matrix": {
    "expected_decompilers": ["fission", "ghidra"],
    "expected_cells": [
      { "decompiler": "fission", "function_name": "foo", "compiler_variant": "gcc -O0" }
    ],
    "expected_rows": 2,
    "observed_rows": 2
  },
  "validity": {
    "valid": true,
    "publishable": true,
    "fission_coverage": 1.0,
    "reasons": [],
    "publish_reasons": []
  },
  "rows": [ ... ]
}
```

Legacy flat-list files are supported for rendering but are always marked `publishable: false`.

## License

AGPL-3.0-or-later

### Speed micro-bench (non-ranking)

Dedicated cold/warm decompile timing (does **not** update semantic ranking or Pages):

```bash
# Local (adapters already up)
python -m runner.speed_microbench \
  --endpoint fission=http://localhost:8000 \
  --endpoint ghidra=http://localhost:8001 \
  --binary corpus/dev/binaries/c/SOME_gcc_O0.exe \
  --addr 0x140001000 --addr 0x140001050 \
  --trials 5 \
  --output results/speed/microbench_latest.json

# CI
gh workflow run "Speed Smoke" --repo fission-systems/fission-benchmark \
  -f fission_version=v0.1.6 \
  -f trials=5 \
  -f decompilers=fission,ghidra
```

Envelope attachment: `attach_summary_to_envelope` writes
`summary.extensions.speed` (row `time_ms` aggregate + optional microbench from
`results/speed/microbench_latest.json`). Dashboard `/speed` shows both.
