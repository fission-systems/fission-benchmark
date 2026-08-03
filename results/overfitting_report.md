# Dev vs Holdout Overfitting Report

- Dev results: `results/dev_publish.json`  
- Holdout results: `results/holdout_latest.json`  
- Overfitting threshold: **10.0pp** drop

## Summary by Decompiler

| Decompiler | Dev N | Dev Correctness | Holdout N | Holdout Correctness | Drop (pp) | Flag |
|---|---|---|---|---|---|---|
| **fission** | 210 | 0.626 | 30 | 0.640 | -1.4pp | ✅ |
| **ghidra** | 215 | 0.726 | 30 | 0.767 | -4.1pp | ✅ |
