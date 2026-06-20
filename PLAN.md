# AirPods Posture — Project Plan

Headless, privacy-first **forward-head-flexion** monitor: a Mac reads **AirPods motion directly** via Core Motion, a calibrated detector flags sustained forward head tilt ("tech neck"), and **osascript** fires a native notification. No App Store app, no per-user model training — just a one-time ~10-second calibration.

---

## What this actually measures (read this first)

AirPods give **head orientation** (pitch/roll/yaw) and acceleration — the skull, nothing below the neck. They **cannot** see your spine, shoulders, or torso, so they cannot detect "rounded shoulders" or thoracic slump directly.

What they *can* measure is **head pitch relative to your neutral** — the head-down component of poor sitting posture, commonly called "tech neck." Head pitch is a reasonable proxy for forward head flexion. (This is not a medical device and makes no clinical claims.)

So the honest product framing is:

> **Detect sustained forward head flexion relative to the user's own calibrated neutral — not "slouch" in general.**

We do not claim to detect torso posture. We detect the head-down signal that head-tracking hardware can actually support.

---

## The model ladder (build #1 always; climb only if the tier below underperforms)

| Tier | Input | Model | Needs training data? | Role |
| ---- | ----- | ----- | -------------------- | ---- |
| **1. Threshold** | raw `pitch − baseline` (degrees) | sustained-past-threshold + hold timer | No — calibration only | **Ships day one. The yardstick everything else must beat.** |
| **2. Classical** | **z-score normalized** time-domain features (mean, var, RMS, peak-to-peak) | Random Forest / SVM | Yes — one *shared* model | Light, interpretable, trains on little data |
| **3. Deep** | z-score normalized raw windows | 1D-CNN / GRU | Yes — one *shared* model | Only if Tier 2 still struggles on dynamic motion |

Two rules that keep this honest and distributable:

1. **No per-user training, ever.** Tiers 2–3 train *one shared model* shipped as frozen weights. Per-user adaptation is handled entirely by the calibration baseline (see normalization below), not by retraining. Users clone → build → calibrate → run.
2. **Every tier must beat the one below it on held-out data, or it doesn't ship.** If the threshold already works, the CNN is gold-plating. Results live in `results/`.

FFT / frequency-domain features are deferred until the time-domain features in Tier 2 prove insufficient.

### Z-score normalization (how one shared model works for everyone)

This is what makes a 5–10 person dataset generalize. The model never sees raw angles — it sees deviations from *this* user's calibrated baseline:

```
z = (x − μ) / σ      # μ, σ from the calibration window, per axis
```

Subtracting μ removes each person's neutral **offset**; dividing by σ removes their movement **scale**. The model learns *behavioral deviation*, not anatomy.

- **Floor σ** to a small per-axis minimum. If the user sits very still during calibration, σ ≈ 0 and the z-scores explode into noise.
- **σ source caveat.** The 10 s calibration σ captures *stillness noise*, not *normal working wiggle*. If z-scores run hot, compute σ from the longer `neutral` recording instead of the calibration window.
- **ML lane only.** Tier 1's threshold uses **raw degrees** (interpretable, citable "20° past neutral"). Only Tiers 2–3 z-score.
- Scope: z-scoring removes *offset and scale* bias — **not** movement-*pattern* bias (how different bodies transition into a slump). It substantially reduces anatomical bias but does not eliminate all of it.

---

## Differentiation

The distinguishing features of this approach are:

- **Per-user calibrated thresholds** (μ/σ from a 10 s calibration) rather than a fixed absolute angle.
- **Z-score normalization** so one shared model generalizes across people without per-user training.
- **LOSO cross-validation** with a reported worst-subject, validating that generalization honestly.
- **Headless Mac tool + documented API**, rather than a closed app.

Taken together, the core contribution is **calibrated, validated cross-user generalization**.

---

## End goal & strategy

The asset here is the *method*, not the app — so the strategy is to publish rigorous open-source work that engineers find on their own terms, rather than to pitch it directly.

- [ ] **Open-source developer tool** — a clean, documented Python package: import it, call one function, get a real-time head-kinematics classification stream. Not a private app.
- [ ] **Rigorous evidence** — confusion matrices, **LOSO cross-validation** results (see below), CPU cost on macOS. The key differentiator is *validated cross-user generalization*.
- [ ] **Technical write-up** — a deep-dive on the pipeline (windowing, normalization, validation, accuracy), with an accurate title and real charts. The rigor is the point; jargon and star-counts are not the goal. The write-up stands as the reference artifact regardless of reach.

The realistic payoff is a strong portfolio/research piece and credibility with serious engineering teams, rather than a direct acquisition.

### Validation: Leave-One-Subject-Out (LOSO)

This is the non-negotiable for the cross-user claim. Random cross-validation on windowed time-series is invalid here — adjacent windows are near-identical, so same-subject data leaks into train+test and produces a fake ~99% that craters in the real world.

