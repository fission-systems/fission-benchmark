# Dev vs Holdout Overfitting Report

- Dev results: `results/dev_publish.json`  
- Holdout results: `results/holdout_latest.json`  
- Overfitting threshold: **10.0pp** drop

## Summary by Decompiler

| Decompiler | Dev N | Dev Correctness | Holdout N | Holdout Correctness | Drop (pp) | Flag |
|---|---|---|---|---|---|---|
| **fission** | 210 | 0.625 | 30 | 0.673 | -4.8pp | ✅ |
| **ghidra** | 215 | 0.768 | 30 | 0.751 | +1.7pp | ✅ |
