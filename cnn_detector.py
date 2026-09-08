"""
Tier 3 live detector: the trained 1D CNN on a rolling window of z-scored samples.

Same job as pitch_detector.SmoothedPitchClassifier (one sample in, one label
out) but it looks at the last WINDOW_SIZE samples instead of one pitch value.
Loads weights/posture_model.pth once. Runs the model every WINDOW_STRIDE
samples (~0.5 s) and repeats the last label in between, so the monitor loop
stays cheap.

Opt-in via `run_monitor.py --detector cnn`. Validated on one held-out session
from one subject, see results/RESULTS.md.
"""
