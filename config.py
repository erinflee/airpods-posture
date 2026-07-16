"""Shared constants."""

from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
WEIGHTS_DIR = ROOT / "weights"
BASELINE_PATH = ROOT / "baseline.json"
MODEL_PATH = WEIGHTS_DIR / "posture_model.pth"

# Sliding windows (ML tiers only)
WINDOW_SIZE = 100 # ~2s at 50Hz
WINDOW_STRIDE = 25 # ~75% overlap

# CSV columns from record_mac.py
FEATURE_FIELDS = [
    "roll", # ear-to-shoulder tilt
    "pitch", # chin up/down
    "yaw", # head turn
    "accelerationX",
    "accelerationY",
    "accelerationZ",
    "rotationRateX",
    "rotationRateY",
    "rotationRateZ",
]

# Class label from filename prefix (forward_01.csv -> 1)
CLASS_PREFIX_TO_ID = {
    "neutral": 0,
    "forward": 1,
    "dynamic": 2,
}
NUM_CLASSES = len(CLASS_PREFIX_TO_ID)

# Tier 1 pitch threshold. Negative because chin-down = negative pitch.
PITCH_SLOUCH_THRESHOLD = -0.15 # rad (-0.15 ≈ -8.6°)
SMOOTHING_WINDOW = 5

# Live daemon timing
INFERENCE_HZ = 2 # one sample per 0.5s
SLOUCH_HOLD_S = 5
MIN_GAP_ALERT_S = 3

# Screen-edge border alert
BORDER_THICKNESS = 14 # points
BORDER_COLOR = (0.85, 0.1, 0.1, 0.92) # RGBA 0-1, translucent red

# Banner alert. We draw our own; a real Notification Center banner kills motion.
BANNER_WIDTH = 360      # points
BANNER_HEIGHT = 88
BANNER_MARGIN = 20      # gap from top-right corner
BANNER_DURATION_S = 4   # auto-dismiss

# Alert sound via afplay. Plain playback is motion-safe.
ALERT_SOUND = "/System/Library/Sounds/Glass.aiff"

# Training defaults (Tier 3)
EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 0.001
VAL_FRACTION = 0.2
