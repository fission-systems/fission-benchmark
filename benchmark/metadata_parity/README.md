# Program metadata parity

This diagnostic stage compares Fission's typed `ProgramSnapshot` with Ghidra's
program database for the same binary. It runs once per binary, not once per
function.

Strict status requires equality of binary identity, memory block ranges and
permissions, function entries, comparable loader-symbol addresses, and
relocation addresses. Ghidra `default`/`analysis` labels are analysis-generated
facts, so they are reported through raw/generated-symbol metrics but are not
mixed into loader-symbol recall. The individual Jaccard rates remain available
for triage. This stage is deliberately non-publishable until the schemas and
provenance filters stabilize.

```bash
export FISSION_HOST_PORT=8007
python -m benchmark.metadata_parity.run --corpus dev --limit 1
```
