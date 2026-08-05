#!/usr/bin/env bash
# full_matrix fan-out: run profile slices then merge envelopes.
#
# Usage:
#   ORACLE_ENDPOINT=http://localhost:8010 \
#     ./scripts/run_matrix_fanout.sh dev results/dev_latest.json
#
# Env:
#   RUN_MODE            smoke|local|official (default: smoke)
#   FANOUT_PROFILES     space-separated profiles (default: core set)
#   CORE_DECOMPILERS    decompilers for core_c_pe (default: fission,ghidra)
#   SLICE_DECOMPILERS   decompilers for lang_*/multi_isa (default: fission,ghidra)
#   FANOUT_PARALLEL     max concurrent slice jobs (default: 2). Slices share the
#                       same decompiler containers; 2 keeps Ghidra/Fission busy
#                       without thrashing a single runner.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CORPUS="${1:-dev}"
OUTPUT="${2:-results/${CORPUS}_latest.json}"
RUN_MODE="${RUN_MODE:-smoke}"
FANOUT_PROFILES="${FANOUT_PROFILES:-core_c_pe lang_cpp lang_rust lang_go multi_isa}"
CORE_DECOMPILERS="${CORE_DECOMPILERS:-fission,ghidra}"
SLICE_DECOMPILERS="${SLICE_DECOMPILERS:-fission,ghidra}"
FANOUT_PARALLEL="${FANOUT_PARALLEL:-2}"
SLICE_DIR="results/slices"
mkdir -p "$SLICE_DIR"

echo "Fan-out corpus=$CORPUS mode=$RUN_MODE profiles=[$FANOUT_PROFILES]"
echo "  core decompilers:  $CORE_DECOMPILERS"
echo "  slice decompilers: $SLICE_DECOMPILERS"
echo "  parallel slots:    $FANOUT_PARALLEL"

run_one() {
  local profile="$1"
  local out="$2"
  local decs="$3"
  local mode="$RUN_MODE"
  # Only the immutable core cohort is a publishable official measurement.
  # Language/ISA slices remain explicit diagnostics in the merged envelope.
  if [ "$mode" = "official" ] && [ "$profile" != "core_c_pe" ]; then
    mode="local"
  fi
  echo "==> profile=$profile mode=$mode decompilers=$decs → $out"
  ORACLE_ENDPOINT="${ORACLE_ENDPOINT:-}" \
    python runner/runner.py \
      --corpus "$CORPUS" \
      --profile "$profile" \
      --decompilers "$decs" \
      --run-mode "$mode" \
      --output "$out"
  echo "OK profile=$profile"
}

# Bounded parallel pool via background jobs + wait -n (bash 5+).
pids=()
labels=()
outputs=()
fail=0

for profile in $FANOUT_PROFILES; do
  out="$SLICE_DIR/${CORPUS}_${profile}.json"
  if [ "$profile" = "core_c_pe" ]; then
    decs="$CORE_DECOMPILERS"
  else
    decs="$SLICE_DECOMPILERS"
  fi

  # Wait until a slot is free.
  while [ "${#pids[@]}" -ge "$FANOUT_PARALLEL" ]; do
    if wait -n 2>/dev/null; then
      :
    else
      # wait -n failed (job failed) or unavailable — fall back to wait-any.
      if ! wait -n; then
        fail=1
      fi
    fi
    # Prune finished pids.
    alive=()
    for pid in "${pids[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then
        alive+=("$pid")
      fi
    done
    pids=("${alive[@]+"${alive[@]}"}")
  done

  (
    run_one "$profile" "$out" "$decs"
  ) &
  pids+=("$!")
  labels+=("$profile")
  outputs+=("$out")
done

# Drain remaining.
for pid in "${pids[@]+"${pids[@]}"}"; do
  if ! wait "$pid"; then
    fail=1
  fi
done
if [ "$fail" -ne 0 ]; then
  echo "FAIL: one or more fan-out slices failed" >&2
  exit 1
fi

# Always keep a pure core slice for publication ranking.
if [ -f "$SLICE_DIR/${CORPUS}_core_c_pe.json" ]; then
  cp "$SLICE_DIR/${CORPUS}_core_c_pe.json" "results/${CORPUS}_core_c_pe.json"
  echo "Wrote results/${CORPUS}_core_c_pe.json (publication ranking slice)"
fi

inputs=()
label_args=()
for i in "${!labels[@]}"; do
  inputs+=("${outputs[$i]}")
  label_args+=(--label "${labels[$i]}")
done

python scripts/merge_envelopes.py "${inputs[@]}" \
  "${label_args[@]}" \
  -o "$OUTPUT"
echo "Merged fan-out → $OUTPUT"
