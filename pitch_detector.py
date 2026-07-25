"""
Rule-based posture detectors (Tier 1).

  - pitch_only_label       Baseline A: raw pitch threshold
  - SmoothedPitchClassifier Baseline B: same, majority-voted over last N labels
"""

from config import PITCH_SLOUCH_THRESHOLD, SMOOTHING_WINDOW


def pitch_only_label(pitch_delta):
    """1 (forward) if pitch_delta is past the threshold, else 0.

    Threshold is negative (chin-down drives pitch below neutral). pitch_delta is
    pitch - baseline mean, in radians.
    """
    if pitch_delta < PITCH_SLOUCH_THRESHOLD:
        return 1
    return 0


class SmoothedPitchClassifier:
    """Baseline B: pitch threshold, majority-voted over the last N labels.

    Stops a single noisy sample near the threshold from flipping the output.
    N defaults to SMOOTHING_WINDOW.
    """

    def __init__(self, window=SMOOTHING_WINDOW):
        self._window = window
        self._buffer = []

    def predict(self, pitch_delta):
        """Majority label (0/1) over the last N samples."""
        label = pitch_only_label(pitch_delta)
        self._buffer.append(label)
        self._buffer = self._buffer[-self._window:]

        if sum(self._buffer) > len(self._buffer) / 2:
            return 1
        return 0

    def reset(self):
        """Clear the buffer between files/sessions."""
        self._buffer = []

