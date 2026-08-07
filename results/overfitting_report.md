# Dev vs Holdout Overfitting Report

- Dev results: `results/dev_publish.json`  
- Holdout results: `results/holdout_latest.json`  
- Overfitting threshold: **10.0pp** drop

## Summary by Decompiler

| Decompiler | Dev N | Dev Correctness | Holdout N | Holdout Correctness | Drop (pp) | Flag |
|---|---|---|---|---|---|---|
| **fission** | 211 | 0.685 | 30 | 0.672 | +1.3pp | ✅ |
| **ghidra** | 215 | 0.726 | 30 | 0.800 | -7.4pp | ✅ |
