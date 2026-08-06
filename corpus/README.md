# Corpus layout (multi-language matrix)

## Layout

```text
corpus/
  matrix/
    profiles.yaml      # smoke / core_c_pe / opt_cliff / lang_* / full_matrix
    toolchains.yaml    # compile recipes (gcc/clang/g++/rustc/go × isa×format)
  dev/ | holdout/
    source/
      c/               # C sources (primary semantic cohort)
      cpp/             # C++ (rolling out)
      rust/            # Rust (rolling out)
      go/              # Go (rolling out)
    manifests/         # per-family JSON (function → variants + addrs)
    binaries/          # gitignored; built by scripts/build_matrix.py
    inventory.json     # optional toolchain fingerprint after build
```

## Profiles

Run / build with a profile to avoid Cartesian explosion:

```bash
export BENCHMARK_PROFILE=smoke
python runner/runner.py --corpus dev --profile smoke --decompilers fission,ghidra

# Build only variants needed for a profile (optional)
python scripts/build_matrix.py --split dev --profile core_c_pe
```

| Profile | Role |
|---------|------|
| `smoke` | Push CI — small C PE O0 slice |
| `core_c_pe` | Official C PE ranking cohort (O0/O2, x64+m32) |
| `opt_cliff` | Full opt ladder on stress functions |
| `lang_cpp` / `lang_rust` / `lang_go` | Language tracks |
| `multi_isa` | PE+ELF / multi-arch |
| `full_matrix` | Fan-out core + languages + multi_isa, merge for diagnostics |
| `decbench_scale_smoke` | 250 external subjects from `corpus/scale` |
| `decbench_scale_full` | Materialized DecBench-scale non-ranking cohort |

```bash
# Fan-out + merge (needs decompilers + oracle up)
./scripts/run_matrix_fanout.sh dev results/dev_latest.json
python scripts/merge_envelopes.py results/slices/dev_*.json -o results/dev_merged.json
```

## Semantic policy

- **Headline ranking** remains semantic pass rate on the **core C PE** cohort until other language oracles are measurement-valid.
- Rows should carry `language`, `isa`, `format`, `abi_profile` for pivots.
- **C++ (P1):** `source/cpp/patterns.cpp` — C++ behind **`extern "C"`** (`lang_cpp`).
- **Rust (P2):** `source/rust/patterns.rs` — **`#[no_mangle] extern "C"`** (`lang_rust`).
- **Go (P3):** `source/go/patterns/` — CGO **`//export`** C ABI (`lang_go`); `go build` with
  `GOOS=windows GOARCH=amd64 CC=x86_64-w64-mingw32-gcc`.

```bash
python runner/runner.py --corpus dev --profile lang_cpp --decompilers fission,ghidra
python runner/runner.py --corpus dev --profile lang_rust --decompilers fission,ghidra
python runner/runner.py --corpus dev --profile lang_go --decompilers fission,ghidra

CORPUS_TARGET=windows-x86_64 python scripts/build_matrix.py --split dev --languages go

# Multi-ISA (ELF x64 + aarch64) — use docker corpus-builder on macOS
docker compose --profile tools run --rm --build corpus-builder \
  python3 scripts/build_matrix.py --split dev --languages c
python runner/runner.py --corpus dev --profile multi_isa --decompilers fission,ghidra
```

Also fix go cstr_len - need C.free which needs stdlib.h

## Build

```bash
# Docker (CI default)
docker compose --profile tools run --rm --build corpus-builder

# Host (needs mingw / toolchains)
CORPUS_TARGET=windows-x86_64 python scripts/build_matrix.py --split dev
```

Legacy entrypoint: `scripts/build_corpus.py` delegates to `build_matrix.py`.

## Tens-of-thousands scale track

The authored fixtures intentionally stay small enough for executable semantic
wrappers. A separate pinned DecBench materialization supplies tens of thousands
of real-project functions without committing third-party binaries:

```bash
python scripts/materialize_scale_corpus.py --config unoptimized
python runner/runner.py --corpus scale --profile decbench_scale_full \
  --run-mode local --decompilers fission,ghidra
```

See `corpus/scale/README.md` for provenance and malware isolation rules.
