"""Project constants. Other files import settings from here."""

from pathlib import Path

# --- Paths ---
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
WEIGHTS_DIR = ROOT / "weights"
BASELINE_PATH = ROOT / "baseline.json"
MODEL_PATH = WEIGHTS_DIR / "posture_model.pth"

# --- Sliding windows (ML tiers only) ---
WINDOW_SIZE = 100 # ~2 s at 50 Hz
WINDOW_STRIDE = 25 # ~75% overlap

# CSV column names from record_mac.py
FEATURE_FIELDS = [
    "roll", # tilt ear toward shoulder
    "pitch", # chin up/down
    "yaw", # turn head left/right
    "accelerationX", # sudden linear move (x)
    "accelerationY", # sudden linear move (y)
    "accelerationZ", # sudden linear move (z)
    "rotationRateX", # how fast roll changes
    "rotationRateY", # how fast pitch changes
    "rotationRateZ", # how fast yaw changes
]

# --- Class labels (from filename prefix, e.g. forward_01.csv -> 1) ---
CLASS_PREFIX_TO_ID = {
    "neutral": 0,
    "forward": 1,
    "dynamic": 2,
}
NUM_CLASSES = len(CLASS_PREFIX_TO_ID)

# --- Tier 1 pitch threshold ---
PITCH_SLOUCH_THRESHOLD = -0.15 # radians (Core Motion's unit); -0.15 rad ≈ -8.6°
SMOOTHING_WINDOW = 5

# --- Live daemon timing ---
INFERENCE_HZ = 2
SLOUCH_HOLD_S = 15
ALERT_COOLDOWN_S = 60

# --- Training defaults (Tier 3) ---
EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 0.001
VAL_FRACTION = 0.2
