#!/bin/bash
# Endless demo loop for a macOS Devbox's screen: cycle through the knockout conditions, each playing
# Doom in closed loop with the real game window visible. Started by mac_start_loop.mjs.
# Plain bash 3.2 (macOS default): no associative arrays.
# Usage: mac_loop.sh <fly-home> <repo> <game-seed> [resolution]
FLY=$1; REPO=$2; SEED=${3:-41027}; RES=${4:-1600x1200}
i=0
while true; do
  for name in intact dnp20-off dnpe017-off mevp9-off; do
    case $name in
      intact)      neurons=""; id=0 ;;
      dnp20-off)   neurons="10059,10162" ;;
      dnpe017-off) neurons="10527,555871" ;;
      mevp9-off)   neurons="12764,12356" ;;
    esac
    i=$((i + 1)); [ "$name" = intact ] || id=$i
    "$FLY/venv/bin/python" "$REPO/run_candidate.py" --candidate-id "$id" --neurons "$neurons" --game-seed "$SEED" \
      --max-tics 2100 --doomfly "$FLY/doomfly" --show-window --realtime --resolution "$RES" --hold 4 --out "$HOME/fly-out/runs" \
      > "$HOME/fly-out/loop-$name.log" 2>&1
  done
done
