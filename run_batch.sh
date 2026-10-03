#!/bin/bash
# Run "<stimulus> <arm>" jobs from a file, $PAR at a time (each run is ~0.5 GB, 1 core).
# Results land in /workspaces/results/<stimulus>/<arm>/. Exits non-zero if any job failed.
set -uo pipefail
JOBS=$1; PAR=${PAR:-12}; export SECS=${SECS:-120}
# Where things live. Defaults match setup.sh; the pre-baked image sets FLY_* in the environment.
export DOOMFLY=${FLY_DOOMFLY:-/workspaces/doomfly} PY=${FLY_VENV:-/workspaces/venv}/bin/python
export REPO=${FLY_REPO:-/workspaces/namespace-fly} OUT=${FLY_OUT:-/workspaces}
cd "$REPO"
mkdir -p "$OUT/logs"
run() {
  local stim=$1 arm=$2 seed sweep work=$OUT/work/$1-$2
  read -r seed sweep < <("$PY" -c "import json;s=json.load(open('stimuli.json'))['$stim'];print(s['seed'],s['sweep'])")
  # ViZDoom writes ./_vizdoom in its cwd; concurrent runs sharing a cwd collide on it.
  mkdir -p "$work"
  if (cd "$work" && "$PY" "$REPO/run_condition.py" --condition "$arm" --tag "$arm" --seed "$seed" --sweep "$sweep" --doomfly "$DOOMFLY" \
       --seconds "$SECS" --warmup 1 --out "$OUT/results/$stim" > "$OUT/logs/$stim-$arm.log" 2>&1)
  then echo "ok $stim/$arm"; else echo "FAIL $stim/$arm"; fi
}
export -f run
SUMMARY=$OUT/logs/batch-$(basename "$JOBS").txt
xargs -P "$PAR" -L 1 bash -c 'run "$@"' _ < "$JOBS" > "$SUMMARY"
echo "$(grep -c '^ok' "$SUMMARY") ok, $(grep -c '^FAIL' "$SUMMARY") failed"
! grep -q '^FAIL' "$SUMMARY"
