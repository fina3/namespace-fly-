#!/bin/bash
# Endless demo loop for a macOS Devbox's screen (started by mac_wall.mjs / mac_start_loop.mjs).
# One python process keeps the brain loaded and cycles the knockout conditions; the window never closes.
# Usage: mac_loop.sh <fly-home> <repo> <game-seed> [resolution]
FLY=$1; REPO=$2; SEED=${3:-41027}; RES=${4:-1600x1200}
# Leave cores for the screen-sharing service the Live page reads from: the brain uses one thread per
# step anyway, and numpy/numba threads only add load on a 6-core box.
export NUMBA_NUM_THREADS=2 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
while true; do
  "$FLY/venv/bin/python" "$REPO/mac_cycle.py" --doomfly "$FLY/doomfly" --seed "$SEED" --resolution "$RES" >> "$HOME/fly-out/cycle.log" 2>&1
  sleep 1   # only reached if the process dies; restart it
done
