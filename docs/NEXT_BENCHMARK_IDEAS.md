# Next benchmark ideas (integrated workspace)

This repo is a **multi-layer measurement workspace**. Status below reflects
implementation as of the full extension pass (not only MVP semantic).

## Implemented (active)

| Track | Module / surface | Headline? |
|-------|------------------|-----------|
| Assembly / pcode / CFG / FD | `runner.run_parity` | Yes (strict dual metrics) |
| ABI | `abi_parity` + `/abi` | Extension |
| Type recovery (name-level) | `type_parity` + `/types` | Extension |
| Call-graph callees | `callgraph_parity` + `/callgraph` | Extension |
| String xrefs | `string_recovery` + `/strings` | Extension (Fission empty honest) |
| Data-flow sinks | `dataflow_parity` + `/dataflow` | Extension |
| SEH flags surface | `seh_parity` + `/seh` | Extension (flags-only) |
| Strip discovery + Δ | `strip_track` + `semantic_delta` | Extension |
| Opt cliff | `opt_cliff` from envelopes | Extension |
| Throughput p50/p95 | `throughput` | Extension |
| PR canary | `scripts/pr_canary.sh` | CI helper |
| Official publication | `publication_gate` | Release gate |
| Golden canaries | `golden_repros` | Meta locks |
| Readability proxies | `runner/readability.py` | Evidence only |
| Human study pack | `benchmark/readability/study_pack` | Scaffold for Phase 3 |
| **Bare-compile rate** | `runner/bare_compile.py` + summary EXT | Diagnostic only |
| **Readability axis (goto/temp/flag)** | `summary.extensions.readability_axis` | Diagnostic only |
| **Track / ISA / format pivots** | `summary.extensions.tracks` | Diagnostic only |
| **Advanced pattern corpus** | `corpus/dev/source/advanced_patterns.c` | Semantic matrix |
| **Dashboard Quality EXT** | `/quality` | Non-ranking UI |
| **Compiler-matched source CFG** | preprocessed TU + GED provenance | Diagnostic ground truth |
| **Resumable matrix execution** | row checkpoint + metric content cache | Infra reliability |
| **Public re-evaluation kit** | binaries + rows + source CFG + manifest | Release artifact |

Unified extension runner:

```bash
python -m runner.run_extensions --corpus dev --limit 20
```

## Deepened (this pass)

1. **Struct field IoU** — `structs[].fields[{offset,size,name,type}]` + `field_layout_jaccard`.
2. **RUNTIME_FUNCTION** — PE `.pdata` parser (`pe_exceptions` / Ghidra `.pdata` walk / Fission `pe_helpers`).
3. **Fission strings** — PE string pool + disasm immediate xref + decomp literals.
4. **Realworld multi-TU** — `util_lib.c` + `util_main.c` PE (+strip) via `build_extension_corpora.py`.
5. **Human study Phase 3** — protocol, answer schema, `analyze_readability_study.py` (composite still forbidden).
6. **Multi-ISA ELF** — clang `hello_elf_x86_64` fixture; arm64 still needs cross sysroot.
7. **Obfuscation** — CFF toy PE under `corpus/adversarial/`.
8. **Full-8 official** — `scripts/run_official_profiles.sh full` + `holdout_full8_latest.json` run path.

## Remaining research depth

- Arm64 multi-ISA with real sysroot / oracle ABI profiles.
- True third-party redistributable PE (license review).
- Human pilot data collection (N≥12).
- Fission native type recovery (beyond known-layout priors).
- Full-8 **dev** official green (wider adapter residuals).

## Design rules

1. Own a stage name and JSONL under `results/<stage>/`.
2. Ghidra (or stronger) for structural layers; **original binary** for semantics.
3. Separate infra failure from quality mismatch.
4. Golden canaries before corpus breadth.
5. Dashboard: rates + denominators, no mystery composite.
