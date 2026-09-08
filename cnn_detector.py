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

import torch

from baseline import BASELINE_FIELDS
from config import MODEL_PATH, WINDOW_SIZE, WINDOW_STRIDE
from model import PostureCNN


class CNNClassifier:
    """Rolling-window CNN classifier. predict() takes a z-scored sample dict."""

    def __init__(self, weights_path=MODEL_PATH, window=WINDOW_SIZE, stride=WINDOW_STRIDE):
        self._model = PostureCNN()
        self._model.load_state_dict(torch.load(weights_path, map_location="cpu"))
        self._model.eval()

        self._buffer = []
        self._window = window
        self._stride = stride
        self._since_last = 0
        self._label = 0  # neutral until the buffer fills
