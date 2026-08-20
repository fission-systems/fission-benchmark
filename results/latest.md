<!-- run_id=0ece7383-c9ac-41ca-a5b8-7bc84753a6f9 source_envelope_sha256=2a016dcb5904a6541ab50d2729b3d8abed4f2f4f95e695eae0d5d79e66b6d159 -->
# Fission Benchmark Report

**Measured at:** 2026-08-20T02:10:22.707129Z
**Rendered at:** 2026-08-20 02:23 UTC
**Corpus:** `dev`
**Functions evaluated:** 36

---

## ✅ VALID RUN

> Fission 213/216 (98.6%), all-backend 428/432 (99.1%)

## MVP Summary — Standard set

> **Primary ranking axis:** semantic pass rate (original-binary oracle when available).
> **Also first-class:** coverage (attempted / adapter clean / boundary invalid / tested), fail taxonomy, runtime.
> **Secondary:** CFG match (attached when cfg_parity JSONL present).
> **Diagnostics only (non-ranking):** source similarity, AST similarity, readability proxies.
> Readability proxies are not a final score until the human validation study completes.

| Decompiler | Attempted | Adapter clean | Boundary invalid | Semantic tested | Semantic mean | Perfect | No wrapper | Fail taxonomy (top) | Mean time |
| ---|---|---|---|---|---|---|---|---|--- |
| **fission** | 216 | 213 | 3 | 213 | 64.1% | 105 | 0 | assertion_fail:69 · compile_error:24 · runtime_error:11 | 1379ms |
| **ghidra** | 216 | 215 | 1 | 215 | 72.7% | 157 | 0 | oracle_error:36 · compile_error:20 · whole_program_output:1 | 11692ms |

### Extension — Cross-compiler / opt

| Decompiler | Variant | Compiler | Opt | Tested | Semantic mean |
| ---|---|---|---|---|--- |
| fission | clang -O0 | clang | -O0 | 36 | 73.2% |
| fission | clang -O2 | clang | -O2 | 33 | 37.1% |
| fission | gcc -O0 | gcc | -O0 | 36 | 79.5% |
| fission | gcc -O2 | gcc | -O2 | 36 | 62.6% |
| fission | gcc-m32 -O0 | gcc-m32 | -O0 | 36 | 73.0% |
| fission | gcc-m32 -O2 | gcc-m32 | -O2 | 36 | 59.1% |
| ghidra | clang -O0 | clang | -O0 | 36 | 75.0% |
| ghidra | clang -O2 | clang | -O2 | 36 | 80.6% |
| ghidra | gcc -O0 | gcc | -O0 | 36 | 0.0% |
| ghidra | gcc -O2 | gcc | -O2 | 35 | 91.7% |
| ghidra | gcc-m32 -O0 | gcc-m32 | -O0 | 36 | 94.4% |
| ghidra | gcc-m32 -O2 | gcc-m32 | -O2 | 36 | 94.4% |

### Secondary — CFG match

| Decompiler | Match | Mismatch | Match rate |
| ---|---|---|--- |
| fission | 20 | 0 | 100.0% |

### Diagnostics note

> Source similarity is **not** listed in the MVP table. It remains on per-function rows for triage only.

---

## Per-Function Results

