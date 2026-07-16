#!/bin/bash
# Run a project motion script through the app bundle AND watch its output live.
#
# Why this wrapper exists: motion scripts must be launched via `open` so macOS
# attributes the Motion permission to AirpodsPosture.app (not the terminal —
# see packaging/launch). `open` detaches from the terminal, so output goes to
# last_run.log. This tails that log to your terminal and stops automatically
# when the run finishes.
#
# Usage:
#   scripts/run.sh calibrate.py
#   scripts/run.sh record_mac.py --label good --duration 30
#   scripts/run.sh train.py

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/AirpodsPosture.app"
LOG="$ROOT/last_run.log"
PYPROC="AirpodsPosture.app/Contents/MacOS/python3"

if [ ! -d "$APP" ]; then
    echo "AirpodsPosture.app not found — build it first: bash scripts/build_app.sh" >&2
    exit 1
fi

: > "$LOG"                          # truncate previous run's log
open "$APP" --args "$@"             # launch detached so TCC blames the app

tail -f "$LOG" &                    # stream output to this terminal
TAILPID=$!
# On exit (incl. Ctrl+C) kill BOTH the tail AND the detached app — `open`
# detaches the daemon from this shell, so Ctrl+C alone would leave it running.
trap 'kill "$TAILPID" 2>/dev/null; pkill -f "$PYPROC" 2>/dev/null' EXIT INT TERM

sleep 1
while pgrep -f "$PYPROC" >/dev/null; do sleep 0.5; done
sleep 0.3                           # let tail flush the final lines