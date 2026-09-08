# AirPods Posture

A headless macOS tool that reads AirPods head motion and nudges you when you
have been leaning your head forward for too long. No app window, no cloud, no
camera: a 10 second calibration, then a small banner and a sound when you
slouch.

It measures **forward head flexion relative to your own calibrated neutral**.
AirPods sit on your skull, so this cannot see your shoulders or spine. It is
not a medical device.

Results, including a trained model compared against the shipped threshold on a
held-out session, are in [results/RESULTS.md](results/RESULTS.md).

## Requirements

- macOS 14 or later. `CMHeadphoneMotionManager` is not available on Mac before that.
- AirPods with head tracking (Pro, 3rd gen or later, Max), connected to the Mac.
- A Python 3 with `pyobjc-framework-CoreMotion` installed. The build script
  looks for one on your PATH and at `/opt/anaconda3/bin/python3`.

```bash
pip install -r requirements.txt
```

`numpy`, `matplotlib`, and `torch` are only needed for the data and training
scripts. The live monitor needs `pyobjc` alone.

## Why there is an `.app`

macOS only lets a process read headphone motion if its bundle declares
`NSMotionUsageDescription`. Bare `python3 script.py` gets killed. So
`scripts/build_app.sh` copies your Python interpreter into
`AirpodsPosture.app`, gives it an `Info.plist` with that key, and ad-hoc signs
the bundle. The `.app` has no UI. It exists only to carry the permission.

Every script that touches motion has to be launched through it. `scripts/run.sh`
does that and streams the output back to your terminal.

## Quick start

```bash
./scripts/build_app.sh             # once
scripts/run.sh calibrate.py        # once, ~15 s, sit how you normally sit
scripts/run.sh run_monitor.py      # leave running while you work, Ctrl+C to stop
```

The first launch prompts for Motion & Fitness permission. Grant it and re-run.

### Calibration

`calibrate.py` records 10 seconds of your natural working posture and saves the
per-axis mean and standard deviation of pitch, roll, yaw, and gravity to
`baseline.json`. Everything downstream measures deviation from that. Sit how
you actually sit, not a forced upright pose, or your normal posture will read
as slouching all day.

Re-calibrate if you change chair, desk, monitor height, or AirPods.

### What the monitor does

```
AirPods -> CMHeadphoneMotionManager (~47 Hz)
        -> pitch - calibrated neutral pitch
        -> forward if more than 0.10 rad (5.7 degrees) chin-down
        -> state machine: 15 s held -> one alert, neutral resets, 60 s cooldown
        -> self-drawn banner + afplay sound
```

The alert is a fake banner drawn with AppKit rather than a real notification,
because firing a Notification Center banner kills the AirPods motion stream.
`keepalive_test.py` reproduces that and checks which alert paths survive.

Thresholds and timings live in `config.py`.

## Using it as a library

`airpods_motion.HeadphoneMotionReader` is the only piece that talks to the
hardware. It hands you one dict per sample:

```python
from airpods_motion import HeadphoneMotionReader

reader = HeadphoneMotionReader()
if not reader.available():
    raise SystemExit("connect AirPods")

def on_sample(sample):
    print(sample["pitch"], sample["roll"], sample["yaw"])   # radians
    # also accelerationX/Y/Z, rotationRateX/Y/Z, gravityX/Y/Z, time_ns

reader.start(on_sample)
reader.run_until_stopped()   # blocks; call reader.stop() from the callback
```

`baseline.apply_baseline(sample, baseline)` gives raw deltas from neutral in
radians. `baseline.zscore(sample, baseline)` gives per-axis z-scores for the
model path. `pitch_detector.SmoothedPitchClassifier` and
`alert_timing.PostureStateMachine` are the two pieces `run_monitor.py` wires
together, and both are plain Python with no AppKit dependency.

## Recording data and training

Only needed if you want to retrain or evaluate the model. The monitor ships
with the threshold detector and needs none of this.

```bash
scripts/run.sh calibrate.py --output data/baseline_01.json
scripts/run.sh record_mac.py --label neutral --duration 300
scripts/run.sh record_mac.py --label forward --duration 300
scripts/run.sh record_mac.py --label dynamic --duration 300
```

Files are numbered by session (`neutral_01.csv`, `forward_01.csv`, ...), and
each session's `baseline_NN.json` is used to normalize that session's
recordings. Classes:

| Label | Record |
| --- | --- |
| neutral | How you actually sit and type at your desk |
| forward | The sustained head-down lean you would want a nudge about |
| dynamic | Sips, stretches, 2 to 3 s glances down, normal movement |

Then, using the bundle's interpreter so numpy and torch are available:

```bash
PY=AirpodsPosture.app/Contents/MacOS/python3
$PY inspect_data.py --plot     # per-file stats and pitch/roll plots into results/
$PY eval_detectors.py          # threshold accuracy per file
$PY train.py                   # 1D CNN, trains on all sessions but the last
$PY eval_model.py              # CNN vs threshold on the held-out session
```

Training splits by session, never randomly. Adjacent windows of a time series
are near-duplicates, so a random split leaks test data into training.

## Layout

```
airpods_motion.py     Core Motion reader, one dict per sample
config.py             thresholds, timings, paths, window sizes
baseline.py           baseline.json read/write, apply_baseline, zscore
calibrate.py          10 s neutral calibration -> baseline.json
record_mac.py         labeled CSV recording
pitch_detector.py     Tier 1 threshold detector (+ majority vote)
alert_timing.py       hold / reset / cooldown state machine
alert_banner.py       self-drawn AppKit banner
run_monitor.py        the live monitor
keepalive_test.py     does an alert kill the motion stream?
inspect_data.py       stats and plots per recording
eval_detectors.py     threshold accuracy on recorded CSVs
shared_features.py    CSV -> z-scored sliding windows
dataset.py            PyTorch dataset, session-based split
model.py              PostureCNN, two Conv1d layers, 11k params
train.py              training loop, saves best epoch
eval_model.py         CNN vs threshold, confusion matrix
packaging/            Info.plist and launcher for the .app
scripts/              build_app.sh, run.sh, stop.sh
data/                 recordings and per-session baselines (gitignored)
weights/              posture_model.pth
results/              RESULTS.md and plots
```

## Limits

- Head only. Forward head flexion, not posture in general.
- Validated on one person across two sessions. Cross-user generalization is
  the stated goal in `PLAN.md` and has not been tested.
- The shipped detector is a fixed threshold on calibrated pitch. The CNN beats
  it on the held-out session but is not wired into the monitor yet.
- macOS only, and only with AirPods connected to the Mac rather than a phone.
