"""
Live posture daemon: Mac AirPods → classify → notify. Run via AirpodsPosture.app.

Tasks:
  - class InferenceEngine:
      - load baseline.json
      - rolling buffer of WINDOW_SIZE feature vectors
      - predict: pitch baseline first; later load PostureCNN from weights/
      - apply_baseline on each raw sample
  - main():
      - HeadphoneMotionReader stream
      - infer at INFERENCE_HZ (not every packet)
      - PostureStateMachine → notify() on sustained slouch
      - --dry-run flag to print predictions only
      - Ctrl+C graceful stop
"""
import sys
from mac_motion import HeadphoneMotionReader
from detectors import SmoothedPitchClassifier
from baseline import load_baseline, apply_baseline
from state_machine import PostureStateMachine
from config import INFERENCE_HZ, BASELINE_PATH
from notify import notify


class InferenceEngine:
    def __init__(self):
        self._baseline = load_baseline(BASELINE_PATH)
        self._classifier = SmoothedPitchClassifier()

    def predict(self, sample):
        delta = apply_baseline(sample, self._baseline)['pitch']
        return self._classifier.predict(delta)
    
def main():
    engine = InferenceEngine()
    state_machine = PostureStateMachine()
    reader = HeadphoneMotionReader()

    if not reader.available():
        print("Error: AirPods motion not available.")
        return 1
    
    def on_sample(sample):
        label = engine.predict(sample)
        if state_machine.update(label):
            notify("Posture Check 🦒", "Your head's leaning forward — ease your chin back!")
    
    reader.start(on_sample)
    reader.run_until_stopped()
    return 0

    
if __name__ == "__main__":
    sys.exit(main())

