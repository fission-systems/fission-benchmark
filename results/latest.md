<!-- run_id=2328cd60-ee30-4352-928b-ba87b3826cf3 source_envelope_sha256=f1d0368255e3e6aeaa509cdf5de0f083483f4e8126243750405a903a6576dde8 -->
# Fission Benchmark Report

**Measured at:** 2026-08-03T17:30:48.516675Z
**Rendered at:** 2026-08-03 17:41 UTC
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
| **fission** | 216 | 210 | 5 | 210 | 62.6% | 111 | 0 | assertion_fail:45 · compile_error:27 · timeout:16 | 2972ms |
| **ghidra** | 216 | 215 | 1 | 215 | 72.6% | 156 | 0 | oracle_error:37 · compile_error:20 · whole_program_output:1 | 11443ms |

### Extension — Cross-compiler / opt

| Decompiler | Variant | Compiler | Opt | Tested | Semantic mean |
| ---|---|---|---|---|--- |
| fission | clang -O0 | clang | -O0 | 35 | 75.6% |
| fission | clang -O2 | clang | -O2 | 31 | 46.1% |
| fission | gcc -O0 | gcc | -O0 | 36 | 80.1% |
| fission | gcc -O2 | gcc | -O2 | 36 | 53.9% |
| fission | gcc-m32 -O0 | gcc-m32 | -O0 | 36 | 69.3% |
| fission | gcc-m32 -O2 | gcc-m32 | -O2 | 36 | 48.9% |
| ghidra | clang -O0 | clang | -O0 | 36 | 75.0% |
| ghidra | clang -O2 | clang | -O2 | 36 | 80.6% |
| ghidra | gcc -O0 | gcc | -O0 | 36 | 0.0% |
| ghidra | gcc -O2 | gcc | -O2 | 35 | 94.3% |
| ghidra | gcc-m32 -O0 | gcc-m32 | -O0 | 36 | 91.7% |
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
| fission | gcc -O0 | 1.000 | 0.069 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1375ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.157 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2178ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.120 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10828ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.178 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2063ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.787 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9342ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.168 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1866ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.120 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10906ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.757 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10859ms | ✅ |
| fission | clang -O0 | 0.600 | 0.115 | 60.0% (3/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2025ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.517 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 10755ms | ❌ |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 3517ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.047 | 0.0% (0/5) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 16 | 11385ms | 🔴 compile |

### `add_ints` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.333 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 2954ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.431 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2877ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.739 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 5758ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.604 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 3096ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.604 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 1515ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.943 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 7942ms | ✅ |
| fission | clang -O0 | 1.000 | 0.342 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 1613ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.761 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 7996ms | ✅ |
| fission | clang -O2 | 1.000 | 0.431 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2628ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 8354ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.678 | 0.0% | #2 | 0 | 1 | GNR 0.57<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 4 | 5744ms | ❌ |
| ghidra | gcc-m32 -O0 | 0.000 | 0.943 | 0.0% (0/5) | #2 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5744ms | ❌ |

### `apply_binop` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.103 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.57<br>expr 0.58<br>cf 1.00<br>art 0 | 2954ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.402 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 2877ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.109 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.88<br>type 0.60<br>expr 0.74<br>cf 1.00<br>art 0 | 3096ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.658 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5744ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.413 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 1515ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.615 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7942ms | ✅ |
| fission | clang -O0 | 1.000 | 0.128 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.73<br>type 0.56<br>expr 0.70<br>cf 1.00<br>art 0 | 1613ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.535 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7996ms | ✅ |
| fission | clang -O2 | 1.000 | 0.424 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.88<br>type 0.60<br>expr 0.68<br>cf 1.00<br>art 0 | 2628ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.615 | 100.0% (6/6) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8354ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.395 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 7 | 5744ms | ❌ |
| ghidra | gcc -O2 | 0.000 | 0.198 | 0.0% (0/6) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 5758ms | 🔴 compile |

### `bounded_checksum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.098 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.62<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 5758ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.548 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 5744ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.286 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.22<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 7942ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.153 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.64<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 8354ms | ✅ |
| fission | gcc -O2 | 0.500 | 0.111 | 50.0% (3/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2877ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.167 | 0.095 | 16.7% (1/6) ⚠️intrin | #2 | 0 | 2 | GNR 0.11<br>type 0.50<br>expr 0.58<br>cf 1.00<br>art 1 | 1515ms | 🟤 assert |
| fission | gcc -O0 | 0.000 | 0.064 | 0.0% (0/6) ⚠️intrin | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 2 | 2954ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.421 | 0.0% | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 5744ms | ❌ |
| fission | gcc-m32 -O0 | 0.000 | 0.082 | 0.0% (0/6) ⚠️intrin | #2 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 2 | 3096ms | 🔴 compile |
| fission | clang -O0 | 0.000 | 0.117 | 0.0% (0/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1613ms | 🟠 runtime |
| ghidra | clang -O0 | 0.000 | 0.319 | 0.0% (0/6) | #1 | 0 | 2 | GNR 0.30<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 7996ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.044 | 0.0% (0/6) | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2628ms | 🔴 compile |

### `bounded_tlv_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.093 | 100.0% (7/7) | #1 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 2234ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.151 | 100.0% (7/7) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8467ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.084 | 100.0% (7/7) | #1 | 3 | 3 | GNR 0.58<br>type 0.50<br>expr 0.50<br>cf 0.67<br>art 0 | 1907ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.363 | 100.0% (7/7) | #1 | 0 | 3 | GNR 0.22<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 8149ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.149 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.61<br>type 0.50<br>expr 0.56<br>cf 1.00<br>art 0 | 9291ms | ✅ |
| fission | clang -O0 | 1.000 | 0.096 | 100.0% (7/7) | #1 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 21138ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.363 | 100.0% (7/7) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10636ms | ✅ |
| fission | gcc-m32 -O2 | 0.286 | 0.041 | 28.6% (2/7) | #2 | 6 | 2 | GNR 0.18<br>type 0.50<br>expr 0.47<br>cf 0.75<br>art 0 | 1954ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.334 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 7 | 9001ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.040 | 0.0% (0/7) ⚠️intrin | #2 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 9 | 1435ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 2256ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.040 | 0.0% (0/7) | #1 | 2 | 7 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 16 | 10666ms | 🔴 compile |

### `bubble_sort` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc-m32 -O0 | 1.000 | 0.050 | 100.0% (5/5) | #1 | 2 | 4 | GNR 0.37<br>type 0.50<br>expr 0.40<br>cf 0.71<br>art 0 | 2047ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.152 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.12<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 8442ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.190 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.12<br>type 0.50<br>expr 0.72<br>cf 1.00<br>art 0 | 8202ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.361 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.57<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 8815ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.100 | 100.0% (5/5) | #1 | 0 | 7 | GNR 0.74<br>type 0.50<br>expr 0.52<br>cf 1.00<br>art 0 | 8795ms | ✅ |
| fission | gcc -O0 | 0.800 | 0.054 | 80.0% (4/5) | #1 | 2 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1707ms | 🟤 assert |
| fission | clang -O0 | 0.800 | 0.090 | 80.0% (4/5) | #2 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1483ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.167 | 0.0% | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 15 | 8618ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.058 | 0.0% (0/5) | #1 | 3 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1882ms | 🔴 compile |
| ghidra | gcc -O2 | 0.000 | 0.131 | 0.0% (0/5) | #1 | 0 | 5 | GNR 0.26<br>type 0.42<br>expr 0.51<br>cf 1.00<br>art 2 | 8611ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.032 | 0.0% (0/5) | #2 | 3 | 4 | GNR 0.14<br>type 0.50<br>expr 0.53<br>cf 0.91<br>art 0 | 1878ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.032 | 0.0% (0/5) | #2 | 15 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1360ms | 🟠 runtime |

### `checksum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.111 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2118ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.081 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1857ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.129 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 10859ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.112 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.78<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 1876ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.819 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 9808ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.147 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.24<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 2097ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.116 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 9451ms | ✅ |
| fission | clang -O0 | 1.000 | 0.111 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2108ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.732 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 10722ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.144 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.71<br>type 0.50<br>expr 0.49<br>cf 1.00<br>art 0 | 10566ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.668 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 10673ms | ❌ |
| fission | clang -O2 | 0.000 | 0.036 | 0.0% (0/5) | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1485ms | 🔴 compile |

### `clamp` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.144 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 2118ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.112 | 100.0% (6/6) ⚠️intrin | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 1857ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.582 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 10859ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.515 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 1876ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.590 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 9808ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.199 | 100.0% (6/6) ⚠️intrin | #1 | 0 | 2 | GNR 0.29<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 1 | 2097ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.731 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 9451ms | ✅ |
| fission | clang -O0 | 1.000 | 0.118 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.91<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 2108ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.421 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.26<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 0 | 10722ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.731 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.91<br>cf 1.00<br>art 0 | 10566ms | ✅ |
| fission | clang -O2 | 0.333 | 0.181 | 33.3% (2/6) | #2 | 0 | 1 | GNR 0.89<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 1485ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.421 | 0.0% | #2 | 0 | 2 | GNR 0.75<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 9 | 10673ms | ❌ |

### `count_bits` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.336 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.92<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 2118ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.265 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.33<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 1857ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.609 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 10859ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.510 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.89<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 1876ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.755 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 9808ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.421 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 2097ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.609 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 9451ms | ✅ |
| fission | clang -O0 | 1.000 | 0.288 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.92<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 2108ms | ✅ |
| fission | clang -O2 | 1.000 | 0.226 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.27<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 1485ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.581 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.53<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 10566ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.688 | 0.0% | #2 | 0 | 2 | GNR 0.14<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 2 | 10673ms | ❌ |
| ghidra | clang -O0 | 0.000 | 0.298 | 0.0% (0/6) | #2 | 0 | 2 | GNR 0.69<br>type 0.33<br>expr 0.78<br>cf 1.00<br>art 2 | 10722ms | 🟡 timeout |

### `crc32` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.062 | 100.0% (6/6) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 3903ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.293 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.50<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 0 | 16698ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.400 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 15872ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.305 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.50<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 0 | 15753ms | ✅ |
| fission | clang -O0 | 1.000 | 0.045 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3338ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.474 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 16964ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.057 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.70<br>type 0.50<br>expr 0.50<br>cf 1.00<br>art 0 | 16529ms | ✅ |
| fission | clang -O2 | 0.333 | 0.063 | 33.3% (2/6) | #2 | 1 | 3 | GNR 0.06<br>type 0.50<br>expr 0.56<br>cf 1.00<br>art 0 | 2863ms | 🟤 assert |
| fission | gcc -O2 | 0.167 | 0.060 | 16.7% (1/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3979ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.167 | 0.081 | 16.7% (1/6) | #2 | 2 | 3 | GNR 0.55<br>type 0.50<br>expr 0.65<br>cf 0.50<br>art 0 | 3235ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.167 | 0.054 | 16.7% (1/6) | #2 | 0 | 4 | GNR 0.15<br>type 0.50<br>expr 0.66<br>cf 1.00<br>art 0 | 3244ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.343 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 16432ms | ❌ |

### `dot_product_stride` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.073 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5758ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.566 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.12<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 5744ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.239 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.30<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 7942ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.494 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7996ms | ✅ |
| fission | gcc -O0 | 0.000 | 0.118 | 0.0% (0/5) | #1 | 1 | 3 | GNR 0.93<br>type 0.50<br>expr 0.80<br>cf 0.67<br>art 0 | 2954ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.474 | 0.0% | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 5744ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.072 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2877ms | 🔴 compile |
| fission | gcc-m32 -O0 | 0.000 | 0.163 | 0.0% (0/5) | #2 | 1 | 3 | GNR 0.91<br>type 0.50<br>expr 0.81<br>cf 0.67<br>art 0 | 3096ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.094 | 0.0% (0/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1515ms | 🟠 runtime |
| fission | clang -O0 | 0.000 | 0.086 | 0.0% (0/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1613ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 2628ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.049 | 0.0% (0/5) | #1 | 1 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 13 | 8354ms | 🔴 compile |

### `factorial` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.239 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1707ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8611ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.579 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8442ms | ✅ |
| fission | clang -O0 | 1.000 | 0.209 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1483ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.504 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 8815ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.290 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8795ms | ✅ |
| fission | gcc -O2 | 0.400 | 0.153 | 40.0% (2/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1882ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.400 | 0.132 | 40.0% (2/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2047ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.400 | 0.026 | 40.0% (2/5) ⚠️intrin | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 16 | 1878ms | 🟤 assert |
| fission | clang -O2 | 0.400 | 0.288 | 40.0% (2/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1360ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.335 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 3 | 8618ms | ❌ |
| ghidra | gcc-m32 -O2 | 0.000 | 0.136 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8202ms | 🔴 compile |

### `fibonacci` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.222 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 1707ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.218 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.59<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 8611ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.598 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.35<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 8442ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.260 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.64<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 8202ms | ✅ |
| fission | clang -O0 | 1.000 | 0.200 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.55<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 1483ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.484 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.45<br>type 0.40<br>expr 0.77<br>cf 1.00<br>art 1 | 8815ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.254 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.67<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 8795ms | ✅ |
| fission | gcc-m32 -O0 | 0.500 | 0.236 | 50.0% (3/6) | #2 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 2047ms | 🟤 assert |
| fission | gcc -O2 | 0.333 | 0.138 | 33.3% (2/6) | #2 | 1 | 3 | GNR 0.10<br>type 0.50<br>expr 0.62<br>cf 1.00<br>art 0 | 1882ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.333 | 0.190 | 33.3% (2/6) | #2 | 0 | 3 | GNR 0.21<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 1878ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.321 | 0.0% | #2 | 0 | 2 | GNR 0.53<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 4 | 8618ms | ❌ |
| fission | clang -O2 | 0.000 | 0.170 | 0.0% (0/6) | #2 | 1 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1360ms | 🟡 timeout |

### `find_pair_value` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.090 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1375ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10828ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.119 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.52<br>type 0.50<br>expr 0.54<br>cf 1.00<br>art 0 | 2063ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.695 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 9342ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.212 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10906ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.472 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10859ms | ✅ |
| fission | clang -O2 | 1.000 | 0.106 | 100.0% (5/5) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3517ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.442 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11385ms | ✅ |
| fission | clang -O0 | 0.800 | 0.109 | 80.0% (4/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2025ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.342 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 10755ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.175 | 0.0% (0/5) | #2 | 2 | 4 | GNR 0.47<br>type 0.50<br>expr 0.80<br>cf 0.71<br>art 0 | 2178ms | 🟡 timeout |
| fission | gcc-m32 -O2 | 0.000 | 0.154 | 0.0% (0/5) | #2 | 2 | 4 | GNR 0.36<br>type 0.50<br>expr 0.70<br>cf 0.71<br>art 0 | 1866ms | 🟡 timeout |

### `find_substring` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.162 | 100.0% (6/6) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 28440ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.401 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.16<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 26208ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.204 | 100.0% (6/6) | #1 | 0 | 5 | GNR 0.42<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 23180ms | ✅ |
| fission | clang -O0 | 1.000 | 0.039 | 100.0% (6/6) | #1 | 11 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4583ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.223 | 100.0% (6/6) | #1 | 0 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 25773ms | ✅ |
| fission | gcc-m32 -O2 | 0.500 | 0.051 | 50.0% (3/6) | #2 | 3 | 6 | GNR 0.27<br>type 0.50<br>expr 0.65<br>cf 0.80<br>art 0 | 5261ms | 🟤 assert |
| fission | gcc -O0 | 0.000 | 0.053 | 0.0% (0/6) | #1 | 6 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4449ms | 🟡 timeout |
| ghidra | gcc -O0 | 0.000 | 0.281 | 0.0% | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 10 | 26677ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.075 | 0.0% (0/6) | #2 | 2 | 6 | GNR 0.39<br>type 0.50<br>expr 0.67<br>cf 0.80<br>art 0 | 4584ms | 🔴 compile |
| fission | gcc-m32 -O0 | 0.000 | 0.088 | 0.0% (0/6) | #2 | 3 | 3 | GNR 0.35<br>type 0.50<br>expr 0.64<br>cf 0.75<br>art 0 | 4512ms | 🟡 timeout |
| ghidra | clang -O0 | 0.000 | 0.142 | 0.0% (0/6) | #2 | 0 | 5 | GNR 0.43<br>type 0.50<br>expr 0.64<br>cf 1.00<br>art 0 | 24221ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.057 | 0.0% (0/6) | #2 | 7 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4026ms | 🔴 compile |

### `kv_lookup` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.064 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2954ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.146 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5758ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.088 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.52<br>type 0.50<br>expr 0.54<br>cf 1.00<br>art 0 | 3096ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.681 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 5744ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.189 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7942ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.455 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 7996ms | ✅ |
| fission | clang -O2 | 1.000 | 0.108 | 100.0% (6/6) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2628ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.412 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8354ms | ✅ |
| fission | clang -O0 | 0.833 | 0.106 | 83.3% (5/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1613ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.316 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 5744ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.148 | 0.0% (0/6) | #2 | 2 | 4 | GNR 0.47<br>type 0.50<br>expr 0.80<br>cf 0.71<br>art 0 | 2877ms | 🟡 timeout |
| fission | gcc-m32 -O2 | 0.000 | 0.141 | 0.0% (0/6) | #2 | 2 | 4 | GNR 0.36<br>type 0.50<br>expr 0.70<br>cf 0.71<br>art 0 | 1515ms | 🟡 timeout |

### `linear_search` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.203 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.63<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 1707ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.660 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8611ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.205 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.58<br>cf 1.00<br>art 0 | 2047ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.617 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 8442ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.688 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.47<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 8202ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.401 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.00<br>type 0.50<br>expr 0.89<br>cf 1.00<br>art 0 | 8815ms | ✅ |
| fission | clang -O2 | 1.000 | 0.171 | 100.0% (6/6) | #1 | 2 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1360ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.317 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.47<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 8795ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.371 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 8618ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.222 | 0.0% (0/6) | #2 | 2 | 4 | GNR 0.42<br>type 0.50<br>expr 0.83<br>cf 0.71<br>art 0 | 1882ms | 🟡 timeout |
| fission | gcc-m32 -O2 | 0.000 | 0.194 | 0.0% (0/6) | #2 | 2 | 4 | GNR 0.42<br>type 0.50<br>expr 0.83<br>cf 0.71<br>art 0 | 1878ms | 🟡 timeout |
| fission | clang -O0 | 0.000 | 0.200 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1483ms | 🟡 timeout |

### `list_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.171 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.67<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 2954ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.453 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.91<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 5758ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.099 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.67<br>type 0.50<br>expr 0.53<br>cf 1.00<br>art 0 | 3096ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.652 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 5744ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.573 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 7942ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.573 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 1 | 8354ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.595 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 2 | 5744ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.411 | 0.0% (0/5) | #2 | 0 | 3 | GNR 0.33<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 2877ms | 🟡 timeout |
| fission | gcc-m32 -O2 | 0.000 | 0.478 | 0.0% (0/5) | #2 | 0 | 3 | GNR 0.33<br>type 0.50<br>expr 0.84<br>cf 1.00<br>art 0 | 1515ms | 🟡 timeout |
| fission | clang -O0 | 0.000 | 0.144 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1613ms | 🟠 runtime |
| ghidra | clang -O0 | 0.000 | 0.353 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 7996ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.411 | 0.0% (0/5) | #2 | 0 | 3 | GNR 0.33<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 2628ms | 🟡 timeout |

### `manipulate_bitfields` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.312 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 25846ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.312 | 100.0% (5/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 23502ms | ✅ |
| fission | gcc -O2 | 0.800 | 0.097 | 80.0% (4/5) | #2 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3964ms | 🟤 assert |
| fission | clang -O0 | 0.800 | 0.051 | 80.0% (4/5) ⚠️intrin | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 5206ms | 🟤 assert |
| fission | clang -O2 | 0.800 | 0.085 | 80.0% (4/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4331ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.200 | 0.069 | 20.0% (1/5) ⚠️intrin | #2 | 0 | 2 | GNR 0.14<br>type 0.50<br>expr 0.50<br>cf 1.00<br>art 1 | 4314ms | 🟤 assert |
| fission | gcc -O0 | 0.000 | 0.036 | 0.0% (0/5) ⚠️intrin | #1 | 0 | 2 | GNR 0.08<br>type 0.50<br>expr 0.46<br>cf 1.00<br>art 13 | 4025ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.119 | 0.0% | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 25121ms | ❌ |
| fission | gcc-m32 -O0 | 0.000 | 0.026 | 0.0% (0/5) ⚠️intrin | #1 | 0 | 2 | GNR 0.09<br>type 0.50<br>expr 0.46<br>cf 1.00<br>art 13 | 4209ms | 🔴 compile |
| ghidra | gcc-m32 -O0 | 0.000 | 0.208 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 24989ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.205 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 25141ms | 🔴 compile |
| ghidra | clang -O2 | 0.000 | 0.341 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 25575ms | 🔴 compile |

### `matrix_multiply` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.043 | 100.0% (5/5) | #1 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4025ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.206 | 100.0% (5/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 25846ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.489 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 24989ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.163 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.38<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 23502ms | ✅ |
| fission | clang -O0 | 1.000 | 0.063 | 100.0% (5/5) | #1 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 5206ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.701 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 25141ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.197 | 100.0% (5/5) | #1 | 0 | 6 | GNR 0.46<br>type 0.50<br>expr 0.50<br>cf 1.00<br>art 0 | 25575ms | ✅ |
| fission | gcc -O2 | 0.200 | 0.052 | 20.0% (1/5) | #2 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3964ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.387 | 0.0% | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 25121ms | ❌ |
| fission | gcc-m32 -O0 | 0.000 | 0.033 | 0.0% (0/5) | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4209ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.029 | 0.0% (0/5) | #2 | 3 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4314ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.053 | 0.0% (0/5) | #2 | 9 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 4331ms | 🔴 compile |

### `mixed_width_accumulate` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.205 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.15<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 8467ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.629 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.30<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 8149ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.187 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.33<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 9291ms | ✅ |
| fission | gcc -O0 | 0.500 | 0.092 | 50.0% (3/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2234ms | 🟤 assert |
| fission | gcc -O2 | 0.500 | 0.163 | 50.0% (3/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1435ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.500 | 0.056 | 50.0% (3/6) | #2 | 0 | 4 | GNR 0.60<br>type 0.50<br>expr 0.52<br>cf 1.00<br>art 0 | 1907ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.333 | 0.046 | 33.3% (2/6) | #2 | 0 | 3 | GNR 0.24<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 1954ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.181 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 9001ms | ❌ |
| fission | clang -O0 | 0.000 | 0.064 | 0.0% (0/6) ⚠️intrin | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 21138ms | 🟡 timeout |
| ghidra | clang -O0 | 0.000 | 0.328 | 0.0% (0/6) | #1 | 0 | 3 | GNR 0.24<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 10636ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 2256ms | ❌ Decompiler returned whole-prog |
| ghidra | clang -O2 | 0.000 | 0.044 | 0.0% (0/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 10666ms | 🔴 compile |

### `mul_ints` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.237 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2954ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.429 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2877ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.739 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.80<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 5758ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.470 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3096ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 5744ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.470 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1515ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.943 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 7942ms | ✅ |
| fission | clang -O0 | 1.000 | 0.243 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1613ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.761 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 7996ms | ✅ |
| fission | clang -O2 | 1.000 | 0.429 | 100.0% (5/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2628ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.989 | 100.0% (5/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 8354ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.678 | 0.0% | #2 | 0 | 1 | GNR 0.57<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 4 | 5744ms | ❌ |

### `overlap_move` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.050 | 100.0% (6/6) | #1 | 4 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 2234ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.068 | 100.0% (6/6) | #1 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1435ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.236 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 8467ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.073 | 100.0% (6/6) | #1 | 3 | 3 | GNR 0.64<br>type 0.50<br>expr 0.50<br>cf 0.83<br>art 0 | 1907ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.528 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.00<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 8149ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.034 | 100.0% (6/6) | #1 | 1 | 4 | GNR 0.36<br>type 0.50<br>expr 0.45<br>cf 0.83<br>art 0 | 1954ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.238 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 9291ms | ✅ |
| fission | clang -O0 | 1.000 | 0.040 | 100.0% (6/6) | #1 | 3 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 21138ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.398 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.17<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 10636ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.048 | 100.0% (6/6) | #1 | 3 | 8 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 43 | 10666ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.269 | 0.0% | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 9001ms | ❌ |
| fission | clang -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 2256ms | ❌ Decompiler returned whole-prog |

### `pointer_stride_sum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.290 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1375ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.292 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2178ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.609 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.29<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 10828ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.342 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.64<br>type 0.50<br>expr 0.67<br>cf 1.00<br>art 0 | 2063ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.674 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 9342ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.316 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.20<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 1866ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.648 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.29<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 10906ms | ✅ |
| fission | clang -O0 | 1.000 | 0.129 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2025ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.489 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 10859ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.079 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11385ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.259 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 10755ms | ❌ |
| fission | clang -O2 | 0.000 | 0.024 | 0.0% (0/5) ⚠️intrin | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 1 | 3517ms | 🔴 compile |

### `power` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.243 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1707ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.203 | 100.0% (6/6) | #1 | 2 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1882ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.392 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8611ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.492 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8442ms | ✅ |
| fission | clang -O0 | 1.000 | 0.231 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1483ms | ✅ |
| fission | clang -O2 | 1.000 | 0.213 | 100.0% (6/6) | #1 | 1 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1360ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.264 | 100.0% (6/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8795ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.374 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 8618ms | ❌ |
| fission | gcc-m32 -O0 | 0.000 | 0.073 | 0.0% (0/6) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2047ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.064 | 0.0% (0/6) | #1 | 1 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1878ms | 🔴 compile |
| ghidra | gcc-m32 -O2 | 0.000 | 0.249 | 0.0% (0/6) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8202ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.215 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 1 | 8815ms | 🔴 compile |

### `process_code` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.103 | 100.0% (5/5) | #1 | 2 | 3 | GNR 0.89<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 1707ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.069 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.24<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 1882ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.286 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 8611ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.111 | 100.0% (5/5) | #1 | 0 | 6 | GNR 0.89<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 2047ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.166 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.44<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 8442ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.286 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 8202ms | ✅ |
| fission | clang -O0 | 1.000 | 0.139 | 100.0% (5/5) | #1 | 2 | 3 | GNR 0.89<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 1483ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.149 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.41<br>type 0.38<br>expr 0.80<br>cf 1.00<br>art 1 | 8815ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.309 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.50<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 8795ms | ✅ |
| fission | clang -O2 | 0.600 | 0.126 | 60.0% (3/5) | #2 | 0 | 5 | GNR 0.24<br>type 0.50<br>expr 0.69<br>cf 1.00<br>art 0 | 1360ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.157 | 0.0% | #2 | 0 | 4 | GNR 0.88<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 8 | 8618ms | ❌ |
| fission | gcc-m32 -O2 | 0.000 | 0.087 | 0.0% (0/5) | #2 | 0 | 5 | GNR 0.25<br>type 0.50<br>expr 0.70<br>cf 1.00<br>art 0 | 1878ms | ❌ |

### `rc4_crypt` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.032 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3903ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.016 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3979ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.234 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.44<br>type 0.50<br>expr 0.62<br>cf 1.00<br>art 0 | 16698ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.030 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.41<br>type 0.50<br>expr 0.40<br>cf 1.00<br>art 0 | 3235ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.440 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.10<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 15872ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.022 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.27<br>type 0.50<br>expr 0.45<br>cf 1.00<br>art 0 | 3244ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.247 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.57<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 15753ms | ✅ |
| fission | clang -O0 | 1.000 | 0.072 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3338ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.384 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.09<br>type 0.50<br>expr 0.62<br>cf 1.00<br>art 0 | 16964ms | ✅ |
| fission | clang -O2 | 1.000 | 0.027 | 100.0% (5/5) | #1 | 1 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2863ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.162 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.75<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 16529ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.292 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 17 | 16432ms | ❌ |

### `rc4_init` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc-m32 -O0 | 1.000 | 0.544 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.11<br>type 0.50<br>expr 0.65<br>cf 1.00<br>art 0 | 15872ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.233 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.69<br>type 0.50<br>expr 0.61<br>cf 1.00<br>art 0 | 15753ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.236 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.24<br>type 0.50<br>expr 0.63<br>cf 1.00<br>art 0 | 16964ms | ✅ |
| fission | gcc -O0 | 0.200 | 0.042 | 20.0% (1/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3903ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.200 | 0.032 | 20.0% (1/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3235ms | 🟤 assert |
| fission | clang -O0 | 0.200 | 0.032 | 20.0% (1/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3338ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.362 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 14 | 16432ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.022 | 0.0% (0/5) | #1 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3979ms | 🔴 compile |
| ghidra | gcc -O2 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 16698ms | ❌ Decompiler returned whole-prog |
| fission | gcc-m32 -O2 | 0.000 | 0.100 | 0.0% (0/5) | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 3244ms | 🟠 runtime |
| fission | clang -O2 | 0.000 | 0.033 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2863ms | 🔴 compile |
| ghidra | clang -O2 | 0.000 | 0.081 | 0.0% (0/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 33 | 16529ms | 🔴 compile |

### `reverse_in_place` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.059 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1375ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.221 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 10828ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.073 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.43<br>type 0.50<br>expr 0.38<br>cf 1.00<br>art 0 | 2063ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.339 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.25<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 9342ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.221 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 0 | 10906ms | ✅ |
| fission | clang -O0 | 1.000 | 0.100 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2025ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.325 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.26<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 10859ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.146 | 100.0% (5/5) | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11385ms | ✅ |
| fission | gcc-m32 -O2 | 0.400 | 0.130 | 40.0% (2/5) | #2 | 2 | 2 | GNR 0.27<br>type 0.50<br>expr 0.67<br>cf 0.60<br>art 0 | 1866ms | 🟤 assert |
| fission | gcc -O2 | 0.200 | 0.124 | 20.0% (1/5) | #2 | 2 | 2 | GNR 0.28<br>type 0.50<br>expr 0.68<br>cf 0.60<br>art 0 | 2178ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.323 | 0.0% | #2 | 0 | 2 | GNR 0.60<br>type 0.50<br>expr 0.71<br>cf 1.00<br>art 11 | 10755ms | ❌ |
| fission | clang -O2 | 0.000 | 0.072 | 0.0% (0/5) | #2 | 1 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 3517ms | 🔴 compile |

### `reverse_string` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.098 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4449ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.233 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 28440ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.067 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.52<br>type 0.50<br>expr 0.53<br>cf 1.00<br>art 0 | 4512ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.353 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.16<br>type 0.50<br>expr 0.78<br>cf 1.00<br>art 0 | 26208ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.263 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 23180ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.256 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.14<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 24221ms | ✅ |
| fission | clang -O2 | 1.000 | 0.103 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.24<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 4026ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.252 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.12<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 25773ms | ✅ |
| fission | clang -O0 | 0.600 | 0.145 | 60.0% (3/5) | #2 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4583ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.251 | 0.0% | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 6 | 26677ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.046 | 0.0% (0/5) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 4584ms | 🔴 compile |
| fission | gcc-m32 -O2 | 0.000 | 0.042 | 0.0% (0/5) | #2 | 0 | 2 | GNR 0.16<br>type 0.50<br>expr 0.57<br>cf 1.00<br>art 0 | 5261ms | 🔴 compile |

### `rolling_hash32` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O2 | 1.000 | 0.139 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1435ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.303 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 8467ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.783 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 8149ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.190 | 100.0% (6/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1954ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.303 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.38<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 9291ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.558 | 100.0% (6/6) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 10636ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.340 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.64<br>type 0.50<br>expr 0.60<br>cf 1.00<br>art 0 | 10666ms | ✅ |
| fission | gcc -O0 | 0.333 | 0.118 | 33.3% (2/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2234ms | 🟤 assert |
| fission | gcc-m32 -O0 | 0.167 | 0.113 | 16.7% (1/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1907ms | 🟤 assert |
| fission | clang -O0 | 0.167 | 0.096 | 16.7% (1/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 21138ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.414 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 9001ms | ❌ |
| fission | clang -O2 | 0.000 | 0.087 | 0.0% (0/6) | #2 | 1 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2256ms | 🟠 runtime |

### `rotate_words` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| ghidra | gcc -O2 | 1.000 | 0.217 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.46<br>type 0.50<br>expr 0.66<br>cf 1.00<br>art 0 | 8467ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.040 | 100.0% (6/6) ⚠️intrin | #1 | 0 | 3 | GNR 0.10<br>type 0.50<br>expr 0.56<br>cf 1.00<br>art 4 | 1954ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.213 | 100.0% (6/6) | #1 | 0 | 3 | GNR 0.44<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 9291ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.152 | 100.0% (6/6) | #1 | 0 | 4 | GNR 0.72<br>type 0.50<br>expr 0.47<br>cf 1.00<br>art 0 | 10666ms | ✅ |
| fission | clang -O2 | 0.833 | 0.048 | 83.3% (5/6) ⚠️intrin | #2 | 3 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 7 | 2256ms | 🟤 assert |
| fission | clang -O0 | 0.667 | 0.044 | 66.7% (4/6) ⚠️intrin | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 13 | 21138ms | 🟤 assert |
| fission | gcc -O2 | 0.500 | 0.038 | 50.0% (3/6) ⚠️intrin | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 1435ms | 🟤 assert |
| fission | gcc -O0 | 0.000 | 0.043 | 0.0% (0/6) ⚠️intrin | #1 | 0 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 3 | 2234ms | 🔴 compile |
| ghidra | gcc -O0 | 0.000 | 0.337 | 0.0% | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 5 | 9001ms | ❌ |
| fission | gcc-m32 -O0 | 0.000 | 0.067 | 0.0% (0/6) ⚠️intrin | #1 | 0 | 4 | GNR 0.31<br>type 0.50<br>expr 0.40<br>cf 1.00<br>art 3 | 1907ms | 🔴 compile |
| ghidra | gcc-m32 -O0 | 0.000 | 0.398 | 0.0% (0/6) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 8149ms | 🔴 compile |
| ghidra | clang -O0 | 0.000 | 0.344 | 0.0% (0/6) | #2 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 10636ms | 🔴 compile |

### `saturating_add` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.137 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.44<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 2118ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.606 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.40<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 10859ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.317 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.94<br>type 0.50<br>expr 0.53<br>cf 1.00<br>art 0 | 1876ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.246 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.47<br>type 0.50<br>expr 0.80<br>cf 1.00<br>art 0 | 9808ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.606 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.40<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 9451ms | ✅ |
| fission | clang -O0 | 1.000 | 0.141 | 100.0% (5/5) | #1 | 0 | 5 | GNR 0.66<br>type 0.50<br>expr 0.73<br>cf 1.00<br>art 0 | 2108ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.315 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.42<br>type 0.50<br>expr 0.81<br>cf 1.00<br>art 0 | 10722ms | ✅ |
| fission | gcc -O2 | 0.800 | 0.319 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.68<br>type 0.50<br>expr 0.68<br>cf 1.00<br>art 0 | 1857ms | 🟤 assert |
| fission | gcc-m32 -O2 | 0.800 | 0.282 | 80.0% (4/5) | #2 | 0 | 5 | GNR 0.55<br>type 0.50<br>expr 0.79<br>cf 1.00<br>art 0 | 2097ms | 🟤 assert |
| ghidra | gcc -O0 | 0.000 | 0.252 | 0.0% | #2 | 0 | 3 | GNR 0.84<br>type 0.50<br>expr 0.76<br>cf 1.00<br>art 8 | 10673ms | ❌ |
| fission | clang -O2 | 0.000 | 0.396 | 0.0% (0/5) | #1 | 0 | 1 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1485ms | ❌ |
| ghidra | clang -O2 | 0.000 | 0.432 | 0.0% (0/5) | #1 | 0 | 1 | GNR 0.00<br>type 0.50<br>expr 0.93<br>cf 1.00<br>art 0 | 10566ms | ❌ |

### `signum` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.335 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 2118ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.133 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.24<br>type 0.50<br>expr 0.74<br>cf 1.00<br>art 0 | 1857ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.492 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.77<br>cf 1.00<br>art 0 | 10859ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.580 | 100.0% (5/5) | #1 | 0 | 4 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 1876ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.611 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.56<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 9808ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.421 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.25<br>type 0.50<br>expr 0.82<br>cf 1.00<br>art 0 | 2097ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.583 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.84<br>cf 1.00<br>art 0 | 9451ms | ✅ |
| fission | clang -O0 | 1.000 | 0.340 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.75<br>type 0.50<br>expr 0.75<br>cf 1.00<br>art 0 | 2108ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.523 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.50<br>type 0.38<br>expr 0.87<br>cf 1.00<br>art 1 | 10722ms | ✅ |
| fission | clang -O2 | 1.000 | 0.117 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.80<br>type 0.50<br>expr 0.72<br>cf 1.00<br>art 0 | 1485ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.624 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.50<br>type 0.50<br>expr 0.86<br>cf 1.00<br>art 0 | 10566ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.375 | 0.0% | #2 | 0 | 3 | GNR 0.80<br>type 0.50<br>expr 0.85<br>cf 1.00<br>art 3 | 10673ms | ❌ |

### `state_machine_score` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.048 | 100.0% (7/7) | #1 | 18 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 2234ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.125 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.72<br>type 0.50<br>expr 0.61<br>cf 0.87<br>art 0 | 8467ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.054 | 100.0% (7/7) | #1 | 18 | 3 | GNR 0.58<br>type 0.50<br>expr 0.57<br>cf 0.37<br>art 0 | 1907ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.117 | 100.0% (7/7) | #1 | 2 | 6 | GNR 0.16<br>type 0.50<br>expr 0.66<br>cf 0.52<br>art 0 | 8149ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.125 | 100.0% (7/7) | #1 | 0 | 5 | GNR 0.72<br>type 0.50<br>expr 0.61<br>cf 0.87<br>art 0 | 9291ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.237 | 100.0% (7/7) | #1 | 2 | 5 | GNR 0.74<br>type 0.50<br>expr 0.56<br>cf 0.48<br>art 0 | 10666ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.107 | 0.0% | #2 | 2 | 6 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 5 | 9001ms | ❌ |
| fission | gcc -O2 | 0.000 | 0.081 | 0.0% (0/7) | #2 | 5 | 4 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 1435ms | 🟡 timeout |
| fission | gcc-m32 -O2 | 0.000 | 0.078 | 0.0% (0/7) | #2 | 6 | 4 | GNR 0.16<br>type 0.50<br>expr 0.57<br>cf 0.62<br>art 0 | 1954ms | 🟡 timeout |
| fission | clang -O0 | 0.000 | 0.000 | 0.0% | — | 0 | 0 | — | 21138ms | ❌ preview_timeout: Rust-Sleigh r |
| ghidra | clang -O0 | 0.000 | 0.146 | 0.0% (0/7) | #1 | 0 | 4 | GNR 0.11<br>type 0.50<br>expr 0.58<br>cf 0.67<br>art 0 | 10636ms | 🔴 compile |
| fission | clang -O2 | 0.000 | 0.070 | 0.0% (0/7) | #2 | 3 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 2256ms | 🟠 runtime |

### `sum_array` 🟢 Fission leads
| Decompiler | Variant | Correctness | Similarity | Semantic | Correctness Rank | Gotos | Depth | Readability Proxies | Time | Status |
| ---|---|---|---|---|---|---|---|---|---|--- |
| fission | gcc -O0 | 1.000 | 0.155 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1375ms | ✅ |
| fission | gcc -O2 | 1.000 | 0.357 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2178ms | ✅ |
| ghidra | gcc -O2 | 1.000 | 0.171 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 10828ms | ✅ |
| fission | gcc-m32 -O0 | 1.000 | 0.225 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.68<br>type 0.50<br>expr 0.55<br>cf 1.00<br>art 0 | 2063ms | ✅ |
| ghidra | gcc-m32 -O0 | 1.000 | 0.833 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 9342ms | ✅ |
| fission | gcc-m32 -O2 | 1.000 | 0.363 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 1866ms | ✅ |
| ghidra | gcc-m32 -O2 | 1.000 | 0.171 | 100.0% (5/5) | #1 | 0 | 3 | GNR 0.28<br>type 0.50<br>expr 0.83<br>cf 1.00<br>art 0 | 10906ms | ✅ |
| fission | clang -O0 | 1.000 | 0.141 | 100.0% (5/5) | #1 | 0 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 2025ms | ✅ |
| ghidra | clang -O0 | 1.000 | 0.733 | 100.0% (5/5) | #1 | 0 | 2 | GNR 0.00<br>type 0.50<br>expr 0.88<br>cf 1.00<br>art 0 | 10859ms | ✅ |
| ghidra | clang -O2 | 1.000 | 0.030 | 100.0% (5/5) | #1 | 0 | 5 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 0 | 11385ms | ✅ |
| ghidra | gcc -O0 | 0.000 | 0.648 | 0.0% | #2 | 0 | 2 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 1.00<br>art 4 | 10755ms | ❌ |
| fission | clang -O2 | 0.000 | 0.012 | 0.0% (0/5) | #2 | 6 | 3 | GNR 1.00<br>type 0.00<br>expr 0.00<br>cf 0.00<br>art 0 | 3517ms | 🔴 compile |

---

## Overfitting Analysis

Functions where **all** decompilers scored below 0.3 are marked as objectively hard.
Functions where **only Fission** scored below 0.3 are marked as quality gaps.

**Fission quality gaps (1):** `dot_product_stride`