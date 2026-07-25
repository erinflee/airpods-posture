"""
Rule-based posture detectors (Tier 1, before the ML tiers).

  - pitch_only_label —> Baseline A: raw pitch threshold
  - SmoothedPitchClassifier —> Baseline B: same, majority-voted over last N labels
"""

from config import PITCH_SLOUCH_THRESHOLD, SMOOTHING_WINDOW


def pitch_only_label(pitch_delta):
    """Label one sample: 1 (forward) if pitch_delta is past the threshold, else 0.

    Threshold is negative because chin-down flexion drives pitch below neutral.
    pitch_delta is pitch - baseline mean, in radians (from apply_baseline).
    """
    if pitch_delta < PITCH_SLOUCH_THRESHOLD:
        return 1
    return 0


class SmoothedPitchClassifier:
    """Baseline B —> pitch threshold smoothed by majority vote over the last N labels.

    De-noises pitch_only_label so a single noisy sample near the threshold
    doesn't flip the output. N defaults to SMOOTHING_WINDOW.
    """

    def __init__(self, window=SMOOTHING_WINDOW):
        """Store the window size and an empty buffer of recent labels."""
        self._window = window
        self._buffer = []

    def predict(self, pitch_delta):
        """Return the majority label (0/1) over the last N samples."""
        label = pitch_only_label(pitch_delta)
        self._buffer.append(label)
        self._buffer = self._buffer[-self._window:]

        if sum(self._buffer) > len(self._buffer) / 2:
            return 1  # more forward labels in the window
        return 0 # more neutral labels in the window

    def reset(self):
        """Clear the buffer so a new file/session starts with no memory."""
        self._buffer = []

