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


    def predict(self, zsample):
        """Class id (0 neutral / 1 forward / 2 dynamic) for the latest sample."""
        self._buffer.append([zsample[field] for field in BASELINE_FIELDS])
        self._buffer = self._buffer[-self._window:]  # keep only the last WINDOW_SIZE samples
        self._since_last += 1

        if len(self._buffer) < self._window:
            return self._label
        if self._since_last < self._stride:
            return self._label

        self._since_last = 0
        # (time, channels) -> (1, channels, time), same layout as rows_to_windows
        x = torch.tensor(self._buffer, dtype=torch.float32).T.unsqueeze(0)
        with torch.no_grad():
            self._label = int(self._model(x).argmax(dim=1))
        return self._label

   