#!/bin/bash
# Run "<stimulus> <arm>" jobs from a file, $PAR at a time (each run is ~0.5 GB, 1 core).
# Results land in /workspaces/results/<stimulus>/<arm>/. Exits non-zero if any job failed.
set -uo pipefail
JOBS=$1; PAR=${PAR:-12}; export SECS=${SECS:-120}
cd /workspaces/namespace-fly
mkdir -p /workspaces/logs
run() {
  local stim=$1 arm=$2 seed sweep work=/workspaces/work/$1-$2
  read -r seed sweep < <(python3 -c "import json;s=json.load(open('stimuli.json'))['$stim'];print(s['seed'],s['sweep'])")
  # ViZDoom writes ./_vizdoom in its cwd; concurrent runs sharing a cwd collide on it.
  mkdir -p "$work"
  if (cd "$work" && /workspaces/venv/bin/python /workspaces/namespace-fly/run_condition.py --condition "$arm" --tag "$arm" --seed "$seed" --sweep "$sweep" \
       --seconds "$SECS" --warmup 1 --out "/workspaces/results/$stim" > "/workspaces/logs/$stim-$arm.log" 2>&1)
  then echo "ok $stim/$arm"; else echo "FAIL $stim/$arm"; fi
}
export -f run
SUMMARY=/workspaces/logs/batch-$(basename "$JOBS").txt
xargs -P "$PAR" -L 1 bash -c 'run "$@"' _ < "$JOBS" > "$SUMMARY"
echo "$(grep -c '^ok' "$SUMMARY") ok, $(grep -c '^FAIL' "$SUMMARY") failed"
! grep -q '^FAIL' "$SUMMARY"
