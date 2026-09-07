"""
Evaluate the trained CNN against the Tier 1 threshold on the held-out session.

  - load the validation split from build_datasets() (same split train.py used)
  - CNN: load weights/posture_model.pth, predict every window in one pass
  - print a 3x3 confusion matrix with per-class recall
  - collapse to forward vs not-forward (what the alert timer consumes)
  - Tier 1 on the same windows: undo the pitch z-score, mean over the window,
    apply PITCH_SLOUCH_THRESHOLD
"""
