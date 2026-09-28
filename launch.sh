#!/bin/bash
# Head agent: one Namespace Devbox per arm, all in parallel, then compare locally.
#   ./launch.sh [seconds]      (default 120 s of game/neural time per arm)
set -euo pipefail
SECONDS_SIM=${1:-120}
ARMS=(control dnp20-off dnpe017-off both-off)
cd "$(dirname "$0")"

arm() {
  local c=$1 box=fly-$1
  devbox list 2>/dev/null | grep -q " $box " || \
    devbox create --name "$box" --image builtin:base --size l --no_checkout \
      --purpose "namespace-fly: DOOMFLY suppression arm $c" >/dev/null
  for f in setup.sh run_condition.py conditions.json; do
    devbox upload "$box" "$f" "/workspaces/namespace-fly/$f" --mkdir >/dev/null
  done
  devbox exec "$box" -- bash -lc "bash /workspaces/namespace-fly/setup.sh > /workspaces/setup.log 2>&1" \
    || { echo "$c: setup failed (see /workspaces/setup.log on $box)"; return 1; }
  devbox exec "$box" -- bash -lc "cd /workspaces/namespace-fly && /workspaces/venv/bin/python run_condition.py \
    --condition $c --seconds $SECONDS_SIM --warmup 1 --out /workspaces/results > /workspaces/run.log 2>&1" \
    || { echo "$c: run failed (see /workspaces/run.log on $box)"; return 1; }
  mkdir -p "results/$c"
  for f in summary.json ticks.csv celltype_spikes.json neuron_counts.npz; do
    devbox download "$box" "/workspaces/results/$c/$f" "results/$c/$f" >/dev/null
  done
  devbox download "$box" /workspaces/run.log "results/$c/run.log" >/dev/null
  echo "$c: done"
}

for c in "${ARMS[@]}"; do arm "$c" & done
wait
python3 compare.py > /dev/null && echo "wrote results/comparison.md"
echo "Tear down when finished: for c in ${ARMS[*]}; do devbox expire fly-\$c --force; done"
