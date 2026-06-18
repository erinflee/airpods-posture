# AirPods Posture — Project Plan

Headless, privacy-first posture monitoring: Mac reads **AirPods motion directly** via Core Motion, a **temporal neural net** classifies posture, and **osascript** fires native notifications. No App Store app — only a minimal `.app` bundle for motion permission.

---

## What to get done

Work through these in order. Check items off as you go.

### 1. Sensor & calibration

- [x] Build `AirpodsPosture.app` (`./scripts/build_app.sh`)
- [x] `record_mac.py` — log motion to CSV via the bundle
- [x] `calibrate.py` + `baseline.py` — 3 s upright baseline → `baseline.json`
- [ ] Optional: `inspect_stream.py` — sample rate, live feature summary

### 2. Record labeled data

Record **~5 min per class**, Mac-native via the bundle. One CSV per session.

| Label | Class        | What to record                                      |
| ----- | ------------ | --------------------------------------------------- |
| 0     | Good posture | Natural upright work / typing                       |
| 1     | Slouch       | Your real slump — not exaggerated "look at lap"     |
| 2     | Dynamic      | Drink, stretch, look down briefly, normal motion  |

- [ ] `good_01.csv`, `slouch_01.csv`, `dynamic_01.csv`
- [ ] Second session per class on a different day or chair (hold-out eval)
- [ ] Run `inspect_data.py` — confirm good vs slouch separable in plots

### 3. Baselines & model

- [ ] Tune thresholds in `config.py`
- [ ] Run `eval_baselines.py` — pitch threshold + smoothed threshold baselines
- [ ] Run `train.py` — 1D-CNN, export to `weights/posture_model.pth`
- [ ] Compare CNN vs baselines on hold-out session; note results in `results/`

### 4. Live daemon

- [ ] Test `run_daemon.py` via the bundle
- [ ] Tune `state_machine.py` — 15 s slouch hold, 60 s cooldown, good posture resets timer
- [ ] Confirm: slouch 15+ s → one notification; drinking doesn't spam alerts

### 5. Wrap up

- [ ] Finish README (build, calibrate, record, train, run)
- [ ] One-page results: baselines vs CNN, false positives, known limits
- [ ] Optional: 2 min demo video

---

## Architecture

```text
AirPods (IMU) — connected to Mac
    ↓
CMHeadphoneMotionManager (macOS 14+)
    ↓
AirpodsPosture.app → Python daemon
    ├── record_mac.py      (data collection)
    ├── run_daemon.py      (live inference)
    ├── calibrate → rolling buffer → model
    ├── state machine (hold / reset / cooldown)
    └── osascript → Notification Center
```

---

## Requirements

| Requirement                 | Notes                                                      |
| --------------------------- | ---------------------------------------------------------- |
| macOS **14+**               | `CMHeadphoneMotionManager` on Mac                          |
| Compatible AirPods          | Pro, 3/4, Max, etc. (head-tracking models)                 |
| AirPods on **Mac**          | Not phone, for native path                                 |
| `AirpodsPosture.app`        | Carries `NSMotionUsageDescription`; run scripts through it |
| Motion & Fitness permission | Granted on first bundle launch                             |

**For other users:** clone repo → `./scripts/build_app.sh` → **one-time 3 s calibrate** → run daemon via bundle. Pretrained weights are a starting point; **upright baseline is required once per user** (re-calibrate if setup changes).

---

## Calibration (default — one time, ~3 seconds)

**Goal:** Store *this user's* upright posture so all features are relative, not absolute.

1. User sits in ideal desk posture.
2. Run `calibrate.py` (3 s countdown, then 3 s still).
3. Mean pitch, roll, yaw, and gravity saved to `baseline.json`.
4. Training and inference use **delta from baseline** (e.g. `pitch - baseline.pitch`).

**Re-calibrate** when you change AirPods, chair, desk, or monitor height, or alerts feel consistently wrong.

```bash
./scripts/build_app.sh
AirpodsPosture.app/Contents/MacOS/launch calibrate.py
# then record or run daemon
AirpodsPosture.app/Contents/MacOS/launch record_mac.py --label good
```

`baseline.json` is per-user and gitignored — not shipped in the repo.

---

## Motion permission (`NSMotionUsageDescription`)

macOS kills bare `python3 script.py` when it reads headphone motion. You need an `Info.plist` with a privacy string inside a `.app` bundle.

```text
packaging/Info.plist     # NSMotionUsageDescription + bundle metadata
packaging/launch         # runs Python scripts from project root
scripts/build_app.sh     # builds AirpodsPosture.app
```

```bash
./scripts/build_app.sh
open -a AirpodsPosture.app --args record_mac.py
# later:
open -a AirpodsPosture.app --args run_daemon.py
```

Edit the permission message in `packaging/Info.plist`, then rebuild. `LSUIElement` is set — no dock icon.

---

## Repo layout

```text
airpods-posture/
├── PLAN.md
├── README.md
├── requirements.txt
├── AirpodsPosture.app/       # built by scripts/build_app.sh (gitignore)
├── packaging/
│   ├── Info.plist
│   └── launch
├── scripts/
│   └── build_app.sh
├── mac_motion.py
├── record_mac.py
├── baseline.py
├── calibrate.py
├── config.py
├── features.py
├── inspect_data.py
├── dataset.py
├── model.py
├── baselines.py
├── eval_baselines.py
├── train.py
├── state_machine.py
├── run_daemon.py
├── notify.py
├── data/
├── weights/
│   └── posture_model.pth
├── baseline.json
└── results/
```

---

## Non-goals

- No App Store app or menu bar UI
- No UDP streaming
- No cloud, accounts, or camera
- No claim of universal pretrained weights without per-user calibration
