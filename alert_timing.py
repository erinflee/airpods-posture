"""Alert timing —> decides WHEN to fire a posture notification."""
from config import SLOUCH_HOLD_S, MIN_GAP_ALERT_S
import time


class PostureStateMachine:
    """Fire only after forward flexion is held SLOUCH_HOLD_S AND MIN_GAP_ALERT_S
    has passed since the last alert. Neutral resets the hold, so brief sips and
    glances never reach it. Decides whether to alert, not how (caller notifies).
    """

    def __init__(self):
        """Both timers start off (None = not slouching / never alerted)."""
        self._start = None # when the current forward stretch began
        self._last_alert = None # when we last fired, for the min-gap check

    def update(self, predicted_class, now=None):
        """Feed one prediction (1 = forward) -> return True if an alert should fire.

        now defaults to time.monotonic() -> pass recorded timestamps for CSV eval.
        """
        if now is None:
            now = time.monotonic()

        # Neutral → cancel the hold timer; never fires.
        if predicted_class != 1:
            self._start = None
            return False

        if self._start is None:
            self._start = now

        held = now - self._start
        can_alert_again = self._last_alert is None or (now - self._last_alert >= MIN_GAP_ALERT_S)

        if held >= SLOUCH_HOLD_S and can_alert_again:
            self._last_alert = now
            return True
        return False

    def reset(self):
        """Clear both timers — use between files/sessions."""
        self._start = None
