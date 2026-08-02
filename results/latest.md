<!-- run_id=36b128a1-7e36-4530-8eb9-c8f20ceddcd3 source_envelope_sha256=f8957b5ac075f093f5cbdab111b0d8d2216f289f4c31735f569871307ab492d6 -->
# Fission Benchmark Report

**Measured at:** 2026-08-02T11:44:24.894760Z
**Rendered at:** 2026-08-02 11:48 UTC
**Corpus:** `dev`
**Functions evaluated:** 36

---

## ✅ VALID RUN

> Fission 210/216 (97.2%), all-backend 425/432 (98.4%)

## MVP Summary — Standard set

> **Primary ranking axis:** semantic pass rate (original-binary oracle when available).
> **Also first-class:** coverage (attempted / adapter clean / boundary invalid / tested), fail taxonomy, runtime.
> **Secondary:** CFG match (attached when cfg_parity JSONL present).
> **Diagnostics only (non-ranking):** source similarity, AST similarity, readability proxies.
> Readability proxies are not a final score until the human validation study completes.

| Decompiler | Attempted | Adapter clean | Boundary invalid | Semantic tested | Semantic mean | Perfect | No wrapper | Fail taxonomy (top) | Mean time |
| ---|---|---|---|---|---|---|---|---|--- |
| **fission** | 216 | 210 | 5 | 210 | 62.5% | 110 | 0 | assertion_fail:46 · compile_error:26 · timeout:16 | 1779ms |
| **ghidra** | 216 | 215 | 1 | 215 | 76.8% | 163 | 0 | compile_error:22 · runtime_error:14 · assertion_fail:13 | 10862ms |

### Extension — Cross-compiler / opt

| Decompiler | Variant | Compiler | Opt | Tested | Semantic mean |
| ---|---|---|---|---|--- |
| fission | clang -O0 | clang | -O0 | 35 | 75.6% |
| fission | clang -O2 | clang | -O2 | 31 | 46.1% |
| fission | gcc -O0 | gcc | -O0 | 36 | 77.3% |
| fission | gcc -O2 | gcc | -O2 | 36 | 53.9% |
| fission | gcc-m32 -O0 | gcc-m32 | -O0 | 36 | 69.3% |
| fission | gcc-m32 -O2 | gcc-m32 | -O2 | 36 | 51.1% |
| ghidra | clang -O0 | clang | -O0 | 36 | 75.0% |
| ghidra | clang -O2 | clang | -O2 | 36 | 77.8% |
| ghidra | gcc -O0 | gcc | -O0 | 36 | 25.3% |
| ghidra | gcc -O2 | gcc | -O2 | 35 | 94.3% |
| ghidra | gcc-m32 -O0 | gcc-m32 | -O0 | 36 | 94.4% |
| ghidra | gcc-m32 -O2 | gcc-m32 | -O2 | 36 | 94.4% |

### Secondary — CFG match

| Decompiler | Match | Mismatch | Match rate |
| ---|---|---|--- |
| fission | 39 | 1 | 97.5% |

### Diagnostics note

> Source similarity is **not** listed in the MVP table. It remains on per-function rows for triage only.

---

## Per-Function Results