- Training uses subjects 1–9 and testing uses only subject 10, rotating so every subject is the held-out test set once.
- Results report mean ± std across held-out subjects, including the worst subject — that worst number is the honest bias measurement.

---

## What to get done

Work through these in order. Check items off as you go.

> **Status (code vs. checklist).** The checklist tracks *tasks* (build / tune / record / test), most of which need real AirPods or recorded data. Code already written and verified offline: `mac_motion.py`, `config.py`, `baseline.py`, `calibrate.py`, `notify.py`, `detectors.py` (Tier 1), `state_machine.py`, `run_daemon.py`. Still stubs: `record_mac.py`, `eval_detectors.py`, `features.py`, `inspect_data.py`, `dataset.py`, `model.py`, `train.py`. Nothing has been run on hardware yet, so the tune/record/test items below stay unchecked.

### 1. Sensor & calibration

- [x] Build `AirpodsPosture.app` (`./scripts/build_app.sh`)
- [ ] `record_mac.py` — log motion to CSV via the bundle
- [x] `calibrate.py` + `baseline.py` — ~10 s neutral baseline → `baseline.json` (per-axis μ and σ) *(code done + unit-tested; `baseline.json` not yet generated on real AirPods)*
- [ ] Optional: `inspect_stream.py` — sample rate, live feature summary

### 2. Tier 1 — threshold detector (ships day one)

- [ ] Tune `PITCH_SLOUCH_THRESHOLD` (radians) + `SMOOTHING_WINDOW` in `config.py` against your own neutral
- [ ] `eval_detectors.py` — confirm the pitch-delta threshold separates forward-flexion from neutral
- [ ] Document its failure modes

**Known limit:** the 15 s hold timer filters *quick* glances, but a slow sip or a 5–10 s look-down still reads as flexion to a pure pitch threshold and will false-fire. That residual false-positive rate is what motivates Tiers 2–3 (the `dynamic` class), and it's measured here rather than assumed away by the timer.

### 3. Record labeled data (only needed to train Tiers 2–3)

Record **~5 min per class**, Mac-native via the bundle. One CSV per session. **Each subject calibrates first** so their μ/σ is stored alongside their CSVs.

| Label | Class           | What to record                                              |
| ----- | --------------- | ----------------------------------------------------------- |
| 0     | Neutral         | Natural upright work / typing at your real desk             |
| 1     | Forward flexion | Your real sustained head-down lean — held steadily          |
| 2     | Dynamic         | Drink, stretch, glance down 2–3 s, normal motion            |

- [ ] `neutral_01.csv`, `forward_01.csv`, `dynamic_01.csv` per subject
- [ ] **5–10 subjects** (friends) — this is what makes the shared model generalize
- [ ] Run `inspect_data.py` — confirm neutral vs forward-flexion separable after z-scoring

### 4. Tier 2 — classical model (does it beat the threshold?)

- [ ] `features.py` — extract z-score-normalized time-domain features per window
- [ ] Train a Random Forest / SVM on the **pooled** normalized features
- [ ] **LOSO cross-validation** — report mean ± std and the worst subject in `results/`
- [ ] Decision: if it doesn't clearly beat the threshold under LOSO, the threshold ships

### 5. Tier 3 — deep model (only if Tier 2 struggles on dynamic motion)

- [ ] `train.py` — 1D-CNN / GRU on z-scored raw windows → `weights/posture_model.pth`
- [ ] **LOSO** again — compare against Tier 1 and Tier 2 on held-out subjects
- [ ] Decision: ship the simplest tier that wins

### 6. Live daemon

- [ ] Test `run_daemon.py` via the bundle
- [ ] Tune `state_machine.py` — 15 s flexion hold, 60 s cooldown, neutral resets timer
- [ ] Confirm: forward flexion 15+ s → one notification; drinking / brief look-downs don't spam alerts

### 7. Wrap up

- [ ] Finish README as a documented **developer tool** (build, calibrate, run; clean API)
- [ ] Results page: threshold vs Tier 2 vs Tier 3 under **LOSO**, confusion matrices, worst-subject, CPU cost, known limits (head-only, no torso)
- [ ] Technical write-up + 2-min demo

---

## Architecture

```text
AirPods (IMU) — connected to Mac
    ↓
CMHeadphoneMotionManager (macOS 14+)
    ↓
AirpodsPosture.app → Python daemon
    ├── record_mac.py      (data collection — Tiers 2-3 only)
    ├── run_daemon.py      (live inference)
    ├── calibrate → baseline.json (μ, σ) → rolling buffer → Tier 1 threshold (or model)
    ├── state machine (hold / reset / cooldown)
    └── osascript → Notification Center
```

The default inference path is the **Tier 1 threshold**. A shared model is swapped in only if it beats Tier 1 under LOSO.

---

## Requirements

