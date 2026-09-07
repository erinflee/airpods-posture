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


