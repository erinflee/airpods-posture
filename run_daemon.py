"""
Live posture daemon: Mac AirPods → classify → notify. Run via AirpodsPosture.app.
"""
import sys
from mac_motion import HeadphoneMotionReader
from detectors import SmoothedPitchClassifier
from baseline import load_baseline, apply_baseline
from state_machine import PostureStateMachine
from config import INFERENCE_HZ, BASELINE_PATH
from notify import notify


class InferenceEngine:
    """Turns one raw motion sample into a posture label.

    Loads the user's baseline once, then for each sample measures pitch
    delta from neutral and hands it to the Tier 1 classifier.
    """

    def __init__(self):
        self._baseline = load_baseline(BASELINE_PATH)
        self._classifier = SmoothedPitchClassifier()

    def predict(self, sample):
        """Return the posture label for one sample (pitch delta -> class)."""
        delta = apply_baseline(sample, self._baseline)['pitch']
        return self._classifier.predict(delta)


def main():
    """Stream AirPods motion live -> notify when slouch is held long enough.

    Wires the pipeline together: sensor -> InferenceEngine (delta + classify) 
    -> PostureStateMachine (hold/cooldown) -> notify. Returns 1 if AirPods
    motion isn't available, else blocks until the stream stops.
    """
    engine = InferenceEngine()
    state_machine = PostureStateMachine()
    reader = HeadphoneMotionReader()

    if not reader.available():
        print("Error: AirPods motion not available.")
        return 1
    
    def on_sample(sample):
        """Handle one live sample: classify it, and notify if the state
        machine says slouch has been held long enough to alert."""
        label = engine.predict(sample)
        if state_machine.update(label):
            notify("Posture Check 🦒", "Your head's leaning forward — ease your chin back!")
    
    reader.start(on_sample)
    reader.run_until_stopped()
    return 0

    
if __name__ == "__main__":
    sys.exit(main())

