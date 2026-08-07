<!-- run_id=3cfcd867-88f0-409a-940d-a3ecd85c5f8f source_envelope_sha256=6e325505f0dfacef4ca870f1f808d31a06ec21a4db31833117fec431ff0425a4 -->
# Fission Benchmark Report

**Measured at:** 2026-08-07T18:14:41.731588Z
**Rendered at:** 2026-08-07 18:27 UTC
**Corpus:** `dev`
**Functions evaluated:** 36

---

## ✅ VALID RUN

> Fission 211/216 (97.7%), all-backend 426/432 (98.6%)

## MVP Summary — Standard set

> **Primary ranking axis:** semantic pass rate (original-binary oracle when available).
> **Also first-class:** coverage (attempted / adapter clean / boundary invalid / tested), fail taxonomy, runtime.
> **Secondary:** CFG match (attached when cfg_parity JSONL present).
> **Diagnostics only (non-ranking):** source similarity, AST similarity, readability proxies.
> Readability proxies are not a final score until the human validation study completes.

| Decompiler | Attempted | Adapter clean | Boundary invalid | Semantic tested | Semantic mean | Perfect | No wrapper | Fail taxonomy (top) | Mean time |
| ---|---|---|---|---|---|---|---|---|--- |
| **fission** | 216 | 211 | 5 | 211 | 67.0% | 118 | 0 | assertion_fail:57 · compile_error:20 · runtime_error:10 | 2019ms |
| **ghidra** | 216 | 215 | 1 | 215 | 72.2% | 156 | 0 | oracle_error:37 · compile_error:20 · whole_program_output:1 | 9069ms |

### Extension — Cross-compiler / opt

