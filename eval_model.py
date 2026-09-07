"""
Evaluate the trained CNN against the Tier 1 threshold on the held-out session.

  - load the validation split from build_datasets() (same split train.py used)
  - CNN: load weights/posture_model.pth, predict every window in one pass
  - print a 3x3 confusion matrix with per-class recall
  - collapse to forward vs not-forward (what the alert timer consumes)
  - Tier 1 on the same windows: undo the pitch z-score, mean over the window,
    apply PITCH_SLOUCH_THRESHOLD
"""

import sys
import numpy as np
import torch

from baseline import BASELINE_FIELDS, SIGMA_FLOOR, load_baseline
from config import CLASS_PREFIX_TO_ID, DATA_DIR, MODEL_PATH, PITCH_SLOUCH_THRESHOLD
from dataset import build_datasets
from model import PostureCNN

CLASS_NAMES = list(CLASS_PREFIX_TO_ID)          # ["neutral", "forward", "dynamic"]
FORWARD = CLASS_PREFIX_TO_ID["forward"]
PITCH_CHANNEL = BASELINE_FIELDS.index("pitch")  # channel order matches rows_to_windows


def cnn_predictions(val):
    """Class id per window from the saved weights. One forward pass, no grad."""
    model = PostureCNN()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()
    with torch.no_grad():
        return model(val.x).argmax(dim=1).numpy()


def tier1_predictions(val, session):
    """Tier 1 label per window: mean raw pitch delta past the threshold.

    Windows hold z-scored pitch, so multiply by the session's sigma (floored
    the same way zscore() floors it) to get radians back.
    """
    baseline = load_baseline(DATA_DIR / f"baseline_{session:02d}.json")
    sigma = max(baseline["std"]["pitch"], SIGMA_FLOOR)
    pitch_delta = val.x[:, PITCH_CHANNEL, :].numpy() * sigma
    forward = pitch_delta.mean(axis=1) < PITCH_SLOUCH_THRESHOLD
    return np.where(forward, FORWARD, CLASS_PREFIX_TO_ID["neutral"])


def confusion_matrix(actual_labels, predicted_labels, n_classes):
    """counts[actual, predicted] = number of windows with that (actual, predicted) pair.

    Rows are the true class, columns are what the model said. The diagonal is
    correct predictions; everything off the diagonal is a specific kind of mistake.
    """
    counts = np.zeros((n_classes, n_classes), dtype=int)
    for actual, predicted in zip(actual_labels, predicted_labels):
        counts[actual, predicted] += 1
    return counts


def print_confusion(counts):
    """Print counts as a table: one row per actual class, one column per predicted class."""
    column_width = 9
    header = " " * column_width + "".join(f"{name:>{column_width}s}" for name in CLASS_NAMES) + "   recall"
    print(header)
    for actual, actual_name in enumerate(CLASS_NAMES):
        row_counts = counts[actual]
        row_text = "".join(f"{count:{column_width}d}" for count in row_counts)
        n_actual = row_counts.sum()
        recall = counts[actual, actual] / n_actual if n_actual else 0.0
        print(f"{actual_name:{column_width}s}{row_text}   {recall:.3f}")