### `accumulate_pairs` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.069 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 717ms | ✅ |
| ghidra | gcc -O0 | 1.000 | 0.517 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 7340ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.157 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1451ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.120 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7617ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.178 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1672ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.787 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6803ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.168 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1713ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.120 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11370ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.757 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11611ms | ✅ |
| fission | clang -O0 | 0.600 | 0.115 | 60.0% (3/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 601ms | 🟤 assert |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 1636ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.047 | 0.0% (0/5) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 16 | 9862ms | 🔴 compile |

### `add_ints` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.333 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 2360ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.431 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2236ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.739 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 5658ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.604 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 2397ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.943 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5643ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.604 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 911ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.943 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 7718ms | ✅ |
| fission | clang -O0 | 1.000 | 0.342 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 797ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.761 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 7695ms | ✅ |
| fission | clang -O2 | 1.000 | 0.431 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 842ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 6756ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.678 | 0.0% (0/5) | #2 | 0 | 1 | GNR 0.57<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 4 | 5653ms | 🟤 assert |

### `apply_binop` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.103 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.57<br>expr 0.58<br>cf 1.00<br>art 0 | 2360ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.402 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 2236ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.109 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.88<br>type 0.60<br>expr 0.74<br>cf 1.00<br>art 0 | 2397ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.658 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5643ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.413 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 911ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.615 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7718ms | ✅ |
| fission | clang -O0 | 1.000 | 0.128 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.73<br>type 0.56<br>expr 0.70<br>cf 1.00<br>art 0 | 797ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.535 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7695ms | ✅ |
| fission | clang -O2 | 1.000 | 0.424 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 842ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.615 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6756ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.395 | 0.0% (0/6) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 7 | 5653ms | 🔴 compile |
| ghidra | gcc -O2 | 0.000 | 0.198 | 0.0% (0/6) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 5658ms | 🔴 compile |

### `bounded_checksum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.098 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.62<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 5658ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.548 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 5643ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.286 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.22<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 7718ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.153 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.64<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 6756ms | ✅ |
| fission | gcc -O2 | 0.500 | 0.111 | 50.0% (3/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2236ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.167 | 0.095 | 16.7% (1/6) ⚠️intrin | #2 | 0 | 2 | GNR 0.11<br>type 0.50<br>expr 0.58<br>cf 1.00<br>art 1 | 911ms | 🟤 assert |
| fission | gcc -O0 | 0.000 | 0.064 | 0.0% (0/6) ⚠️intrin | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 2 | 2360ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.421 | 0.0% (0/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 5653ms | 🟠 runtime |
| fission | gcc-m32 -O0 | 0.000 | 0.082 | 0.0% (0/6) ⚠️intrin | #2 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 2 | 2397ms | 🔴 compile |
| fission | clang -O0 | 0.000 | 0.117 | 0.0% (0/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 797ms | 🟠 runtime |
| ghidra | clang -O0 | 0.000 | 0.319 | 0.0% (0/6) | #1 | 0 | 2 | GNR 0.30<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 7695ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.044 | 0.0% (0/6) | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 842ms | 🔴 compile |

### `bounded_tlv_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.093 | 100.0% (7/7) | #1 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1233ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.151 | 100.0% (7/7) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10969ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.084 | 100.0% (7/7) | #1 | 3 | 3 | GNR 0.58<br>type 0.50<br>expr 0.50<br>cf 0.67<br>art 0 | 600ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.363 | 100.0% (7/7) | #1 | 0 | 3 | GNR 0.22<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 10021ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.149 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.61<br>type 0.50<br>expr 0.56<br>cf 1.00<br>art 0 | 11878ms | ✅ |
| fission | clang -O0 | 1.000 | 0.096 | 100.0% (7/7) | #1 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 20302ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.363 | 100.0% (7/7) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 13587ms | ✅ |
| fission | gcc-m32 -O2 | 0.286 | 0.041 | 28.6% (2/7) | #2 | 6 | 2 | GNR 0.18<br>type 0.50<br>expr 0.47<br>cf 0.75<br>art 0 | 533ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.334 | 0.0% (0/7) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 7 | 10660ms | 🟠 runtime |
| fission | gcc -O2 | 0.000 | 0.040 | 0.0% (0/7) ⚠️intrin | #2 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 9 | 561ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 999ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.040 | 0.0% (0/7) | #1 | 2 | 7 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 16 | 10032ms | 🔴 compile |

### `bubble_sort` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc-m32 -O0 | 1.000 | 0.050 | 100.0% (5/5) | #1 | 2 | 4 | GNR 0.37<br>type 0.50<br>expr 0.40<br>cf 0.71<br>art 0 | 984ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.152 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.12<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 5205ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.190 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.12<br>type 0.50<br>expr 0.72<br>cf 1.00<br>art 0 | 5237ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.361 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.57<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 5812ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.100 | 100.0% (5/5) | #1 | 0 | 7 | GNR 0.74<br>type 0.50<br>expr 0.52<br>cf 1.00<br>art 0 | 8475ms | ✅ |
| fission | gcc -O0 | 0.800 | 0.054 | 80.0% (4/5) | #1 | 2 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 699ms | 🟤 assert |
| fission | clang -O0 | 0.800 | 0.090 | 80.0% (4/5) | #2 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1326ms | 🟤 assert |
| ghidra | gcc -O0 | 0.400 | 0.167 | 40.0% (2/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 15 | 7065ms | 🟤 assert |
| fission | gcc -O2 | 0.000 | 0.058 | 0.0% (0/5) | #1 | 3 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 664ms | 🔴 compile |
| ghidra | gcc -O2 | 0.000 | 0.131 | 0.0% (0/5) | #1 | 0 | 5 | GNR 0.26<br>type 0.42<br>expr 0.51<br>cf 1.00<br>art 2 | 8515ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.032 | 0.0% (0/5) | #2 | 3 | 4 | GNR 0.14<br>type 0.50<br>expr 0.53<br>cf 0.91<br>art 0 | 1404ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.032 | 0.0% (0/5) | #2 | 15 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1395ms | 🟠 runtime |

### `checksum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.111 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 978ms | ✅ |
| ghidra | gcc -O0 | 1.000 | 0.668 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 12428ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.081 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 926ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.129 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 13192ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.112 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.78<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 624ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.819 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 11094ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.147 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.24<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 670ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.116 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 11561ms | ✅ |
| fission | clang -O0 | 1.000 | 0.111 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 627ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.732 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 12672ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.144 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.71<br>type 0.50<br>expr 0.49<br>cf 1.00<br>art 0 | 12509ms | ✅ |
| fission | clang -O2 | 0.000 | 0.036 | 0.0% (0/5) | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 558ms | 🔴 compile |

### `clamp` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.144 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 978ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.112 | 100.0% (6/6) ⚠️intrin | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 926ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.582 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 13192ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.515 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 624ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.590 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 11094ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.199 | 100.0% (6/6) ⚠️intrin | #1 | 0 | 2 | GNR 0.29<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 1 | 670ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.731 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 11561ms | ✅ |
| fission | clang -O0 | 1.000 | 0.118 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 627ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.421 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.26<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 0 | 12672ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.731 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 12509ms | ✅ |
| fission | clang -O2 | 0.333 | 0.181 | 33.3% (2/6) | #2 | 0 | 1 | GNR 0.89<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 558ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.421 | 0.0% (0/6) | #2 | 0 | 2 | GNR 0.75<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 9 | 12428ms | 🟤 assert |

### `count_bits` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.336 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.92<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 978ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.265 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.33<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 926ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.609 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 13192ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.510 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.89<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 624ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.755 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 11094ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.421 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 670ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.609 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 11561ms | ✅ |
| fission | clang -O0 | 1.000 | 0.288 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.92<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 627ms | ✅ |
| fission | clang -O2 | 1.000 | 0.226 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.27<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 558ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.581 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.53<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 12509ms | ✅ |
| ghidra | gcc -O0 | 0.167 | 0.688 | 16.7% (1/6) | #2 | 0 | 2 | GNR 0.14<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 2 | 12428ms | 🟤 assert |
| ghidra | clang -O0 | 0.000 | 0.298 | 0.0% (0/6) | #2 | 0 | 2 | GNR 0.69<br>type 0.33<br>expr 0.78<br>cf 1.00<br>art 2 | 12672ms | 🟡 timeout |

### `crc32` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.062 | 100.0% (6/6) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1032ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.293 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.50<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 0 | 20313ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.400 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 19523ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.305 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.50<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 0 | 19794ms | ✅ |
| fission | clang -O0 | 1.000 | 0.045 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1248ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.474 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 17934ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.057 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.70<br>type 0.50<br>expr 0.50<br>cf 1.00<br>art 0 | 18133ms | ✅ |
| fission | clang -O2 | 0.333 | 0.063 | 33.3% (2/6) | #2 | 1 | 3 | GNR 0.06<br>type 0.50<br>expr 0.56<br>cf 1.00<br>art 0 | 975ms | 🟤 assert |
| fission | gcc -O2 | 0.167 | 0.060 | 16.7% (1/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 851ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.167 | 0.081 | 16.7% (1/6) | #2 | 2 | 3 | GNR 0.55<br>type 0.50<br>expr 0.65<br>cf 0.50<br>art 0 | 999ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.167 | 0.054 | 16.7% (1/6) | #2 | 0 | 4 | GNR 0.15<br>type 0.50<br>expr 0.66<br>cf 1.00<br>art 0 | 1004ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.343 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 20163ms | 🔴 compile |

### `dot_product_stride` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.073 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5658ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.566 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.12<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 5643ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.239 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.30<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 7718ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.494 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7695ms | ✅ |
| fission | gcc -O0 | 0.000 | 0.118 | 0.0% (0/5) | #1 | 1 | 3 | GNR 0.93<br>type 0.50<br>expr 0.80<br>cf 0.67<br>art 0 | 2360ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.474 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 5653ms | 🟠 runtime |
| fission | gcc -O2 | 0.000 | 0.072 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2236ms | 🔴 compile |
| fission | gcc-m32 -O0 | 0.000 | 0.163 | 0.0% (0/5) | #2 | 1 | 3 | GNR 0.91<br>type 0.50<br>expr 0.81<br>cf 0.67<br>art 0 | 2397ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.094 | 0.0% (0/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 911ms | 🟠 runtime |
| fission | clang -O0 | 0.000 | 0.086 | 0.0% (0/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 797ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 842ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.049 | 0.0% (0/5) | #1 | 1 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 13 | 6756ms | 🔴 compile |

### `factorial` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.239 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 699ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8515ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.579 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5205ms | ✅ |
| fission | clang -O0 | 1.000 | 0.209 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1326ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.504 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 5812ms | ✅ |
| ghidra | gcc -O0 | 0.400 | 0.335 | 40.0% (2/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 3 | 7065ms | 🟤 assert |
| fission | gcc -O2 | 0.400 | 0.153 | 40.0% (2/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 664ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.400 | 0.132 | 40.0% (2/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 984ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.400 | 0.026 | 40.0% (2/5) ⚠️intrin | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 16 | 1404ms | 🟤 assert |
| fission | clang -O2 | 0.400 | 0.288 | 40.0% (2/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1395ms | 🟤 assert |
| ghidra | gcc-m32 -O2 | 0.000 | 0.136 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5237ms | 🔴 compile |
| ghidra | clang -O2 | 0.000 | 0.290 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8475ms | ❌ |

### `fibonacci` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.222 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 699ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.218 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.59<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 8515ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.598 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.35<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 5205ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.260 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.64<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 5237ms | ✅ |
| fission | clang -O0 | 1.000 | 0.200 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.55<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 1326ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.484 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.40<br>expr 0.77<br>cf 1.00<br>art 1 | 5812ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.254 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.67<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 8475ms | ✅ |
| fission | gcc-m32 -O0 | 0.500 | 0.236 | 50.0% (3/6) | #2 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 984ms | 🟤 assert |
| fission | gcc -O2 | 0.333 | 0.138 | 33.3% (2/6) | #2 | 1 | 3 | GNR 0.10<br>type 0.50<br>expr 0.62<br>cf 1.00<br>art 0 | 664ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.333 | 0.190 | 33.3% (2/6) | #2 | 0 | 3 | GNR 0.21<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 1404ms | 🟤 assert |
| ghidra | gcc -O0 | 0.167 | 0.321 | 16.7% (1/6) | #2 | 0 | 2 | GNR 0.53<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 4 | 7065ms | 🟤 assert |
| fission | clang -O2 | 0.000 | 0.170 | 0.0% (0/6) | #2 | 1 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1395ms | 🟡 timeout |

### `find_pair_value` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.090 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 717ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7617ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.119 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.52<br>type 0.50<br>expr 0.54<br>cf 1.00<br>art 0 | 1672ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.695 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6803ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11370ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.472 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11611ms | ✅ |
| fission | clang -O2 | 1.000 | 0.106 | 100.0% (5/5) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1636ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.442 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9862ms | ✅ |
| fission | clang -O0 | 0.800 | 0.109 | 80.0% (4/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 601ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.342 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 7340ms | 🟠 runtime |
| fission | gcc -O2 | 0.000 | 0.175 | 0.0% (0/5) | #2 | 2 | 4 | GNR 0.47<br>type 0.50<br>expr 0.80<br>cf 0.71<br>art 0 | 1451ms | 🟡 timeout |
| fission | gcc-m32 -O2 | 0.000 | 0.154 | 0.0% (0/5) | #2 | 2 | 4 | GNR 0.36<br>type 0.50<br>expr 0.70<br>cf 0.71<br>art 0 | 1713ms | 🟡 timeout |

### `find_substring` 🔴 Fission-only gap
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.162 | 100.0% (6/6) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 25578ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.401 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.16<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 23290ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.204 | 100.0% (6/6) | #1 | 0 | 5 | GNR 0.42<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 17520ms | ✅ |
| fission | clang -O0 | 1.000 | 0.039 | 100.0% (6/6) | #1 | 11 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1381ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.223 | 100.0% (6/6) | #1 | 0 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11832ms | ✅ |
| fission | gcc-m32 -O2 | 0.500 | 0.051 | 50.0% (3/6) | #2 | 3 | 6 | GNR 0.27<br>type 0.50<br>expr 0.65<br>cf 0.80<br>art 0 | 1637ms | 🟤 assert |
| ghidra | gcc -O0 | 0.167 | 0.281 | 16.7% (1/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 10 | 26854ms | 🟤 assert |
| fission | gcc -O0 | 0.000 | 0.053 | 0.0% (0/6) | #2 | 6 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1368ms | 🟡 timeout |
| fission | gcc -O2 | 0.000 | 0.075 | 0.0% (0/6) | #2 | 2 | 6 | GNR 0.39<br>type 0.50<br>expr 0.67<br>cf 0.80<br>art 0 | 1205ms | 🔴 compile |
| fission | gcc-m32 -O0 | 0.000 | 0.088 | 0.0% (0/6) | #2 | 3 | 3 | GNR 0.35<br>type 0.50<br>expr 0.64<br>cf 0.75<br>art 0 | 1363ms | 🟡 timeout |
| ghidra | clang -O0 | 0.000 | 0.142 | 0.0% (0/6) | #2 | 0 | 5 | GNR 0.43<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 11926ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.057 | 0.0% (0/6) | #2 | 7 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1264ms | 🔴 compile |

### `kv_lookup` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.064 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2360ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.146 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5658ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.088 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.52<br>type 0.50<br>expr 0.54<br>cf 1.00<br>art 0 | 2397ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.681 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5643ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.189 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7718ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.455 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7695ms | ✅ |
| fission | clang -O2 | 1.000 | 0.108 | 100.0% (6/6) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 842ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.412 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6756ms | ✅ |
| fission | clang -O0 | 0.833 | 0.106 | 83.3% (5/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 797ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.316 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 5653ms | 🟠 runtime |
| fission | gcc -O2 | 0.000 | 0.148 | 0.0% (0/6) | #2 | 2 | 4 | GNR 0.47<br>type 0.50<br>expr 0.80<br>cf 0.71<br>art 0 | 2236ms | 🟡 timeout |
| fission | gcc-m32 -O2 | 0.000 | 0.141 | 0.0% (0/6) | #2 | 2 | 4 | GNR 0.36<br>type 0.50<br>expr 0.70<br>cf 0.71<br>art 0 | 911ms | 🟡 timeout |

### `linear_search` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.203 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.63<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 699ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.660 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8515ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.205 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.58<br>cf 1.00<br>art 0 | 984ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.617 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 5205ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.688 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.47<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 5237ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.401 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 5812ms | ✅ |
| fission | clang -O2 | 1.000 | 0.171 | 100.0% (6/6) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1395ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.317 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.47<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 8475ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.371 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 7065ms | 🟠 runtime |
| fission | gcc -O2 | 0.000 | 0.222 | 0.0% (0/6) | #2 | 2 | 4 | GNR 0.42<br>type 0.50<br>expr 0.83<br>cf 0.71<br>art 0 | 664ms | 🟡 timeout |
| fission | gcc-m32 -O2 | 0.000 | 0.194 | 0.0% (0/6) | #2 | 2 | 4 | GNR 0.42<br>type 0.50<br>expr 0.83<br>cf 0.71<br>art 0 | 1404ms | 🟡 timeout |
| fission | clang -O0 | 0.000 | 0.200 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1326ms | 🟡 timeout |

### `list_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.171 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.67<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 2360ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.453 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.91<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 5658ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.099 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.67<br>type 0.50<br>expr 0.53<br>cf 1.00<br>art 0 | 2397ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.652 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 5643ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.573 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 7718ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.573 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 1 | 6756ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.595 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 2 | 5653ms | 🟠 runtime |
| fission | gcc -O2 | 0.000 | 0.411 | 0.0% (0/5) | #2 | 0 | 3 | GNR 0.33<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 2236ms | 🟡 timeout |
| fission | gcc-m32 -O2 | 0.000 | 0.478 | 0.0% (0/5) | #2 | 0 | 3 | GNR 0.33<br>type 0.50<br>expr 0.84<br>cf 1.00<br>art 0 | 911ms | 🟡 timeout |
| fission | clang -O0 | 0.000 | 0.144 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 797ms | 🟠 runtime |
| ghidra | clang -O0 | 0.000 | 0.353 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 7695ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.411 | 0.0% (0/5) | #2 | 0 | 3 | GNR 0.33<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 842ms | 🟡 timeout |

### `manipulate_bitfields` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.312 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 19080ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.312 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 14776ms | ✅ |
| fission | gcc -O2 | 0.800 | 0.097 | 80.0% (4/5) | #2 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3224ms | 🟤 assert |
| fission | clang -O0 | 0.800 | 0.051 | 80.0% (4/5) ⚠️intrin | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 3213ms | 🟤 assert |
| fission | clang -O2 | 0.800 | 0.085 | 80.0% (4/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2786ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.200 | 0.069 | 20.0% (1/5) ⚠️intrin | #2 | 0 | 2 | GNR 0.14<br>type 0.50<br>expr 0.50<br>cf 1.00<br>art 1 | 2311ms | 🟤 assert |
| fission | gcc -O0 | 0.000 | 0.036 | 0.0% (0/5) ⚠️intrin | #1 | 0 | 2 | GNR 0.08<br>type 0.50<br>expr 0.46<br>cf 1.00<br>art 13 | 3653ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.119 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 18013ms | 🟠 runtime |
| fission | gcc-m32 -O0 | 0.000 | 0.026 | 0.0% (0/5) ⚠️intrin | #1 | 0 | 2 | GNR 0.09<br>type 0.50<br>expr 0.46<br>cf 1.00<br>art 13 | 3646ms | 🔴 compile |
| ghidra | gcc-m32 -O0 | 0.000 | 0.208 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 17714ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.205 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 16664ms | 🔴 compile |
| ghidra | clang -O2 | 0.000 | 0.341 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 16565ms | 🔴 compile |

### `matrix_multiply` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.043 | 100.0% (5/5) | #1 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 3653ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.206 | 100.0% (5/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 19080ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.489 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 17714ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.163 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.38<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 14776ms | ✅ |
| fission | clang -O0 | 1.000 | 0.063 | 100.0% (5/5) | #1 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 3213ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.701 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 16664ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.197 | 100.0% (5/5) | #1 | 0 | 6 | GNR 0.46<br>type 0.50<br>expr 0.50<br>cf 1.00<br>art 0 | 16565ms | ✅ |
| fission | gcc -O2 | 0.200 | 0.052 | 20.0% (1/5) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3224ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.387 | 0.0% (0/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 18013ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.000 | 0.033 | 0.0% (0/5) | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 3646ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.029 | 0.0% (0/5) | #2 | 3 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 2311ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.053 | 0.0% (0/5) | #2 | 9 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 2786ms | 🔴 compile |

### `mixed_width_accumulate` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.205 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.15<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 10969ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.629 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.30<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 10021ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.187 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.33<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 11878ms | ✅ |
| fission | gcc -O0 | 0.500 | 0.092 | 50.0% (3/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1233ms | 🟤 assert |
| fission | gcc -O2 | 0.500 | 0.163 | 50.0% (3/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 561ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.500 | 0.056 | 50.0% (3/6) | #2 | 0 | 4 | GNR 0.60<br>type 0.50<br>expr 0.52<br>cf 1.00<br>art 0 | 600ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.333 | 0.046 | 33.3% (2/6) | #2 | 0 | 3 | GNR 0.24<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 533ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.181 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 10660ms | 🟠 runtime |
| fission | clang -O0 | 0.000 | 0.064 | 0.0% (0/6) ⚠️intrin | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 20302ms | 🟡 timeout |
| ghidra | clang -O0 | 0.000 | 0.328 | 0.0% (0/6) | #1 | 0 | 3 | GNR 0.24<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 13587ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 999ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.044 | 0.0% (0/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 10032ms | 🔴 compile |

### `mul_ints` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.237 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2360ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.429 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2236ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.739 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 5658ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.470 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2397ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5643ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.470 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 911ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.943 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 7718ms | ✅ |
| fission | clang -O0 | 1.000 | 0.243 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 797ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.761 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 7695ms | ✅ |
| fission | clang -O2 | 1.000 | 0.429 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 842ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 6756ms | ✅ |
| ghidra | gcc -O0 | 0.200 | 0.678 | 20.0% (1/5) | #2 | 0 | 1 | GNR 0.57<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 4 | 5653ms | 🟤 assert |

### `overlap_move` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.050 | 100.0% (6/6) | #1 | 4 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1233ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.068 | 100.0% (6/6) | #1 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 561ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.236 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 10969ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.073 | 100.0% (6/6) | #1 | 3 | 3 | GNR 0.64<br>type 0.50<br>expr 0.50<br>cf 0.83<br>art 0 | 600ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.528 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 10021ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.034 | 100.0% (6/6) | #1 | 1 | 4 | GNR 0.36<br>type 0.50<br>expr 0.45<br>cf 0.83<br>art 0 | 533ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.238 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 11878ms | ✅ |
| fission | clang -O0 | 1.000 | 0.040 | 100.0% (6/6) | #1 | 3 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 20302ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.398 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 13587ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.048 | 100.0% (6/6) | #1 | 3 | 8 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 43 | 10032ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.269 | 0.0% (0/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 10660ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 999ms | ❌ Decompiler returned whole-prog |

### `pointer_stride_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.290 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 717ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.292 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1451ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.609 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.29<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 7617ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.342 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.64<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 1672ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.674 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 6803ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.316 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.20<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 1713ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.648 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.29<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 11370ms | ✅ |
| fission | clang -O0 | 1.000 | 0.129 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 601ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.489 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 11611ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.079 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9862ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.259 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 7340ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.024 | 0.0% (0/5) ⚠️intrin | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 1 | 1636ms | 🔴 compile |

### `power` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.243 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 699ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.203 | 100.0% (6/6) | #1 | 2 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 664ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.392 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8515ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.492 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5205ms | ✅ |
| fission | clang -O0 | 1.000 | 0.231 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1326ms | ✅ |
| fission | clang -O2 | 1.000 | 0.213 | 100.0% (6/6) | #1 | 1 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1395ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.264 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8475ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.374 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 7065ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.000 | 0.073 | 0.0% (0/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 984ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.064 | 0.0% (0/6) | #1 | 1 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1404ms | 🔴 compile |
| ghidra | gcc-m32 -O2 | 0.000 | 0.249 | 0.0% (0/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5237ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.215 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 5812ms | 🔴 compile |

### `process_code` 🔴 Fission-only gap
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O2 | 1.000 | 0.069 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.24<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 664ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.286 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 8515ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.111 | 100.0% (5/5) | #1 | 0 | 6 | GNR 0.89<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 984ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.166 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.44<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 5205ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.286 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 5237ms | ✅ |
| fission | clang -O0 | 1.000 | 0.139 | 100.0% (5/5) | #1 | 2 | 3 | GNR 0.89<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 1326ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.149 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.41<br>type 0.38<br>expr 0.80<br>cf 1.00<br>art 1 | 5812ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.309 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 8475ms | ✅ |
| fission | gcc-m32 -O2 | 0.800 | 0.087 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.25<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 1404ms | 🟤 assert |
| fission | clang -O2 | 0.600 | 0.126 | 60.0% (3/5) | #2 | 0 | 5 | GNR 0.24<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 1395ms | 🟤 assert |
| ghidra | gcc -O0 | 0.200 | 0.157 | 20.0% (1/5) | #1 | 0 | 4 | GNR 0.88<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 8 | 7065ms | 🟤 assert |
| fission | gcc -O0 | 0.000 | 0.103 | 0.0% (0/5) | #2 | 2 | 3 | GNR 0.89<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 699ms | ❌ |

### `rc4_crypt` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.032 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1032ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.016 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 851ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.234 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.44<br>type 0.50<br>expr 0.62<br>cf 1.00<br>art 0 | 20313ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.030 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.41<br>type 0.50<br>expr 0.40<br>cf 1.00<br>art 0 | 999ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.440 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.10<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 19523ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.022 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.27<br>type 0.50<br>expr 0.45<br>cf 1.00<br>art 0 | 1004ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.247 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.57<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 19794ms | ✅ |
| fission | clang -O0 | 1.000 | 0.072 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1248ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.384 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.09<br>type 0.50<br>expr 0.62<br>cf 1.00<br>art 0 | 17934ms | ✅ |
| fission | clang -O2 | 1.000 | 0.027 | 100.0% (5/5) | #1 | 1 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 975ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.162 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.75<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 18133ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.292 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 17 | 20163ms | 🟠 runtime |

### `rc4_init` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.544 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.11<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 19523ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.233 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.69<br>type 0.50<br>expr 0.61<br>cf 1.00<br>art 0 | 19794ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.236 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.24<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 17934ms | ✅ |
| fission | gcc -O0 | 0.200 | 0.042 | 20.0% (1/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1032ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.200 | 0.032 | 20.0% (1/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 999ms | 🟤 assert |
| fission | clang -O0 | 0.200 | 0.032 | 20.0% (1/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1248ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.362 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 20163ms | 🟠 runtime |
| fission | gcc -O2 | 0.000 | 0.022 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 851ms | 🔴 compile |
| ghidra | gcc -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 20313ms | ❌ Decompiler returned whole-prog |
| fission | gcc-m32 -O2 | 0.000 | 0.100 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1004ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.033 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 975ms | 🔴 compile |
| ghidra | clang -O2 | 0.000 | 0.081 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 33 | 18133ms | 🔴 compile |

### `reverse_in_place` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.059 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 717ms | ✅ |
| ghidra | gcc -O0 | 1.000 | 0.323 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.60<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 11 | 7340ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.221 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 7617ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.073 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.43<br>type 0.50<br>expr 0.38<br>cf 1.00<br>art 0 | 1672ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.339 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.25<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 6803ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.221 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 11370ms | ✅ |
| fission | clang -O0 | 1.000 | 0.100 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 601ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.325 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.26<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 11611ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.146 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9862ms | ✅ |
| fission | gcc-m32 -O2 | 0.400 | 0.130 | 40.0% (2/5) | #2 | 2 | 2 | GNR 0.27<br>type 0.50<br>expr 0.67<br>cf 0.60<br>art 0 | 1713ms | 🟤 assert |
| fission | gcc -O2 | 0.200 | 0.124 | 20.0% (1/5) | #2 | 2 | 2 | GNR 0.28<br>type 0.50<br>expr 0.68<br>cf 0.60<br>art 0 | 1451ms | 🟤 assert |
| fission | clang -O2 | 0.000 | 0.072 | 0.0% (0/5) | #2 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1636ms | 🔴 compile |

### `reverse_string` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.098 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1368ms | ✅ |
| ghidra | gcc -O0 | 1.000 | 0.251 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 26854ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.233 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 25578ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.067 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.52<br>type 0.50<br>expr 0.53<br>cf 1.00<br>art 0 | 1363ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.353 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.16<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 23290ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.263 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 17520ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.256 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.14<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 11926ms | ✅ |
| fission | clang -O2 | 1.000 | 0.103 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.24<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 1264ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.252 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.12<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 11832ms | ✅ |
| fission | clang -O0 | 0.600 | 0.145 | 60.0% (3/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1381ms | 🟤 assert |
| fission | gcc -O2 | 0.000 | 0.046 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1205ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.042 | 0.0% (0/5) | #2 | 0 | 2 | GNR 0.16<br>type 0.50<br>expr 0.57<br>cf 1.00<br>art 0 | 1637ms | 🔴 compile |

### `rolling_hash32`
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O0 | 1.000 | 0.414 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 10660ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.139 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 561ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.303 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 10969ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.783 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 10021ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.190 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 533ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.303 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 11878ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.558 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 13587ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.340 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.64<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 10032ms | ✅ |
| fission | gcc -O0 | 0.333 | 0.118 | 33.3% (2/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1233ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.167 | 0.113 | 16.7% (1/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 600ms | 🟤 assert |
| fission | clang -O0 | 0.167 | 0.096 | 16.7% (1/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 20302ms | 🟤 assert |
| fission | clang -O2 | 0.000 | 0.087 | 0.0% (0/6) | #2 | 1 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 999ms | 🟠 runtime |

### `rotate_words` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.217 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.46<br>type 0.50<br>expr 0.66<br>cf 1.00<br>art 0 | 10969ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.040 | 100.0% (6/6) ⚠️intrin | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.56<br>cf 1.00<br>art 4 | 533ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.213 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.44<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 11878ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.152 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.72<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 10032ms | ✅ |
| fission | clang -O2 | 0.833 | 0.048 | 83.3% (5/6) ⚠️intrin | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 7 | 999ms | 🟤 assert |
| fission | clang -O0 | 0.667 | 0.044 | 66.7% (4/6) ⚠️intrin | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 13 | 20302ms | 🟤 assert |
| fission | gcc -O2 | 0.500 | 0.038 | 50.0% (3/6) ⚠️intrin | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 561ms | 🟤 assert |
| fission | gcc -O0 | 0.000 | 0.043 | 0.0% (0/6) ⚠️intrin | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 3 | 1233ms | ❌ |
| ghidra | gcc -O0 | 0.000 | 0.337 | 0.0% (0/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 10660ms | 🟠 runtime |
| fission | gcc-m32 -O0 | 0.000 | 0.067 | 0.0% (0/6) ⚠️intrin | #1 | 0 | 4 | GNR 0.31<br>type 0.50<br>expr 0.40<br>cf 1.00<br>art 3 | 600ms | 🔴 compile |
| ghidra | gcc-m32 -O0 | 0.000 | 0.398 | 0.0% (0/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10021ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.344 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 13587ms | 🔴 compile |

### `saturating_add` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.137 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.44<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 978ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.606 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.40<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 13192ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.317 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.94<br>type 0.50<br>expr 0.53<br>cf 1.00<br>art 0 | 624ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.246 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.47<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 11094ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.606 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.40<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 11561ms | ✅ |
| fission | clang -O0 | 1.000 | 0.141 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.66<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 627ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.315 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.42<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 12672ms | ✅ |
| fission | gcc -O2 | 0.800 | 0.319 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.68<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 926ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.800 | 0.282 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.55<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 670ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.252 | 0.0% (0/5) | #2 | 0 | 3 | GNR 0.84<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 8 | 12428ms | 🟤 assert |
| fission | clang -O2 | 0.000 | 0.396 | 0.0% (0/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 558ms | ❌ |
| ghidra | clang -O2 | 0.000 | 0.432 | 0.0% (0/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 12509ms | ❌ |

### `signum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.335 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 978ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.133 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.24<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 926ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.492 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 13192ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.580 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 624ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.611 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.56<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 11094ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.421 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 670ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.583 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.84<br>cf 1.00<br>art 0 | 11561ms | ✅ |
| fission | clang -O0 | 1.000 | 0.340 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 627ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.523 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.50<br>type 0.38<br>expr 0.87<br>cf 1.00<br>art 1 | 12672ms | ✅ |
| fission | clang -O2 | 1.000 | 0.117 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.80<br>type 0.50<br>expr 0.72<br>cf 1.00<br>art 0 | 558ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.624 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 12509ms | ✅ |
| ghidra | gcc -O0 | 0.400 | 0.375 | 40.0% (2/5) | #2 | 0 | 3 | GNR 0.80<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 3 | 12428ms | 🟤 assert |

### `state_machine_score` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.048 | 100.0% (7/7) | #1 | 18 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1233ms | ✅ |
| ghidra | gcc -O0 | 1.000 | 0.107 | 100.0% (7/7) | #1 | 2 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 5 | 10660ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.125 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.72<br>type 0.50<br>expr 0.61<br>cf 0.87<br>art 0 | 10969ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.054 | 100.0% (7/7) | #1 | 18 | 3 | GNR 0.58<br>type 0.50<br>expr 0.57<br>cf 0.37<br>art 0 | 600ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.117 | 100.0% (7/7) | #1 | 2 | 6 | GNR 0.16<br>type 0.50<br>expr 0.66<br>cf 0.52<br>art 0 | 10021ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.125 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.72<br>type 0.50<br>expr 0.61<br>cf 0.87<br>art 0 | 11878ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.237 | 100.0% (7/7) | #1 | 2 | 5 | GNR 0.74<br>type 0.50<br>expr 0.56<br>cf 0.48<br>art 0 | 10032ms | ✅ |
| fission | gcc -O2 | 0.000 | 0.081 | 0.0% (0/7) | #2 | 5 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 561ms | 🟡 timeout |
| fission | gcc-m32 -O2 | 0.000 | 0.078 | 0.0% (0/7) | #2 | 6 | 4 | GNR 0.16<br>type 0.50<br>expr 0.57<br>cf 0.62<br>art 0 | 533ms | 🟡 timeout |
| fission | clang -O0 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 20302ms | ❌ preview_timeout: Rust-Sleigh r |
| ghidra | clang -O0 | 0.000 | 0.146 | 0.0% (0/7) | #1 | 0 | 4 | GNR 0.11<br>type 0.50<br>expr 0.58<br>cf 0.67<br>art 0 | 13587ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.070 | 0.0% (0/7) | #2 | 3 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 999ms | 🟠 runtime |

### `sum_array` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.155 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 717ms | ✅ |
| ghidra | gcc -O0 | 1.000 | 0.648 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 7340ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.357 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1451ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.171 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 7617ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.225 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.68<br>type 0.50<br>expr 0.55<br>cf 1.00<br>art 0 | 1672ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.833 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 6803ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.363 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1713ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.171 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 11370ms | ✅ |
| fission | clang -O0 | 1.000 | 0.141 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 601ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.733 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 11611ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.030 | 100.0% (5/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9862ms | ✅ |
| fission | clang -O2 | 0.000 | 0.012 | 0.0% (0/5) | #2 | 6 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1636ms | 🔴 compile |

---

## Overfitting Analysis

Functions where **all** decompilers scored below 0.3 are marked as objectively hard.
Functions where **only Fission** scored below 0.3 are marked as quality gaps.

**Fission quality gaps (1):** `dot_product_stride`