| Decompiler | Variant | Compiler | Opt | Tested | Semantic mean |
| ---|---|---|---|---|--- |
| fission | clang -O0 | clang | -O0 | 36 | 78.6% |
| fission | clang -O2 | clang | -O2 | 31 | 42.3% |
| fission | gcc -O0 | gcc | -O0 | 36 | 84.7% |
| fission | gcc -O2 | gcc | -O2 | 36 | 62.4% |
| fission | gcc-m32 -O0 | gcc-m32 | -O0 | 36 | 79.4% |
| fission | gcc-m32 -O2 | gcc-m32 | -O2 | 36 | 54.2% |
| ghidra | clang -O0 | clang | -O0 | 36 | 72.2% |
| ghidra | clang -O2 | clang | -O2 | 36 | 80.6% |
| ghidra | gcc -O0 | gcc | -O0 | 36 | 0.0% |
| ghidra | gcc -O2 | gcc | -O2 | 35 | 91.7% |
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
| fission | gcc -O0 | 1.000 | 0.131 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1525ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.157 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1430ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.120 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8255ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.229 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 574ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.787 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5060ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.168 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1413ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.120 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8415ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.757 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8207ms | ✅ |
| fission | clang -O0 | 0.600 | 0.115 | 60.0% (3/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2077ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.517 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 8579ms | ❌ |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 979ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.047 | 0.0% (0/5) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 16 | 6250ms | 🔴 compile |

### `add_ints` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.333 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 755ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.431 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3905ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.739 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 3709ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.604 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 1236ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.943 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5581ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.943 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5116ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.604 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 946ms | ✅ |
| fission | clang -O0 | 1.000 | 0.342 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 922ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.761 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5761ms | ✅ |
| fission | clang -O2 | 1.000 | 0.431 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1042ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 8700ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.678 | 0.0% | #2 | 0 | 1 | GNR 0.57<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 4 | 5531ms | ❌ |

### `apply_binop` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.103 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.57<br>expr 0.58<br>cf 1.00<br>art 0 | 755ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.402 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 3905ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.109 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.88<br>type 0.60<br>expr 0.74<br>cf 1.00<br>art 0 | 1236ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.658 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5581ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.615 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5116ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.413 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 946ms | ✅ |
| fission | clang -O0 | 1.000 | 0.128 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.73<br>type 0.56<br>expr 0.70<br>cf 1.00<br>art 0 | 922ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.535 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5761ms | ✅ |
| fission | clang -O2 | 1.000 | 0.424 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 1042ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.615 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8700ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.395 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 7 | 5531ms | ❌ |
| ghidra | gcc -O2 | 0.000 | 0.198 | 0.0% (0/6) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 3709ms | 🔴 compile |

### `bounded_checksum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.098 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.62<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 3709ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.548 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 5581ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.286 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.22<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 5116ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.153 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.64<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 8700ms | ✅ |
| fission | gcc-m32 -O0 | 0.667 | 0.128 | 66.7% (4/6) | #2 | 0 | 2 | GNR 0.38<br>type 0.50<br>expr 0.49<br>cf 1.00<br>art 0 | 1236ms | 🟤 assert |
| fission | gcc -O0 | 0.500 | 0.086 | 50.0% (3/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 755ms | 🟤 assert |
| fission | gcc -O2 | 0.500 | 0.118 | 50.0% (3/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3905ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.167 | 0.089 | 16.7% (1/6) | #2 | 0 | 2 | GNR 0.21<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 946ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.421 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 5531ms | ❌ |
| fission | clang -O0 | 0.000 | 0.117 | 0.0% (0/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 922ms | 🟠 runtime |
| ghidra | clang -O0 | 0.000 | 0.319 | 0.0% (0/6) | #1 | 0 | 2 | GNR 0.30<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 5761ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.049 | 0.0% (0/6) | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1042ms | 🔴 compile |

### `bounded_tlv_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.078 | 100.0% (7/7) | #1 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1477ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.151 | 100.0% (7/7) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6682ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.363 | 100.0% (7/7) | #1 | 0 | 3 | GNR 0.22<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 6283ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.074 | 100.0% (7/7) | #1 | 3 | 3 | GNR 0.58<br>type 0.50<br>expr 0.52<br>cf 0.67<br>art 0 | 917ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.149 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.61<br>type 0.50<br>expr 0.56<br>cf 1.00<br>art 0 | 10462ms | ✅ |
| fission | clang -O0 | 1.000 | 0.089 | 100.0% (7/7) | #1 | 3 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1315ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.363 | 100.0% (7/7) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9312ms | ✅ |
| fission | gcc -O2 | 0.429 | 0.036 | 42.9% (3/7) | #2 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1493ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.286 | 0.038 | 28.6% (2/7) | #2 | 6 | 2 | GNR 0.25<br>type 0.50<br>expr 0.48<br>cf 0.75<br>art 0 | 1718ms | 🟤 assert |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 4720ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.040 | 0.0% (0/7) | #1 | 2 | 7 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 16 | 4834ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.334 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 7 | 10755ms | ❌ |

### `bubble_sort` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc-m32 -O0 | 1.000 | 0.050 | 100.0% (5/5) | #1 | 2 | 4 | GNR 0.37<br>type 0.50<br>expr 0.43<br>cf 0.71<br>art 0 | 1514ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.152 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.12<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 4603ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.190 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.12<br>type 0.50<br>expr 0.72<br>cf 1.00<br>art 0 | 7062ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.361 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.57<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 7064ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.100 | 100.0% (5/5) | #1 | 0 | 7 | GNR 0.74<br>type 0.50<br>expr 0.52<br>cf 1.00<br>art 0 | 4900ms | ✅ |
| fission | gcc -O0 | 0.800 | 0.054 | 80.0% (4/5) | #1 | 2 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1281ms | 🟤 assert |
| fission | clang -O0 | 0.800 | 0.090 | 80.0% (4/5) | #2 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1250ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.167 | 0.0% | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 15 | 6946ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.058 | 0.0% (0/5) | #1 | 3 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 424ms | 🔴 compile |
| ghidra | gcc -O2 | 0.000 | 0.131 | 0.0% (0/5) | #1 | 0 | 5 | GNR 0.26<br>type 0.42<br>expr 0.51<br>cf 1.00<br>art 2 | 6429ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.032 | 0.0% (0/5) | #2 | 3 | 4 | GNR 0.14<br>type 0.50<br>expr 0.57<br>cf 0.91<br>art 0 | 1257ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.033 | 0.0% (0/5) | #2 | 15 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1344ms | 🟠 runtime |

### `checksum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | clang -O0 | 1.000 | 0.121 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5379ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.732 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 5164ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.144 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.71<br>type 0.50<br>expr 0.49<br>cf 1.00<br>art 0 | 12470ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.146 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1269ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.081 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1863ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.129 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 7988ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.819 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 5755ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.169 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.78<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 1600ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.147 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.24<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 1140ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.116 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 7361ms | ✅ |
| fission | clang -O2 | 0.000 | 0.036 | 0.0% (0/5) | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1832ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.668 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 8288ms | ❌ |

### `clamp` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | clang -O0 | 1.000 | 0.118 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 5379ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.421 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.26<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 0 | 5164ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.731 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 12470ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.144 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 1269ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.104 | 100.0% (6/6) ⚠️intrin | #1 | 0 | 1 | GNR 0.71<br>type 0.50<br>expr 0.57<br>cf 1.00<br>art 1 | 1863ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.582 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 7988ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.590 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 5755ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.515 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 1600ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.731 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 7361ms | ✅ |
| fission | gcc-m32 -O2 | 0.833 | 0.146 | 83.3% (5/6) ⚠️intrin | #2 | 0 | 2 | GNR 0.19<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 1 | 1140ms | 🟤 assert |
| fission | clang -O2 | 0.167 | 0.425 | 16.7% (1/6) | #2 | 0 | 1 | GNR 0.67<br>type 0.50<br>expr 0.72<br>cf 1.00<br>art 0 | 1832ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.421 | 0.0% | #2 | 0 | 2 | GNR 0.75<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 9 | 8288ms | ❌ |

### `count_bits` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | clang -O0 | 1.000 | 0.231 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.76<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 5379ms | ✅ |
| fission | clang -O2 | 1.000 | 0.226 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.27<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 1832ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.581 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.53<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 12470ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.237 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.92<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 1269ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.265 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.33<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 1863ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.609 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 7988ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.755 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 5755ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.438 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.89<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 1600ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.410 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 1140ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.609 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 7361ms | ✅ |
| ghidra | clang -O0 | 0.000 | 0.298 | 0.0% (0/6) | #2 | 0 | 2 | GNR 0.69<br>type 0.33<br>expr 0.78<br>cf 1.00<br>art 2 | 5164ms | 🟡 timeout |
| ghidra | gcc -O0 | 0.000 | 0.688 | 0.0% | #2 | 0 | 2 | GNR 0.14<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 2 | 8288ms | ❌ |

### `crc32` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.100 | 100.0% (6/6) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 2361ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.293 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.50<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 0 | 14699ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.400 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 6130ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.305 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.50<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 0 | 21627ms | ✅ |
| fission | clang -O0 | 1.000 | 0.059 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3178ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.474 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 13530ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.057 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.70<br>type 0.50<br>expr 0.50<br>cf 1.00<br>art 0 | 7787ms | ✅ |
| fission | clang -O2 | 0.333 | 0.063 | 33.3% (2/6) | #2 | 1 | 3 | GNR 0.02<br>type 0.50<br>expr 0.57<br>cf 1.00<br>art 0 | 1974ms | 🟤 assert |
| fission | gcc -O2 | 0.167 | 0.060 | 16.7% (1/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2543ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.167 | 0.112 | 16.7% (1/6) | #2 | 2 | 3 | GNR 0.55<br>type 0.50<br>expr 0.66<br>cf 0.50<br>art 0 | 1694ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.167 | 0.041 | 16.7% (1/6) | #2 | 0 | 4 | GNR 0.15<br>type 0.50<br>expr 0.66<br>cf 1.00<br>art 0 | 2998ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.343 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 9830ms | ❌ |

### `dot_product_stride` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.073 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3709ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.105 | 100.0% (5/5) | #1 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1236ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.566 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.12<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 5581ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.239 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.30<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 5116ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.494 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5761ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.474 | 0.0% | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 5531ms | ❌ |
| fission | gcc -O0 | 0.000 | 0.090 | 0.0% (0/5) | #1 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 755ms | 🟠 runtime |
| fission | gcc -O2 | 0.000 | 0.070 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3905ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.068 | 0.0% (0/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 946ms | 🟠 runtime |
| fission | clang -O0 | 0.000 | 0.102 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 922ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 1042ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.049 | 0.0% (0/5) | #1 | 1 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 13 | 8700ms | 🔴 compile |

### `factorial` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.239 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1281ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6429ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.579 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4603ms | ✅ |
| fission | clang -O0 | 1.000 | 0.209 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1250ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.504 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 7064ms | ✅ |
| fission | clang -O2 | 1.000 | 0.256 | 100.0% (5/5) | #1 | 1 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1344ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.290 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4900ms | ✅ |
| fission | gcc -O2 | 0.400 | 0.220 | 40.0% (2/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 424ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.400 | 0.132 | 40.0% (2/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1514ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.335 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 3 | 6946ms | ❌ |
| fission | gcc-m32 -O2 | 0.000 | 0.071 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1257ms | 🟡 timeout |
| ghidra | gcc-m32 -O2 | 0.000 | 0.136 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7062ms | 🔴 compile |

### `fibonacci` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.222 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 1281ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.218 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.59<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 6429ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.598 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.35<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 4603ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.260 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.64<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 7062ms | ✅ |
| fission | clang -O0 | 1.000 | 0.200 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.55<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 1250ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.484 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.40<br>expr 0.77<br>cf 1.00<br>art 1 | 7064ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.254 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.67<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 4900ms | ✅ |
| fission | gcc-m32 -O0 | 0.500 | 0.236 | 50.0% (3/6) | #2 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 1514ms | 🟤 assert |
| fission | gcc -O2 | 0.333 | 0.138 | 33.3% (2/6) | #2 | 1 | 3 | GNR 0.10<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 424ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.333 | 0.190 | 33.3% (2/6) | #2 | 0 | 3 | GNR 0.21<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 1257ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.321 | 0.0% | #2 | 0 | 2 | GNR 0.53<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 4 | 6946ms | ❌ |
| fission | clang -O2 | 0.000 | 0.170 | 0.0% (0/6) | #2 | 1 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1344ms | 🟡 timeout |

### `find_pair_value` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.090 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1525ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8255ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.117 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.43<br>type 0.50<br>expr 0.53<br>cf 1.00<br>art 0 | 574ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.695 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5060ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8415ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.472 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8207ms | ✅ |
| fission | clang -O2 | 1.000 | 0.106 | 100.0% (5/5) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 979ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.442 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6250ms | ✅ |
| fission | clang -O0 | 0.800 | 0.109 | 80.0% (4/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2077ms | 🟤 assert |
| fission | gcc -O2 | 0.400 | 0.200 | 40.0% (2/5) | #2 | 1 | 3 | GNR 0.29<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 1430ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.400 | 0.176 | 40.0% (2/5) | #2 | 1 | 3 | GNR 0.35<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 1413ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.342 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 8579ms | ❌ |

### `find_substring` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.401 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.16<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 14445ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.114 | 100.0% (6/6) | #1 | 3 | 3 | GNR 0.25<br>type 0.50<br>expr 0.59<br>cf 0.75<br>art 0 | 13977ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.204 | 100.0% (6/6) | #1 | 0 | 5 | GNR 0.42<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 29112ms | ✅ |
| fission | clang -O0 | 1.000 | 0.040 | 100.0% (6/6) | #1 | 11 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 3545ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.223 | 100.0% (6/6) | #1 | 0 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 20831ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.162 | 100.0% (6/6) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 19106ms | ✅ |
| fission | gcc -O0 | 0.667 | 0.075 | 66.7% (4/6) | #1 | 6 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 3383ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.500 | 0.051 | 50.0% (3/6) | #2 | 3 | 6 | GNR 0.06<br>type 0.50<br>expr 0.67<br>cf 0.80<br>art 0 | 4718ms | 🟤 assert |
| ghidra | clang -O0 | 0.000 | 0.142 | 0.0% (0/6) | #2 | 0 | 5 | GNR 0.43<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 19017ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.060 | 0.0% (0/6) | #2 | 7 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 3398ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.281 | 0.0% | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 10 | 32646ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.075 | 0.0% (0/6) | #2 | 2 | 6 | GNR 0.06<br>type 0.50<br>expr 0.70<br>cf 0.80<br>art 0 | 3486ms | 🔴 compile |

### `kv_lookup` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.064 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 755ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.146 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3709ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.086 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.43<br>type 0.50<br>expr 0.53<br>cf 1.00<br>art 0 | 1236ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.681 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5581ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.189 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5116ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.455 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5761ms | ✅ |
| fission | clang -O2 | 1.000 | 0.108 | 100.0% (6/6) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1042ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.412 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8700ms | ✅ |
| fission | clang -O0 | 0.833 | 0.106 | 83.3% (5/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 922ms | 🟤 assert |
| fission | gcc -O2 | 0.500 | 0.160 | 50.0% (3/6) | #2 | 1 | 3 | GNR 0.29<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 3905ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.333 | 0.109 | 33.3% (2/6) | #2 | 1 | 3 | GNR 0.35<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 946ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.316 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 5531ms | ❌ |

### `linear_search` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.203 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.63<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 1281ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.230 | 100.0% (6/6) | #1 | 1 | 3 | GNR 0.41<br>type 0.50<br>expr 0.84<br>cf 1.00<br>art 0 | 424ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.660 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6429ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.205 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.61<br>cf 1.00<br>art 0 | 1514ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.617 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 4603ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.224 | 100.0% (6/6) | #1 | 1 | 3 | GNR 0.41<br>type 0.50<br>expr 0.84<br>cf 1.00<br>art 0 | 1257ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.688 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.47<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 7062ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.401 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 7064ms | ✅ |
| fission | clang -O2 | 1.000 | 0.171 | 100.0% (6/6) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1344ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.317 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.47<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 4900ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.371 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 6946ms | ❌ |
| fission | clang -O0 | 0.000 | 0.200 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1250ms | 🟡 timeout |

### `list_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.063 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.67<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 755ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.158 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 3905ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.453 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.91<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 3709ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.091 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.67<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 1236ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.652 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 5581ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.573 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 5116ms | ✅ |
| fission | clang -O0 | 1.000 | 0.072 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.57<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 922ms | ✅ |
| fission | clang -O2 | 1.000 | 0.158 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 1042ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.573 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 1 | 8700ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.595 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 2 | 5531ms | ❌ |
| fission | gcc-m32 -O2 | 0.000 | 0.478 | 0.0% (0/5) | #2 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.87<br>cf 1.00<br>art 0 | 946ms | 🟡 timeout |
| ghidra | clang -O0 | 0.000 | 0.353 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 5761ms | 🔴 compile |

### `manipulate_bitfields` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.312 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 18634ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.312 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 28864ms | ✅ |
| fission | gcc -O2 | 0.800 | 0.097 | 80.0% (4/5) | #2 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4376ms | 🟤 assert |
| fission | clang -O0 | 0.800 | 0.076 | 80.0% (4/5) ⚠️intrin | #1 | 0 | 1 | GNR 0.07<br>type 0.50<br>expr 0.52<br>cf 1.00<br>art 1 | 4979ms | 🟤 assert |
| fission | clang -O2 | 0.800 | 0.085 | 80.0% (4/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3886ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.200 | 0.078 | 20.0% (1/5) ⚠️intrin | #2 | 0 | 2 | GNR 0.14<br>type 0.50<br>expr 0.66<br>cf 1.00<br>art 1 | 3217ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.119 | 0.0% | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 21209ms | ❌ |
| fission | gcc -O0 | 0.000 | 0.084 | 0.0% (0/5) ⚠️intrin | #1 | 0 | 2 | GNR 0.11<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 1 | 2741ms | 🔴 compile |
| fission | gcc-m32 -O0 | 0.000 | 0.050 | 0.0% (0/5) ⚠️intrin | #1 | 0 | 2 | GNR 0.09<br>type 0.50<br>expr 0.51<br>cf 1.00<br>art 1 | 4549ms | 🔴 compile |
| ghidra | gcc-m32 -O0 | 0.000 | 0.208 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 18591ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.205 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 20551ms | 🔴 compile |
| ghidra | clang -O2 | 0.000 | 0.341 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 20172ms | 🔴 compile |

### `matrix_multiply` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.035 | 100.0% (5/5) | #1 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 2741ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.206 | 100.0% (5/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 18634ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.489 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 18591ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.163 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.38<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 28864ms | ✅ |
| fission | clang -O0 | 1.000 | 0.064 | 100.0% (5/5) | #1 | 1 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4979ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.701 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 20551ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.197 | 100.0% (5/5) | #1 | 0 | 6 | GNR 0.46<br>type 0.50<br>expr 0.50<br>cf 1.00<br>art 0 | 20172ms | ✅ |
| fission | gcc -O2 | 0.200 | 0.054 | 20.0% (1/5) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4376ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.387 | 0.0% | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 21209ms | ❌ |
| fission | gcc-m32 -O0 | 0.000 | 0.034 | 0.0% (0/5) | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4549ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.029 | 0.0% (0/5) | #2 | 3 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 3217ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.029 | 0.0% (0/5) | #2 | 9 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 3886ms | 🔴 compile |

### `mixed_width_accumulate` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.205 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.15<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 6682ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.629 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.30<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 6283ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.187 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.33<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 10462ms | ✅ |
| fission | gcc -O0 | 0.500 | 0.092 | 50.0% (3/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1477ms | 🟤 assert |
| fission | gcc -O2 | 0.500 | 0.163 | 50.0% (3/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1493ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.500 | 0.056 | 50.0% (3/6) | #2 | 0 | 4 | GNR 0.60<br>type 0.50<br>expr 0.54<br>cf 1.00<br>art 0 | 917ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.167 | 0.046 | 16.7% (1/6) | #2 | 0 | 4 | GNR 0.24<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 1718ms | 🟤 assert |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 4720ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.044 | 0.0% (0/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 4834ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.181 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 10755ms | ❌ |
| fission | clang -O0 | 0.000 | 0.072 | 0.0% (0/6) ⚠️intrin | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 1315ms | 🟡 timeout |
| ghidra | clang -O0 | 0.000 | 0.328 | 0.0% (0/6) | #1 | 0 | 3 | GNR 0.24<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 9312ms | 🔴 compile |

### `mul_ints` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.237 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 755ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.429 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3905ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.739 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 3709ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.470 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1236ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5581ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.943 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5116ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.470 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 946ms | ✅ |
| fission | clang -O0 | 1.000 | 0.243 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 922ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.761 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5761ms | ✅ |
| fission | clang -O2 | 1.000 | 0.429 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1042ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 8700ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.678 | 0.0% | #2 | 0 | 1 | GNR 0.57<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 4 | 5531ms | ❌ |

### `overlap_move` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | clang -O2 | 1.000 | 0.048 | 100.0% (6/6) | #1 | 3 | 8 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 43 | 4834ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.084 | 100.0% (6/6) | #1 | 4 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1477ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.066 | 100.0% (6/6) | #1 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1493ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.236 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 6682ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.528 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 6283ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.053 | 100.0% (6/6) | #1 | 3 | 3 | GNR 0.64<br>type 0.50<br>expr 0.53<br>cf 0.83<br>art 0 | 917ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.057 | 100.0% (6/6) | #1 | 1 | 4 | GNR 0.34<br>type 0.50<br>expr 0.39<br>cf 0.83<br>art 0 | 1718ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.238 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 10462ms | ✅ |
| fission | clang -O0 | 1.000 | 0.036 | 100.0% (6/6) | #1 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1315ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.398 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 9312ms | ✅ |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 4720ms | ❌ Decompiler returned whole-prog |
| ghidra | gcc -O0 | 0.000 | 0.269 | 0.0% | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 10755ms | ❌ |

### `pointer_stride_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.110 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1525ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.292 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1430ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.609 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.29<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 8255ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.312 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.43<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 574ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.674 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 5060ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.316 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.20<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 1413ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.648 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.29<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 8415ms | ✅ |
| fission | clang -O0 | 1.000 | 0.086 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2077ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.489 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 8207ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.079 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6250ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.259 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 8579ms | ❌ |
| fission | clang -O2 | 0.000 | 0.034 | 0.0% (0/5) | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 979ms | 🔴 compile |

### `power` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.243 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1281ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.203 | 100.0% (6/6) | #1 | 2 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 424ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.392 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6429ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.492 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4603ms | ✅ |
| fission | clang -O0 | 1.000 | 0.231 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1250ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.264 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4900ms | ✅ |
| fission | clang -O2 | 0.500 | 0.212 | 50.0% (3/6) | #2 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1344ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.374 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 6946ms | ❌ |
| fission | gcc-m32 -O0 | 0.000 | 0.073 | 0.0% (0/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1514ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.081 | 0.0% (0/6) | #1 | 1 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1257ms | 🔴 compile |
| ghidra | gcc-m32 -O2 | 0.000 | 0.249 | 0.0% (0/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7062ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.215 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 7064ms | 🔴 compile |

### `process_code` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.103 | 100.0% (5/5) | #1 | 2 | 3 | GNR 0.89<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 1281ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.202 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.83<br>type 0.50<br>expr 0.54<br>cf 1.00<br>art 0 | 424ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.286 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 6429ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.111 | 100.0% (5/5) | #1 | 0 | 6 | GNR 0.89<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 1514ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.166 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.44<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 4603ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.286 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 7062ms | ✅ |
| fission | clang -O0 | 1.000 | 0.139 | 100.0% (5/5) | #1 | 2 | 3 | GNR 0.89<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 1250ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.149 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.41<br>type 0.38<br>expr 0.80<br>cf 1.00<br>art 1 | 7064ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.309 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 4900ms | ✅ |
| fission | gcc-m32 -O2 | 0.800 | 0.102 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.56<br>type 0.50<br>expr 0.66<br>cf 1.00<br>art 0 | 1257ms | 🟤 assert |
| fission | clang -O2 | 0.600 | 0.163 | 60.0% (3/5) | #2 | 0 | 5 | GNR 0.29<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 0 | 1344ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.157 | 0.0% | #2 | 0 | 4 | GNR 0.88<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 8 | 6946ms | ❌ |

### `rc4_crypt` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.044 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2361ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.234 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.44<br>type 0.50<br>expr 0.62<br>cf 1.00<br>art 0 | 14699ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.016 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2543ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.032 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.52<br>type 0.50<br>expr 0.37<br>cf 1.00<br>art 0 | 1694ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.440 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.10<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 6130ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.013 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.29<br>type 0.50<br>expr 0.45<br>cf 1.00<br>art 0 | 2998ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.247 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.57<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 21627ms | ✅ |
| fission | clang -O0 | 1.000 | 0.069 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3178ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.384 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.09<br>type 0.50<br>expr 0.62<br>cf 1.00<br>art 0 | 13530ms | ✅ |
| fission | clang -O2 | 1.000 | 0.027 | 100.0% (5/5) | #1 | 1 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1974ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.162 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.75<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 7787ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.292 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 17 | 9830ms | ❌ |

### `rc4_init` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.544 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.11<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 6130ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.233 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.69<br>type 0.50<br>expr 0.61<br>cf 1.00<br>art 0 | 21627ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.236 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.24<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 13530ms | ✅ |
| fission | gcc -O0 | 0.200 | 0.082 | 20.0% (1/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2361ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.200 | 0.013 | 20.0% (1/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1694ms | 🟤 assert |
| fission | clang -O0 | 0.200 | 0.010 | 20.0% (1/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3178ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.362 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 9830ms | ❌ |
| ghidra | gcc -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 14699ms | ❌ Decompiler returned whole-prog |
| fission | gcc -O2 | 0.000 | 0.023 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2543ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.105 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2998ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.033 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1974ms | 🔴 compile |
| ghidra | clang -O2 | 0.000 | 0.081 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 33 | 7787ms | 🔴 compile |

### `reverse_in_place` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.079 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1525ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.221 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 8255ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.098 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.29<br>type 0.50<br>expr 0.43<br>cf 1.00<br>art 0 | 574ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.339 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.25<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 5060ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.221 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 8415ms | ✅ |
| fission | clang -O0 | 1.000 | 0.105 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2077ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.325 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.26<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 8207ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.146 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6250ms | ✅ |
| fission | gcc-m32 -O2 | 0.400 | 0.130 | 40.0% (2/5) | #2 | 2 | 2 | GNR 0.27<br>type 0.50<br>expr 0.67<br>cf 0.60<br>art 0 | 1413ms | 🟤 assert |
| fission | gcc -O2 | 0.200 | 0.124 | 20.0% (1/5) | #2 | 2 | 2 | GNR 0.28<br>type 0.50<br>expr 0.68<br>cf 0.60<br>art 0 | 1430ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.323 | 0.0% | #2 | 0 | 2 | GNR 0.60<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 11 | 8579ms | ❌ |
| fission | clang -O2 | 0.000 | 0.059 | 0.0% (0/5) | #2 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 979ms | 🔴 compile |

### `reverse_string` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.353 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.16<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 14445ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.097 | 100.0% (5/5) | #1 | 1 | 2 | GNR 0.51<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 13977ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.263 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 29112ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.256 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.14<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 19017ms | ✅ |
| fission | clang -O2 | 1.000 | 0.107 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.24<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 3398ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.252 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.12<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 20831ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.083 | 100.0% (5/5) | #1 | 1 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3383ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.233 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 19106ms | ✅ |
| fission | clang -O0 | 0.600 | 0.116 | 60.0% (3/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3545ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.000 | 0.042 | 0.0% (0/5) | #2 | 0 | 2 | GNR 0.16<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 4718ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.251 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 32646ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.043 | 0.0% (0/5) | #2 | 1 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3486ms | 🔴 compile |

### `rolling_hash32` 🔴 Fission-only gap
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | clang -O2 | 1.000 | 0.340 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.64<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 4834ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.139 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1493ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.303 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 6682ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.783 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 6283ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.147 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1718ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.303 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 10462ms | ✅ |
| fission | clang -O0 | 1.000 | 0.104 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1315ms | ✅ |
| fission | gcc -O0 | 0.333 | 0.190 | 33.3% (2/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1477ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.167 | 0.111 | 16.7% (1/6) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 917ms | 🟤 assert |
| fission | clang -O2 | 0.000 | 0.090 | 0.0% (0/6) | #2 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4720ms | 🟠 runtime |
| ghidra | gcc -O0 | 0.000 | 0.414 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 10755ms | ❌ |
| ghidra | clang -O0 | 0.000 | 0.558 | 0.0% (0/6) | #2 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 9312ms | ❌ |

### `rotate_words`
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | clang -O2 | 1.000 | 0.152 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.72<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 4834ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.217 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.46<br>type 0.50<br>expr 0.66<br>cf 1.00<br>art 0 | 6682ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.071 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.43<br>type 0.50<br>expr 0.40<br>cf 1.00<br>art 0 | 917ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.111 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.14<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 0 | 1718ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.213 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.44<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 10462ms | ✅ |
| fission | clang -O2 | 0.833 | 0.084 | 83.3% (5/6) | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4720ms | 🟤 assert |
| fission | clang -O0 | 0.667 | 0.049 | 66.7% (4/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1315ms | 🟤 assert |
| fission | gcc -O0 | 0.500 | 0.047 | 50.0% (3/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1477ms | 🟤 assert |
| fission | gcc -O2 | 0.500 | 0.089 | 50.0% (3/6) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1493ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.337 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 10755ms | ❌ |
| ghidra | gcc-m32 -O0 | 0.000 | 0.398 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6283ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.344 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9312ms | 🔴 compile |

### `saturating_add` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | clang -O0 | 1.000 | 0.141 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.66<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 5379ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.315 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.42<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 5164ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.137 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.44<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 1269ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.606 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.40<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 7988ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.246 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.47<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 5755ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.317 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.94<br>type 0.50<br>expr 0.53<br>cf 1.00<br>art 0 | 1600ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.606 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.40<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 7361ms | ✅ |
| fission | gcc -O2 | 0.800 | 0.319 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.68<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 1863ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.800 | 0.282 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.55<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 1140ms | 🟤 assert |
| fission | clang -O2 | 0.000 | 0.396 | 0.0% (0/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1832ms | ❌ |
| ghidra | clang -O2 | 0.000 | 0.432 | 0.0% (0/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 12470ms | ❌ |
| ghidra | gcc -O0 | 0.000 | 0.252 | 0.0% | #2 | 0 | 3 | GNR 0.84<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 8 | 8288ms | ❌ |

### `signum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | clang -O0 | 1.000 | 0.340 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 5379ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.523 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.50<br>type 0.38<br>expr 0.87<br>cf 1.00<br>art 1 | 5164ms | ✅ |
| fission | clang -O2 | 1.000 | 0.409 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.75<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 1832ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.624 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 12470ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.335 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 1269ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.492 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 7988ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.611 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.56<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 5755ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.580 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 1600ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.477 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.75<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 1140ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.583 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.84<br>cf 1.00<br>art 0 | 7361ms | ✅ |
| fission | gcc -O2 | 0.600 | 0.388 | 60.0% (3/5) | #2 | 0 | 1 | GNR 0.30<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 1863ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.375 | 0.0% | #2 | 0 | 3 | GNR 0.80<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 3 | 8288ms | ❌ |

### `state_machine_score` 🔴 Fission-only gap
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | clang -O2 | 1.000 | 0.237 | 100.0% (7/7) | #1 | 2 | 5 | GNR 0.74<br>type 0.50<br>expr 0.56<br>cf 0.48<br>art 0 | 4834ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.048 | 100.0% (7/7) | #1 | 18 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1477ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.125 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.72<br>type 0.50<br>expr 0.61<br>cf 0.87<br>art 0 | 6682ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.117 | 100.0% (7/7) | #1 | 2 | 6 | GNR 0.16<br>type 0.50<br>expr 0.66<br>cf 0.52<br>art 0 | 6283ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.054 | 100.0% (7/7) | #1 | 18 | 3 | GNR 0.58<br>type 0.50<br>expr 0.57<br>cf 0.37<br>art 0 | 917ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.125 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.72<br>type 0.50<br>expr 0.61<br>cf 0.87<br>art 0 | 10462ms | ✅ |
| fission | gcc -O2 | 0.143 | 0.070 | 14.3% (1/7) | #2 | 7 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1493ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.143 | 0.046 | 14.3% (1/7) | #2 | 8 | 3 | GNR 0.15<br>type 0.50<br>expr 0.56<br>cf 0.54<br>art 0 | 1718ms | 🟤 assert |
| fission | clang -O2 | 0.000 | 0.070 | 0.0% (0/7) | #2 | 3 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4720ms | 🟠 runtime |
| ghidra | gcc -O0 | 0.000 | 0.107 | 0.0% | #2 | 2 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 5 | 10755ms | ❌ |
| fission | clang -O0 | 0.000 | 0.054 | 0.0% (0/7) | #1 | 2 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1315ms | 🟠 runtime |
| ghidra | clang -O0 | 0.000 | 0.146 | 0.0% (0/7) | #1 | 0 | 4 | GNR 0.11<br>type 0.50<br>expr 0.58<br>cf 0.67<br>art 0 | 9312ms | 🔴 compile |

### `sum_array` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.255 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1525ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.358 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1430ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.171 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 8255ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.309 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.68<br>type 0.50<br>expr 0.59<br>cf 1.00<br>art 0 | 574ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.833 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 5060ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.363 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1413ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.171 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 8415ms | ✅ |
| fission | clang -O0 | 1.000 | 0.150 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2077ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.733 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 8207ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.030 | 100.0% (5/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 6250ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.648 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 8579ms | ❌ |
| fission | clang -O2 | 0.000 | 0.012 | 0.0% (0/5) | #2 | 6 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 979ms | 🔴 compile |

---

## Overfitting Analysis

Functions where **all** decompilers scored below 0.3 are marked as objectively hard.
Functions where **only Fission** scored below 0.3 are marked as quality gaps.

✅ No significant quality gaps detected.