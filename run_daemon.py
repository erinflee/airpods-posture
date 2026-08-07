"""
Live posture daemon: motion -> classify -> alert. Run via AirpodsPosture.app.

The alert is a custom banner (banner.py) plus an afplay sound, both motion-safe.
A real Notification Center banner isn't; see keepalive_test.py.
"""
import subprocess
import sys

from airpods_motion import HeadphoneMotionReader
from pitch_detector import SmoothedPitchClassifier
from baseline import load_baseline, apply_baseline
from alert_timing import PostureStateMachine
from alert_banner import PostureBanner
from config import BASELINE_PATH, ALERT_SOUND


class InferenceEngine:
    """One raw motion sample -> one posture label.

    Loads the baseline once, then runs each sample's pitch delta through the
    Tier 1 classifier.
    """

    def __init__(self):
        self._baseline = load_baseline(BASELINE_PATH)
        self._classifier = SmoothedPitchClassifier()

    def predict(self, sample):
        """Label for one sample."""
        delta = apply_baseline(sample, self._baseline)['pitch']
        return self._classifier.predict(delta)


def main():
    """Stream motion and alert when slouch is held long enough.

    Pipeline: sensor -> InferenceEngine -> PostureStateMachine -> banner + sound.
    Returns 1 if motion isn't available, else blocks until the stream stops.
    """
    engine = InferenceEngine()
    state_machine = PostureStateMachine()
    reader = HeadphoneMotionReader()
    banner = PostureBanner.alloc().init()

    if not reader.available():
        print("Error: AirPods motion not available.")
        return 1

    state = {"count": 0}

    def fire_alert():
        """Play the sound and show the banner. Runs on the main queue (via
        on_sample), so no AppKit marshaling needed."""
        print(">>> posture alert — banner + sound", flush=True)
        subprocess.Popen(["afplay", ALERT_SOUND])
        banner.show_((
            "Posture Check",
            "Your head's leaning forward — ease your chin back!",
            "🦒",
        ))

    def on_sample(sample):
        """Classify one sample; alert if slouch held long enough."""
        delta = apply_baseline(sample, engine._baseline)['pitch']
        label = engine.predict(sample)

        state["count"] += 1
        if state["count"] == 1:
            print("Streaming AirPods motion — slouch and hold to trigger an alert. Ctrl+C to stop.", flush=True)
        if state["count"] % 48 == 0:
            print(f"pitch delta={delta:+.3f} rad  label={label}  samples={state['count']}", flush=True)

        if state_machine.update(label):
            fire_alert()

    reader.start(on_sample)
    reader.run_until_stopped()
    banner.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
