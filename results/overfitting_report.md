# Dev vs Holdout Overfitting Report

- Dev results: `results/dev_publish.json`  
- Holdout results: `results/holdout_latest.json`  
- Overfitting threshold: **10.0pp** drop

## Summary by Decompiler

| Decompiler | Dev N | Dev Correctness | Holdout N | Holdout Correctness | Drop (pp) | Flag |
|---|---|---|---|---|---|---|
| **fission** | 213 | 0.650 | 30 | 0.668 | -1.8pp | ✅ |
| **ghidra** | 215 | 0.730 | 30 | 0.800 | -7.0pp | ✅ |
