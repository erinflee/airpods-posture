#!/bin/bash
# Force-stop any running AirpodsPosture monitor + its run.sh wrapper.
# Use this if a run got suspended (Ctrl+Z) or detached and is still holding
# the AirPods motion manager (symptom: `open` fails with error -600).

pkill -f "AirpodsPosture.app/Contents/MacOS/python3" 2>/dev/null
pkill -f "run.sh run_monitor" 2>/dev/null
pkill -f "tail -f.*last_run.log" 2>/dev/null
echo "stopped any running AirpodsPosture monitor"