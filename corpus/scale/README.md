# Scale corpus

This directory materializes a pinned slice of the public
noelo-lab/decbench-dataset without committing third-party binaries.

    python scripts/materialize_scale_corpus.py --config unoptimized
    python runner/runner.py --corpus scale --profile decbench_scale_smoke \
      --run-mode local --decompilers fission,ghidra

The pinned unoptimized slice contains 34,406 upstream function records and
34,098 requested records after the five real-malware projects are excluded.
The current materialization resolves 34,097 DWARF addresses, and 33,041 of
those subjects (96.90%) have a matching function in the published source CFGs.
Both counts are locked against silent upstream/importer drift. Every subject
is identified as decbench::project::binary::symbol, so common symbols such as
main do not collide between projects. Binaries are content-address checked;
published source CFGs and generated manifests are local artifacts.

Safety and ranking boundaries:

- External binaries are decompiled and inspected but never executed.
- Real-malware projects are excluded unless --include-malware is explicit.
- This cohort has no Fission executable semantic wrapper, so it is a
  non-ranking structural/type/recompilation scale track.
- The authored core_c_pe cohort remains the semantic release ranking.
- dataset-lock.json pins the Hugging Face revision, license, and expected
  config counts.

## Local release measurement and CI publication

The full cohort runs on a stable local machine. GitHub Actions does not execute
the 68,194-cell matrix; it verifies and publishes the completed result:

```bash
FISSION_SOURCE=release FISSION_VERSION=vX.Y.Z \
  python runner/runner.py --corpus scale --profile decbench_scale_full \
  --run-mode local --decompilers fission,ghidra \
  --output results/scale_latest.json

python scripts/submit_scale_benchmark.py results/scale_latest.json \
  --fission-version vX.Y.Z --execute
```

The submit helper validates the complete pinned matrix before uploading a
deterministic gzip asset to the existing `benchmark-vX.Y.Z` GitHub Release. It
then dispatches `publish-unofficial-corpus.yml`. CI independently checks the
asset hash, current Fission release, dataset revision, malware exclusion,
subject count, expected cells, duplicate cells, release provenance, and minimum
clean output coverage. Only the compact non-ranking aggregate is committed to
`public/`; the raw per-function result remains a Release asset.

The Vercel dashboard reads `public/unofficial-corpus-latest.json` on the
**Unofficial Corpus** tab. Every accepted run is also retained under
`public/unofficial-corpus-history/`; these results never replace or influence
the official semantic ranking.
