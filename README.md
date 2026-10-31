# fission-benchmark

Local, [DecBench](https://github.com/Noelo-Lab/decbench)-style benchmark for the
[Fission](https://github.com/fission-systems/Fission) decompiler. Results page:
**https://fission-systems.github.io/fission-benchmark/**

- Runs **on your machine**, over hundreds of binaries (the published DecBench dataset: ~800 binaries, 39 projects, O0 / O2 / O2-noinline). No CI generates results.
- **Fission only.** No cross-decompiler comparison.
- Scoring uses DecBench's own metrics:
  - **GED**: control-flow graph edit distance vs the source CFG (perfect = 0)
  - **type_match**: recovered variable types vs DWARF
  - **byte_match**: recompile the decompiled C and compare code (Jaccard)
  - **Union**: functions that are perfect on at least one metric
- Fission only sees a **stripped** copy of each binary; names and types come from the original afterwards, for grading only.
- Rates are over *all* target functions (those with a symbol and a source CFG). A miss or crash counts against Fission.

## Setup

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -e .                                   # installs DecBench (pyjoern downloads Joern on first use, ~1.8 GB)
huggingface-cli download noelo-lab/decbench-dataset --repo-type dataset --local-dir decbench-data   # or: decbench download full
export FISSION_CLI=/path/to/fission_cli            # or put it on PATH
```

`llvm-nm` and `llvm-strip` (or `nm`/`strip`) must be on `PATH`. `byte_match` also
needs a native-arch C cross compiler for each target (e.g. `x86_64-linux-gnu-gcc`
for x86-64 ELF); without one that metric abstains and shows as `n/a`.

## Use

```sh
python -m fbench list --opt O0                      # what can be run
python -m fbench run -j 4                           # all binaries, resumable (runs/binaries/...)
python -m fbench run --opt O2 --project zlib        # a slice
python -m fbench run --limit 50 --layer hir         # evenly sampled, HIR print surface
python -m fbench report                             # -> docs/data/summary.json
python -m fbench serve                              # preview docs/ at http://localhost:8000
```

Already-scored binaries are skipped; use `--force` to redo them. Use `DECBENCH_DATA`
or `--data` to point at the dataset elsewhere.

## Publish (GitHub Pages)

```sh
python -m fbench report
git add docs && git commit -m "results: fission <version>" && git push
```

In the repo settings, set **Pages → Source: Deploy from a branch → `main` / `/docs`**.
`docs/` is plain static HTML + JSON; there is no build step and no workflow.