### `accumulate_pairs` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.075 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1333ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.120 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10878ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.072 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 511ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.787 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9592ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.184 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1442ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.120 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5264ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.108 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1627ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.757 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11100ms | ✅ |
| fission | clang -O0 | 0.400 | 0.124 | 40.0% (2/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 799ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.517 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 10314ms | ❌ |
| ghidra | clang -O2 | 0.000 | 0.047 | 0.0% (0/5) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 16 | 11129ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 2424ms | ❌ Decompiler returned whole-prog |

### `add_ints` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.943 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 4681ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.750 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 871ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.943 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5786ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.750 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 696ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.761 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 7231ms | ✅ |
| fission | clang -O0 | 1.000 | 0.433 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 841ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 11517ms | ✅ |
| fission | clang -O2 | 1.000 | 0.497 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 1856ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.424 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 1435ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.739 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 7409ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.497 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 513ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.678 | 0.0% | #2 | 0 | 1 | GNR 0.57<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 4 | 5922ms | ❌ |

### `apply_binop` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.658 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4681ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.431 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.88<br>type 0.60<br>expr 0.74<br>cf 1.00<br>art 0 | 871ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.615 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5786ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.440 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 696ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.535 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7231ms | ✅ |
| fission | clang -O0 | 1.000 | 0.129 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 841ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.615 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11517ms | ✅ |
| fission | clang -O2 | 1.000 | 0.447 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 1856ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.099 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1435ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.151 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 513ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.395 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 7 | 5922ms | ❌ |
| ghidra | gcc -O2 | 0.000 | 0.198 | 0.0% (0/6) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 7409ms | 🔴 compile |

### `bounded_checksum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.548 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 4681ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.115 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.67<br>type 0.50<br>expr 0.49<br>cf 1.00<br>art 0 | 871ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.286 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.22<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 5786ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.153 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.64<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 11517ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.062 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1435ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.098 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.62<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 7409ms | ✅ |
| fission | gcc -O2 | 0.500 | 0.085 | 50.0% (3/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 513ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.167 | 0.110 | 16.7% (1/6) | #2 | 0 | 2 | GNR 0.46<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 696ms | 🟤 assert |
| ghidra | clang -O0 | 0.000 | 0.319 | 0.0% (0/6) | #1 | 0 | 2 | GNR 0.30<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 7231ms | 🔴 compile |
| fission | clang -O0 | 0.000 | 0.107 | 0.0% (0/6) ⚠️intrin | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 841ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.052 | 0.0% (0/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1856ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.421 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 5922ms | ❌ |

### `bounded_tlv_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.112 | 100.0% (7/7) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 919ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.151 | 100.0% (7/7) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 13771ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.363 | 100.0% (7/7) | #1 | 0 | 3 | GNR 0.22<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 8992ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.121 | 100.0% (7/7) | #1 | 0 | 4 | GNR 0.58<br>type 0.50<br>expr 0.50<br>cf 1.00<br>art 0 | 1329ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.149 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.61<br>type 0.50<br>expr 0.56<br>cf 1.00<br>art 0 | 9080ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.363 | 100.0% (7/7) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9178ms | ✅ |
| fission | clang -O0 | 1.000 | 0.060 | 100.0% (7/7) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 582ms | ✅ |
| fission | gcc -O2 | 0.429 | 0.071 | 42.9% (3/7) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1204ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.286 | 0.017 | 28.6% (2/7) | #2 | 0 | 5 | GNR 0.27<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 916ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.334 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 7 | 6698ms | ❌ |
| ghidra | clang -O2 | 0.000 | 0.040 | 0.0% (0/7) | #1 | 2 | 7 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 16 | 9491ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.026 | 0.0% (0/7) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 1 | 2096ms | 🔴 compile |

### `bubble_sort` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.152 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.12<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 8086ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.082 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.40<br>type 0.50<br>expr 0.41<br>cf 1.00<br>art 0 | 764ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.190 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.12<br>type 0.50<br>expr 0.72<br>cf 1.00<br>art 0 | 8615ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.361 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.57<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 8945ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.100 | 100.0% (5/5) | #1 | 0 | 7 | GNR 0.74<br>type 0.50<br>expr 0.52<br>cf 1.00<br>art 0 | 13696ms | ✅ |
| fission | gcc -O0 | 0.800 | 0.076 | 80.0% (4/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1245ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.167 | 0.0% | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 15 | 4710ms | ❌ |
| ghidra | gcc -O2 | 0.000 | 0.131 | 0.0% (0/5) | #1 | 0 | 5 | GNR 0.26<br>type 0.42<br>expr 0.51<br>cf 1.00<br>art 2 | 7942ms | 🔴 compile |
| fission | gcc -O2 | 0.000 | 0.112 | 0.0% (0/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1080ms | 🟠 runtime |
| fission | gcc-m32 -O2 | 0.000 | 0.047 | 0.0% (0/5) | #2 | 0 | 5 | GNR 0.25<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 1193ms | 🟠 runtime |
| fission | clang -O0 | 0.000 | 0.074 | 0.0% (0/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 333ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.064 | 0.0% (0/5) | #2 | 0 | 7 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1147ms | 🟠 runtime |

### `checksum` 🔴 Fission-only gap
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | clang -O2 | 1.000 | 0.144 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.71<br>type 0.50<br>expr 0.49<br>cf 1.00<br>art 0 | 6716ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.106 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 632ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.129 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 11204ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.112 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 568ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.819 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 15357ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.140 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.78<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 1419ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.116 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 10116ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.082 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.33<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 1864ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.732 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 11384ms | ✅ |
| fission | clang -O0 | 1.000 | 0.123 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 816ms | ✅ |
| fission | clang -O2 | 0.000 | 0.039 | 0.0% (0/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1462ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.668 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 10572ms | ❌ |

### `clamp`
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | clang -O2 | 1.000 | 0.731 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 6716ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.122 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 632ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.582 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 11204ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.104 | 100.0% (6/6) ⚠️intrin | #1 | 0 | 1 | GNR 0.71<br>type 0.50<br>expr 0.57<br>cf 1.00<br>art 1 | 568ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.590 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 15357ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.516 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 1419ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.731 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 10116ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.421 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.26<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 0 | 11384ms | ✅ |
| fission | clang -O0 | 1.000 | 0.118 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 816ms | ✅ |
| fission | clang -O2 | 0.833 | 0.417 | 83.3% (5/6) | #2 | 0 | 1 | GNR 0.88<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 1462ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.833 | 0.096 | 83.3% (5/6) ⚠️intrin | #2 | 0 | 2 | GNR 0.33<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 1 | 1864ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.421 | 0.0% | #2 | 0 | 2 | GNR 0.75<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 9 | 10572ms | ❌ |

### `count_bits`
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | clang -O2 | 1.000 | 0.581 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.53<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 6716ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.396 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.92<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 632ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.609 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 11204ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.180 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 568ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.755 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 15357ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.592 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.89<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 1419ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.609 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 10116ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.443 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 1864ms | ✅ |
| fission | clang -O0 | 1.000 | 0.226 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.74<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 816ms | ✅ |
| fission | clang -O2 | 0.833 | 0.150 | 83.3% (5/6) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1462ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.688 | 0.0% | #2 | 0 | 2 | GNR 0.14<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 2 | 10572ms | ❌ |
| ghidra | clang -O0 | 0.000 | 0.298 | 0.0% (0/6) | #2 | 0 | 2 | GNR 0.69<br>type 0.33<br>expr 0.78<br>cf 1.00<br>art 2 | 11384ms | 🟡 timeout |

### `crc32` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.071 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1566ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.293 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.50<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 0 | 8398ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.400 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 16695ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.305 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.50<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 0 | 11570ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.474 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 18263ms | ✅ |
| fission | clang -O0 | 1.000 | 0.049 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 534ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.057 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.70<br>type 0.50<br>expr 0.50<br>cf 1.00<br>art 0 | 26070ms | ✅ |
| fission | clang -O2 | 1.000 | 0.046 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3052ms | ✅ |
| fission | gcc-m32 -O2 | 0.500 | 0.048 | 50.0% (3/6) | #2 | 0 | 5 | GNR 0.18<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 1582ms | 🟤 assert |
| fission | gcc -O2 | 0.167 | 0.075 | 16.7% (1/6) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1137ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.167 | 0.085 | 16.7% (1/6) | #2 | 0 | 4 | GNR 0.59<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 2702ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.343 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 16043ms | ❌ |

### `dot_product_stride`
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.566 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.12<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 4681ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.239 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.30<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 5786ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.494 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7231ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.073 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7409ms | ✅ |
| fission | gcc -O2 | 0.400 | 0.063 | 40.0% (2/5) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 513ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.200 | 0.069 | 20.0% (1/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 871ms | 🟤 assert |
| fission | gcc -O0 | 0.200 | 0.073 | 20.0% (1/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1435ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.000 | 0.085 | 0.0% (0/5) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 696ms | 🟠 runtime |
| fission | clang -O0 | 0.000 | 0.118 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 841ms | 🟠 runtime |
| ghidra | clang -O2 | 0.000 | 0.049 | 0.0% (0/5) | #1 | 1 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 13 | 11517ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 1856ms | ❌ Decompiler returned whole-prog |
| ghidra | gcc -O0 | 0.000 | 0.474 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 5922ms | ❌ |

### `factorial` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.184 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1245ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7942ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.579 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8086ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.504 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 8945ms | ✅ |
| fission | clang -O0 | 1.000 | 0.252 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 333ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.290 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 13696ms | ✅ |
| fission | clang -O2 | 1.000 | 0.240 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1147ms | ✅ |
| fission | gcc-m32 -O0 | 0.600 | 0.148 | 60.0% (3/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 764ms | 🟤 assert |
| fission | gcc -O2 | 0.400 | 0.268 | 40.0% (2/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1080ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.400 | 0.022 | 40.0% (2/5) ⚠️intrin | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 3 | 1193ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.335 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 3 | 4710ms | ❌ |
| ghidra | gcc-m32 -O2 | 0.000 | 0.136 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8615ms | 🔴 compile |

### `fibonacci` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.079 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 1245ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.218 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.59<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 7942ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.598 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.35<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 8086ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.260 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.64<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 8615ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.484 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.40<br>expr 0.77<br>cf 1.00<br>art 1 | 8945ms | ✅ |
| fission | clang -O0 | 1.000 | 0.301 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.55<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 333ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.254 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.67<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 13696ms | ✅ |
| fission | gcc -O2 | 0.500 | 0.220 | 50.0% (3/6) | #2 | 0 | 2 | GNR 0.16<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 0 | 1080ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.500 | 0.260 | 50.0% (3/6) | #2 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 764ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.500 | 0.281 | 50.0% (3/6) | #2 | 0 | 2 | GNR 0.22<br>type 0.50<br>expr 0.84<br>cf 1.00<br>art 0 | 1193ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.321 | 0.0% | #2 | 0 | 2 | GNR 0.53<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 4 | 4710ms | ❌ |
| fission | clang -O2 | 0.000 | 0.275 | 0.0% (0/6) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1147ms | 🟡 timeout |

### `find_pair_value` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.080 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1333ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10878ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.695 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9592ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5264ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.472 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11100ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.442 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11129ms | ✅ |
| fission | gcc -O2 | 0.400 | 0.204 | 40.0% (2/5) | #2 | 0 | 4 | GNR 0.12<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 511ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.400 | 0.141 | 40.0% (2/5) | #2 | 0 | 3 | GNR 0.46<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 1442ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.400 | 0.188 | 40.0% (2/5) | #2 | 0 | 4 | GNR 0.20<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 1627ms | 🟤 assert |
| fission | clang -O0 | 0.400 | 0.058 | 40.0% (2/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 799ms | 🟤 assert |
| fission | clang -O2 | 0.400 | 0.099 | 40.0% (2/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2424ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.342 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 10314ms | ❌ |

### `find_substring`
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O2 | 1.000 | 0.204 | 100.0% (6/6) | #1 | 0 | 5 | GNR 0.42<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 14134ms | ✅ |
| fission | clang -O0 | 1.000 | 0.051 | 100.0% (6/6) | #1 | 0 | 7 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2987ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.223 | 100.0% (6/6) | #1 | 0 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 24654ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.401 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.16<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 37550ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.051 | 100.0% (6/6) | #1 | 0 | 7 | GNR 0.25<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 3707ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.162 | 100.0% (6/6) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 21252ms | ✅ |
| fission | gcc -O0 | 0.667 | 0.063 | 66.7% (4/6) | #1 | 0 | 7 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2902ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.500 | 0.069 | 50.0% (3/6) | #2 | 2 | 6 | GNR 0.00<br>type 0.50<br>expr 0.71<br>cf 0.80<br>art 0 | 3894ms | 🟤 assert |
| ghidra | clang -O0 | 0.000 | 0.142 | 0.0% (0/6) | #2 | 0 | 5 | GNR 0.43<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 31896ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.069 | 0.0% (0/6) | #2 | 1 | 7 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1714ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.281 | 0.0% | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 10 | 29430ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.070 | 0.0% (0/6) | #2 | 2 | 6 | GNR 0.14<br>type 0.50<br>expr 0.69<br>cf 0.80<br>art 0 | 1728ms | 🔴 compile |

### `kv_lookup`
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.681 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4681ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.189 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5786ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.455 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7231ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.412 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11517ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.059 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1435ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.146 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7409ms | ✅ |
| fission | clang -O0 | 0.500 | 0.048 | 50.0% (3/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 841ms | 🟤 assert |
| fission | clang -O2 | 0.500 | 0.060 | 50.0% (3/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1856ms | 🟤 assert |
| fission | gcc -O2 | 0.500 | 0.182 | 50.0% (3/6) | #2 | 0 | 4 | GNR 0.12<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 513ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.333 | 0.093 | 33.3% (2/6) | #2 | 0 | 3 | GNR 0.46<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 871ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.333 | 0.204 | 33.3% (2/6) | #2 | 0 | 4 | GNR 0.20<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 696ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.316 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 5922ms | ❌ |

### `linear_search` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.660 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7942ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.617 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 8086ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.194 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.46<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 764ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.688 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.47<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 8615ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.261 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.37<br>type 0.50<br>expr 0.84<br>cf 1.00<br>art 0 | 1193ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.401 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 8945ms | ✅ |
| fission | clang -O0 | 1.000 | 0.155 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 333ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.317 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.47<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 13696ms | ✅ |
| fission | clang -O2 | 1.000 | 0.195 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1147ms | ✅ |
| fission | gcc -O0 | 0.667 | 0.187 | 66.7% (4/6) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 1245ms | 🟤 assert |
| fission | gcc -O2 | 0.667 | 0.249 | 66.7% (4/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1080ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.371 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 4710ms | ❌ |

### `list_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.652 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4681ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.217 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.75<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 871ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.573 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 5786ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.573 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 1 | 11517ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.453 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.91<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 7409ms | ✅ |
| fission | gcc-m32 -O2 | 0.000 | 0.480 | 0.0% (0/5) | #2 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.87<br>cf 1.00<br>art 0 | 696ms | 🟡 timeout |
| ghidra | clang -O0 | 0.000 | 0.353 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 7231ms | 🔴 compile |
| fission | clang -O0 | 0.000 | 0.120 | 0.0% (0/5) | #1 | 0 | 2 | GNR 0.52<br>type 0.60<br>expr 0.73<br>cf 1.00<br>art 0 | 841ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.162 | 0.0% (0/5) | #2 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 1856ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.595 | 0.0% | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 2 | 5922ms | ❌ |
| fission | gcc -O0 | 0.000 | 0.192 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1435ms | 🔴 compile |
| fission | gcc -O2 | 0.000 | 0.162 | 0.0% (0/5) | #2 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 513ms | 🔴 compile |

### `manipulate_bitfields` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.312 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 27424ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.312 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 25386ms | ✅ |
| fission | gcc -O2 | 0.800 | 0.089 | 80.0% (4/5) | #2 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2703ms | 🟤 assert |
| fission | clang -O0 | 0.800 | 0.081 | 80.0% (4/5) ⚠️intrin | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 2295ms | 🟤 assert |
| fission | clang -O2 | 0.800 | 0.103 | 80.0% (4/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2051ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.200 | 0.078 | 20.0% (1/5) ⚠️intrin | #2 | 0 | 2 | GNR 0.20<br>type 0.50<br>expr 0.66<br>cf 1.00<br>art 1 | 4159ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.119 | 0.0% | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 39759ms | ❌ |
| fission | gcc -O0 | 0.000 | 0.080 | 0.0% (0/5) ⚠️intrin | #1 | 0 | 2 | GNR 0.13<br>type 0.50<br>expr 0.46<br>cf 1.00<br>art 1 | 4278ms | 🔴 compile |
| ghidra | gcc-m32 -O0 | 0.000 | 0.208 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 24499ms | 🔴 compile |
| fission | gcc-m32 -O0 | 0.000 | 0.048 | 0.0% (0/5) ⚠️intrin | #1 | 0 | 2 | GNR 0.12<br>type 0.50<br>expr 0.51<br>cf 1.00<br>art 1 | 3291ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.205 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 27357ms | 🔴 compile |
| ghidra | clang -O2 | 0.000 | 0.341 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 28299ms | 🔴 compile |

### `matrix_multiply` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.206 | 100.0% (5/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 27424ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.489 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 24499ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.163 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.38<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 25386ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.701 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 27357ms | ✅ |
| fission | clang -O0 | 1.000 | 0.033 | 100.0% (5/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2295ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.197 | 100.0% (5/5) | #1 | 0 | 6 | GNR 0.46<br>type 0.50<br>expr 0.50<br>cf 1.00<br>art 0 | 28299ms | ✅ |
| fission | gcc -O0 | 0.200 | 0.043 | 20.0% (1/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4278ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.387 | 0.0% | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 39759ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.076 | 0.0% (0/5) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2703ms | 🟠 runtime |
| fission | gcc-m32 -O0 | 0.000 | 0.046 | 0.0% (0/5) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3291ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.039 | 0.0% (0/5) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4159ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.040 | 0.0% (0/5) | #2 | 0 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2051ms | 🔴 compile |

### `mixed_width_accumulate` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.205 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.15<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 13771ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.629 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.30<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 8992ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.187 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.33<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 9080ms | ✅ |
| fission | gcc -O0 | 0.500 | 0.097 | 50.0% (3/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 919ms | 🟤 assert |
| fission | gcc -O2 | 0.500 | 0.162 | 50.0% (3/6) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1204ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.500 | 0.061 | 50.0% (3/6) | #2 | 0 | 3 | GNR 0.64<br>type 0.50<br>expr 0.54<br>cf 1.00<br>art 0 | 1329ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.167 | 0.035 | 16.7% (1/6) | #2 | 0 | 5 | GNR 0.36<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 916ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.181 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 6698ms | ❌ |
| ghidra | clang -O0 | 0.000 | 0.328 | 0.0% (0/6) | #1 | 0 | 3 | GNR 0.24<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 9178ms | 🔴 compile |
| fission | clang -O0 | 0.000 | 0.074 | 0.0% (0/6) ⚠️intrin | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 582ms | 🟡 timeout |
| ghidra | clang -O2 | 0.000 | 0.044 | 0.0% (0/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 9491ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.017 | 0.0% (0/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2096ms | 🔴 compile |

### `mul_ints` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 4681ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.627 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 871ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.943 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5786ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.627 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 696ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.761 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 7231ms | ✅ |
| fission | clang -O0 | 1.000 | 0.370 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 841ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 11517ms | ✅ |
| fission | clang -O2 | 1.000 | 0.556 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1856ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.364 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1435ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.739 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 7409ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.556 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 513ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.678 | 0.0% | #2 | 0 | 1 | GNR 0.57<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 4 | 5922ms | ❌ |

### `overlap_move` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.049 | 100.0% (6/6) | #1 | 0 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 919ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.236 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 13771ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.079 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1204ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.528 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 8992ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.012 | 100.0% (6/6) | #1 | 0 | 6 | GNR 0.52<br>type 0.50<br>expr 0.54<br>cf 1.00<br>art 0 | 1329ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.238 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 9080ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.057 | 100.0% (6/6) | #1 | 0 | 5 | GNR 0.45<br>type 0.48<br>expr 0.38<br>cf 1.00<br>art 1 | 916ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.398 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 9178ms | ✅ |
| fission | clang -O0 | 1.000 | 0.041 | 100.0% (6/6) | #1 | 0 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 582ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.048 | 100.0% (6/6) | #1 | 3 | 8 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 43 | 9491ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.269 | 0.0% | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 6698ms | ❌ |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 2096ms | ❌ Decompiler returned whole-prog |

### `pointer_stride_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.609 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.29<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 10878ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.280 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 511ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.674 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 9592ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.648 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.29<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 5264ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.289 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.84<br>cf 1.00<br>art 0 | 1627ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.489 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 11100ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.079 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11129ms | ✅ |
| fission | gcc -O0 | 0.200 | 0.321 | 20.0% (1/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1333ms | 🟤 assert |
| fission | clang -O0 | 0.200 | 0.096 | 20.0% (1/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 799ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.259 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 10314ms | ❌ |
| fission | gcc-m32 -O0 | 0.000 | 0.380 | 0.0% (0/5) | #2 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 1442ms | 🟤 assert |
| fission | clang -O2 | 0.000 | 0.028 | 0.0% (0/5) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2424ms | 🔴 compile |

### `power` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.350 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1245ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.392 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7942ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.249 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1080ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.492 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8086ms | ✅ |
| fission | clang -O0 | 1.000 | 0.318 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 333ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.264 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 13696ms | ✅ |
| fission | clang -O2 | 0.500 | 0.161 | 50.0% (3/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1147ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.374 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 4710ms | ❌ |
| fission | gcc-m32 -O0 | 0.000 | 0.096 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 764ms | 🔴 compile |
| ghidra | gcc-m32 -O2 | 0.000 | 0.249 | 0.0% (0/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8615ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.107 | 0.0% (0/6) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1193ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.215 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 8945ms | 🔴 compile |

### `process_code` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.286 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 7942ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.156 | 100.0% (5/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1080ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.166 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.44<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 8086ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.111 | 100.0% (5/5) | #1 | 0 | 6 | GNR 0.89<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 764ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.286 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 8615ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.149 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.41<br>type 0.38<br>expr 0.80<br>cf 1.00<br>art 1 | 8945ms | ✅ |
| fission | clang -O0 | 1.000 | 0.040 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.16<br>type 0.50<br>expr 0.61<br>cf 1.00<br>art 0 | 333ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.309 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 13696ms | ✅ |
| fission | gcc -O0 | 0.800 | 0.160 | 80.0% (4/5) | #1 | 0 | 6 | GNR 0.89<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 1245ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.800 | 0.110 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.56<br>type 0.50<br>expr 0.61<br>cf 1.00<br>art 0 | 1193ms | 🟤 assert |
| fission | clang -O2 | 0.400 | 0.095 | 40.0% (2/5) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1147ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.157 | 0.0% | #2 | 0 | 4 | GNR 0.88<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 8 | 4710ms | ❌ |

### `rc4_crypt` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.021 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1566ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.234 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.44<br>type 0.50<br>expr 0.62<br>cf 1.00<br>art 0 | 8398ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.015 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1137ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.440 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.10<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 16695ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.029 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.27<br>type 0.50<br>expr 0.48<br>cf 1.00<br>art 0 | 2702ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.247 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.57<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 11570ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.013 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.36<br>type 0.50<br>expr 0.48<br>cf 1.00<br>art 0 | 1582ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.384 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.09<br>type 0.50<br>expr 0.62<br>cf 1.00<br>art 0 | 18263ms | ✅ |
| fission | clang -O0 | 1.000 | 0.076 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 534ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.162 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.75<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 26070ms | ✅ |
| fission | clang -O2 | 1.000 | 0.032 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3052ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.292 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 17 | 16043ms | ❌ |

### `rc4_init` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.042 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1566ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.544 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.11<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 16695ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.233 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.69<br>type 0.50<br>expr 0.61<br>cf 1.00<br>art 0 | 11570ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.236 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.24<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 18263ms | ✅ |
| fission | clang -O0 | 1.000 | 0.118 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 534ms | ✅ |
| fission | gcc-m32 -O0 | 0.600 | 0.023 | 60.0% (3/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2702ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.362 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 16043ms | ❌ |
| ghidra | gcc -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 8398ms | ❌ Decompiler returned whole-prog |
| fission | gcc -O2 | 0.000 | 0.023 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1137ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.080 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1582ms | 🟤 assert |
| ghidra | clang -O2 | 0.000 | 0.081 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 33 | 26070ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.042 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3052ms | 🔴 compile |

### `reverse_in_place` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.093 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 1333ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.221 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 10878ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.339 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.25<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 9592ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.221 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 5264ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.325 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.26<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 11100ms | ✅ |
| fission | clang -O0 | 1.000 | 0.089 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 799ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.146 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11129ms | ✅ |
| fission | gcc-m32 -O0 | 0.800 | 0.108 | 80.0% (4/5) | #2 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.40<br>cf 1.00<br>art 0 | 1442ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.400 | 0.126 | 40.0% (2/5) | #2 | 0 | 3 | GNR 0.18<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 1627ms | 🟤 assert |
| fission | gcc -O2 | 0.200 | 0.122 | 20.0% (1/5) | #2 | 0 | 3 | GNR 0.18<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 511ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.323 | 0.0% | #2 | 0 | 2 | GNR 0.60<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 11 | 10314ms | ❌ |
| fission | clang -O2 | 0.000 | 0.030 | 0.0% (0/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 2424ms | 🔴 compile |

### `reverse_string` 🔴 Fission-only gap
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O2 | 1.000 | 0.263 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 14134ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.256 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.14<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 31896ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.252 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.12<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 24654ms | ✅ |
| fission | gcc -O0 | 1.000 | 0.151 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2902ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.353 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.16<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 37550ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.066 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.63<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 3707ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.233 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 21252ms | ✅ |
| fission | clang -O0 | 0.600 | 0.116 | 60.0% (3/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2987ms | 🟤 assert |
| fission | clang -O2 | 0.600 | 0.122 | 60.0% (3/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1714ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.000 | 0.042 | 0.0% (0/5) | #2 | 0 | 2 | GNR 0.16<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 3894ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.251 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 29430ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.041 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1728ms | 🔴 compile |

### `rolling_hash32` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.303 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 13771ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.108 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1204ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.783 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 8992ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.303 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 9080ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.212 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.32<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 916ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.558 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 9178ms | ✅ |
| fission | clang -O0 | 1.000 | 0.150 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 582ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.340 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.64<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 9491ms | ✅ |
| fission | gcc -O0 | 0.333 | 0.078 | 33.3% (2/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 919ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.167 | 0.134 | 16.7% (1/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1329ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.414 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 6698ms | ❌ |
| fission | clang -O2 | 0.000 | 0.102 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2096ms | 🟠 runtime |

### `rotate_words` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.217 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.46<br>type 0.50<br>expr 0.66<br>cf 1.00<br>art 0 | 13771ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.077 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.52<br>type 0.50<br>expr 0.40<br>cf 1.00<br>art 0 | 1329ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.213 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.44<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 9080ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.121 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.14<br>type 0.50<br>expr 0.72<br>cf 1.00<br>art 0 | 916ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.152 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.72<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 9491ms | ✅ |
| fission | gcc -O0 | 0.667 | 0.053 | 66.7% (4/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 919ms | 🟤 assert |
| fission | gcc -O2 | 0.667 | 0.093 | 66.7% (4/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1204ms | 🟤 assert |
| fission | clang -O0 | 0.667 | 0.059 | 66.7% (4/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 582ms | 🟤 assert |
| fission | clang -O2 | 0.500 | 0.085 | 50.0% (3/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2096ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.337 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 6698ms | ❌ |
| ghidra | gcc-m32 -O0 | 0.000 | 0.398 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8992ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.344 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9178ms | 🔴 compile |

### `saturating_add` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.192 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.72<br>type 0.50<br>expr 0.55<br>cf 1.00<br>art 0 | 632ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.606 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.40<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 11204ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.246 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.47<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 15357ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.355 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.94<br>type 0.50<br>expr 0.53<br>cf 1.00<br>art 0 | 1419ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.606 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.40<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 10116ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.315 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.42<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 11384ms | ✅ |
| fission | gcc -O2 | 0.800 | 0.319 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.68<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 568ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.800 | 0.282 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.58<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 1864ms | 🟤 assert |
| fission | clang -O0 | 0.800 | 0.168 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.72<br>type 0.50<br>expr 0.55<br>cf 1.00<br>art 0 | 816ms | 🟤 assert |
| ghidra | clang -O2 | 0.000 | 0.432 | 0.0% (0/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 6716ms | ❌ |
| fission | clang -O2 | 0.000 | 0.438 | 0.0% (0/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 1462ms | ❌ |
| ghidra | gcc -O0 | 0.000 | 0.252 | 0.0% | #2 | 0 | 3 | GNR 0.84<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 8 | 10572ms | ❌ |

### `signum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | clang -O2 | 1.000 | 0.624 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 6716ms | ✅ |
| fission | clang -O2 | 1.000 | 0.372 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.75<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 1462ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.492 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 11204ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.611 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.56<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 15357ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.583 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 1419ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.583 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.84<br>cf 1.00<br>art 0 | 10116ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.459 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.75<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 1864ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.523 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.50<br>type 0.38<br>expr 0.87<br>cf 1.00<br>art 1 | 11384ms | ✅ |
| fission | clang -O0 | 1.000 | 0.340 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 816ms | ✅ |
| fission | gcc -O0 | 0.600 | 0.156 | 60.0% (3/5) | #1 | 0 | 4 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 632ms | 🟤 assert |
| fission | gcc -O2 | 0.600 | 0.408 | 60.0% (3/5) | #2 | 0 | 1 | GNR 0.30<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 568ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.375 | 0.0% | #2 | 0 | 3 | GNR 0.80<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 3 | 10572ms | ❌ |

### `state_machine_score` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.042 | 100.0% (7/7) | #1 | 2 | 7 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 919ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.125 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.72<br>type 0.50<br>expr 0.61<br>cf 0.87<br>art 0 | 13771ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.068 | 100.0% (7/7) | #1 | 4 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1204ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.117 | 100.0% (7/7) | #1 | 2 | 6 | GNR 0.16<br>type 0.50<br>expr 0.66<br>cf 0.52<br>art 0 | 8992ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.044 | 100.0% (7/7) | #1 | 2 | 7 | GNR 0.62<br>type 0.50<br>expr 0.55<br>cf 0.76<br>art 0 | 1329ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.125 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.72<br>type 0.50<br>expr 0.61<br>cf 0.87<br>art 0 | 9080ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.100 | 100.0% (7/7) | #1 | 4 | 4 | GNR 0.12<br>type 0.50<br>expr 0.59<br>cf 0.67<br>art 0 | 916ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.237 | 100.0% (7/7) | #1 | 2 | 5 | GNR 0.74<br>type 0.50<br>expr 0.56<br>cf 0.48<br>art 0 | 9491ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.107 | 0.0% | #2 | 2 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 5 | 6698ms | ❌ |
| ghidra | clang -O0 | 0.000 | 0.146 | 0.0% (0/7) | #1 | 0 | 4 | GNR 0.11<br>type 0.50<br>expr 0.58<br>cf 0.67<br>art 0 | 9178ms | 🔴 compile |
| fission | clang -O0 | 0.000 | 0.065 | 0.0% (0/7) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 582ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.095 | 0.0% (0/7) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 2096ms | 🟠 runtime |

### `sum_array` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.159 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1333ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.171 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 10878ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.184 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 511ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.833 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 9592ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.211 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.93<br>type 0.50<br>expr 0.55<br>cf 1.00<br>art 0 | 1442ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.171 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 5264ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.242 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1627ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.733 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 11100ms | ✅ |
| fission | clang -O0 | 1.000 | 0.147 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 799ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.030 | 100.0% (5/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11129ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.648 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 10314ms | ❌ |
| fission | clang -O2 | 0.000 | 0.022 | 0.0% (0/5) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2424ms | 🔴 compile |

---

## Overfitting Analysis

Functions where **all** decompilers scored below 0.3 are marked as objectively hard.
Functions where **only Fission** scored below 0.3 are marked as quality gaps.

✅ No significant quality gaps detected.