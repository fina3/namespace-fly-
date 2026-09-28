#!/bin/bash
# Head agent. One Namespace Devbox per primary arm; every arm runs on every stimulus.
#   ./launch.sh [seconds]      (default 120 s of game/neural time per run)
#
# Phase 1  each box sets up and runs its own arm on s1, s2, s3. The control box also runs
#          the follow-up (MeVP9 upstream knockout) and the blank/frozen vision controls.
# Phase 2  sham pairs are selected from the s1 control run, then spread across all boxes.
# Phase 3  results are pulled back and compared; compare.py rejects any frame-hash mismatch.
set -uo pipefail  # no -e: every phase checks and reports its own failures
export SECS=${1:-120}
ARMS=(control dnp20-off dnpe017-off both-off)
CONTROL_BOX_EXTRAS=(mevp9-off blank-vision frozen-vision)
FILES=(setup.sh run_condition.py run_batch.sh select_shams.py conditions.json stimuli.json)
cd "$(dirname "$0")"
STIMS=$(python3 -c "import json;print(' '.join(json.load(open('stimuli.json'))))")
WORK=$(mktemp -d)
quiet() { grep -v -i -e 'new version' -e 'devbox update' -e '^\s*$' || true; }

phase1() {
  local arm=$1 box=fly-$1 s x
  if ! devbox list 2>/dev/null > "$WORK/list-$arm.txt" || ! grep -q " $box " "$WORK/list-$arm.txt"; then
    devbox create --name "$box" --image builtin:base --size l --no_checkout \
      --purpose "namespace-fly: DOOMFLY knockout arm $arm" >/dev/null 2>&1 || { echo "FAIL $arm: create"; return 1; }
  fi
  for f in "${FILES[@]}"; do
    devbox upload "$box" "$f" "/workspaces/namespace-fly/$f" --mkdir >/dev/null 2>&1 || { echo "FAIL $arm: upload $f"; return 1; }
  done
  devbox exec "$box" -- bash -lc "rm -rf /workspaces/results /workspaces/logs /workspaces/work /workspaces/namespace-fly/shams.json; \
    bash /workspaces/namespace-fly/setup.sh > /workspaces/setup.log 2>&1" >/dev/null 2>&1 \
    || { echo "FAIL $arm: setup (see /workspaces/setup.log on $box)"; return 1; }
  for s in $STIMS; do
    echo "$s $arm"
    if [ "$arm" = control ]; then for x in "${CONTROL_BOX_EXTRAS[@]}"; do echo "$s $x"; done; fi
  done > "$WORK/jobs-$arm.txt"
  devbox upload "$box" "$WORK/jobs-$arm.txt" /workspaces/jobs-main.txt >/dev/null 2>&1
  local out; out=$(devbox exec "$box" -- bash -lc "SECS=$SECS bash /workspaces/namespace-fly/run_batch.sh /workspaces/jobs-main.txt" 2>&1)
  local status=$?
  echo "$box main: $(echo "$out" | quiet | tail -1)"
  return $status
}

phase2() {  # $1 = box index; takes every Nth sham x stimulus job
  local box=fly-${ARMS[$1]}
  python3 - "$1" "${#ARMS[@]}" > "$WORK/jobs-sham-$1.txt" <<'PY'
import json, sys
k, n = int(sys.argv[1]), int(sys.argv[2])
jobs = [f'{s} {a}' for a in json.load(open('shams.json')) for s in json.load(open('stimuli.json'))]
print('\n'.join(jobs[k::n]))
PY
  devbox upload "$box" shams.json /workspaces/namespace-fly/shams.json >/dev/null 2>&1 &&
  devbox upload "$box" "$WORK/jobs-sham-$1.txt" /workspaces/jobs-sham.txt >/dev/null 2>&1 || { echo "FAIL $box: sham upload"; return 1; }
  local out; out=$(devbox exec "$box" -- bash -lc "SECS=$SECS bash /workspaces/namespace-fly/run_batch.sh /workspaces/jobs-sham.txt" 2>&1)
  local status=$?
  echo "$box shams: $(echo "$out" | quiet | tail -1)"
  return $status
}

pull() {
  local box=fly-$1
  devbox exec "$box" -- bash -lc "cd /workspaces && tar -czf results.tgz \$(ls -d results/s* 2>/dev/null)" >/dev/null 2>&1 &&
  devbox download "$box" /workspaces/results.tgz "$WORK/results-$1.tgz" >/dev/null 2>&1 &&
  tar -xzf "$WORK/results-$1.tgz" -C . || { echo "FAIL $box: pull"; return 1; }
}

# Run a phase on every box in parallel; stop if any box failed.
each() {
  local fn=$1; shift; local pids=() failed=0 p
  for x in "$@"; do "$fn" "$x" & pids+=($!); done
  for p in "${pids[@]}"; do wait "$p" || failed=1; done
  [ $failed = 0 ] || { echo "ABORT: $fn failed on at least one box"; exit 1; }
}

each phase1 "${ARMS[@]}"

devbox exec fly-control -- bash -lc 'cd /workspaces/namespace-fly && /workspaces/venv/bin/python select_shams.py \
  --control-counts /workspaces/results/s1/control/neuron_counts.npz' 2>&1 | quiet
devbox download fly-control /workspaces/namespace-fly/shams.json shams.json >/dev/null 2>&1 &&
devbox download fly-control /workspaces/namespace-fly/neuron_types.npz neuron_types.npz >/dev/null 2>&1 \
  || { echo "ABORT: sham selection"; exit 1; }
each phase2 $(seq 0 $((${#ARMS[@]} - 1)))

rm -rf results/s[0-9]*
each pull "${ARMS[@]}"
python3 compare.py > /dev/null && echo "wrote results/comparison.md" || { echo "ABORT: compare.py failed"; exit 1; }
echo "Tear down when finished: for a in ${ARMS[*]}; do devbox expire fly-\$a --force; done"