| Requirement                 | Notes                                                      |
| --------------------------- | ---------------------------------------------------------- |
| macOS **14+**               | `CMHeadphoneMotionManager` on Mac                          |
| Compatible AirPods          | Pro, 3/4, Max, etc. (head-tracking models)                 |
| AirPods on **Mac**          | Not phone, for native path                                 |
| `AirpodsPosture.app`        | Carries `NSMotionUsageDescription`; run scripts through it |
| Motion & Fitness permission | Granted on first bundle launch                             |

**For other users:** clone repo → `./scripts/build_app.sh` → **one-time ~10 s calibrate** → run daemon via bundle. **No training required** — calibration alone personalizes the detector (the model, if any, ships as frozen shared weights). (Re-calibrate if setup changes.)

---

## Calibration (one time, ~10 seconds — this is the only personalization)

**Goal:** Store *this user's* neutral head **mean (μ) and std (σ)** so the detector measures **deviation relative to them**, not an absolute angle. This is what makes "slouch is different per person" a non-problem: there is no universal threshold, only deviation from your own neutral.

1. User sits in their **natural, sustainable working posture** — *not* a forced "perfect" pose. (Calibrating to a posture you'd never hold means your normal sitting reads as slouch → all-day alert spam.)
2. Run `calibrate.py` (countdown, then ~10 s still while working normally).
3. Per-axis μ and σ (pitch, roll, yaw, gravity) saved to `baseline.json`.
4. Tier 1 uses **raw delta** (`pitch − μ`, in degrees). Tiers 2–3 use **z-scores** (`(x − μ) / σ`, with σ floored).

**Re-calibrate** when you change AirPods, chair, desk, or monitor height, or alerts feel consistently wrong.

```bash
./scripts/build_app.sh
AirpodsPosture.app/Contents/MacOS/launch calibrate.py
# then run the daemon (no training step needed)
AirpodsPosture.app/Contents/MacOS/launch run_daemon.py
```

`baseline.json` is per-user and gitignored — not shipped in the repo.

---

## Recording protocol (only needed to train Tiers 2–3)

Skip this entirely if you're just running the Tier 1 threshold. You only record data to train and LOSO-validate the shared model.

The shared model does **not** learn anyone's personal angles. After per-user z-scoring, it learns **deviation patterns** — how the statistical departure from an individual's own neutral behaves over time — pooled across all subjects. Each subject's own `baseline.json` supplies the μ/σ; the labels just mark which windows are neutral vs forward vs dynamic.

### Define classes before you record

| Class | Record as… | Not… |
| ----- | ---------- | ---- |
| **Neutral** | How you actually sit at this desk — sustainable, real typing/scrolling, normal screen glances | Forced "chin up" or a pose you'd never hold for 20 min |
| **Forward flexion** | The sustained head-down lean you'd want a nudge about — chin forward/down, **held steadily** | A quick look at the keyboard, or an exaggerated "stare at lap" pose |
| **Dynamic** | Short intentional moves: sip, stretch, pick something up, glance at phone, look down 2–3 s then sit back | Sustained flexion (that's the forward class) |

Looking down at a laptop is fine in **neutral** if that's your normal desk angle. The daemon only alerts after **15 s** of sustained flexion, so brief look-downs shouldn't spam notifications once **dynamic** is in the training set.

### Session order

1. **Calibrate** at your real desk — this is your reference zero.
2. **Neutral** — ~5 min of real work; include natural micro-movements.
3. **Forward flexion** — ~5 min; only label positions you'd actually want corrected.
4. **Dynamic** — ~5 min; deliberately mix short motions throughout.
5. Repeat on a different day or chair for hold-out files (`neutral_02.csv`, etc.).

### Sanity check

Run `inspect_data.py` on your CSVs. If neutral and forward flexion overlap in pitch deltas, your labels are too close — tighten the flexion definition or re-calibrate at your true working posture before training.

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
open -a AirpodsPosture.app --args run_daemon.py
```

Edit the permission message in `packaging/Info.plist`, then rebuild. `LSUIElement` is set — no dock icon. The `.app` exists **only** to carry the motion permission — it is not a product UI.

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
├── record_mac.py             # data collection — Tiers 2-3 only
├── baseline.py               # baseline.json μ/σ; apply_baseline + zscore
├── calibrate.py
├── config.py
├── features.py               # z-scored time-domain features (Tier 2)
├── inspect_data.py
├── dataset.py                # Tier 3 (deep)
├── model.py                  # Tier 3 (deep)
├── detectors.py              # Tier 1 threshold (the day-one product)
├── eval_detectors.py
├── train.py                  # Tier 3 (deep)
├── state_machine.py
├── run_daemon.py
├── notify.py
├── data/
├── weights/
│   └── posture_model.pth     # only used if a model beats Tier 1
├── baseline.json
└── results/
```

---

## Non-goals

- No claim of torso/spine sensing — **head flexion only**
- No per-user model training required to use the product
- No App Store app or menu bar UI (the `.app` is just a permission carrier)
- No mass distribution as a goal — a working prototype with rigorous evidence is the target
- No UDP streaming, cloud, accounts, or camera
- No claim of universal pretrained weights without per-user calibration
