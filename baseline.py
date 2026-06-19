"""
Helpers for baseline.json — this user's personal *neutral* posture reference.

calibrate.py collects ~10 s of motion dicts from mac_motion, then calls
mean_std_fields() and save_baseline() here. Later, record_mac.py / train.py /
run_daemon.py call load_baseline() plus:
  - apply_baseline() -> Tier 1 threshold: raw delta from neutral (radians)
  - zscore() -> Tiers 2-3 model: (x - μ) / σ, anatomy-invariant

All orientation values are radians (Core Motion's native unit); gravity is in g.
"""

import json
import statistics

# Bumped to 2: baseline now stores per-axis std (σ), not just means.
BASELINE_VERSION = 2

# Orientation + gravity define "neutral posture". acceleration / rotationRate
# are motion (mean ~0 at rest), so they are not part of the posture reference.
BASELINE_FIELDS = ("pitch", "roll", "yaw", "gravityX", "gravityY", "gravityZ")

# σ can be ~0 if the user sits very still during calibration; dividing by it
# would explode z-scores into noise. Floor every std to this minimum.
# NOTE: calibration σ is "stillness noise", not "normal working wiggle". If
# z-scores feel too hot, recompute σ from the neutral *recording* instead.
SIGMA_FLOOR = 1e-3


def mean_std_fields(samples):
    """Return (means, stds) dicts over BASELINE_FIELDS for a list of samples.

    samples is a list like [{"pitch": -0.48, "roll": 0.01, ...}, ...] from
    mac_motion. For each field, compute the mean (μ) and population std (σ).
    calibrate.py calls this after recording ~10 s of neutral posture.
    """


def save_baseline(means, stds, sample_count, duration_s, path):
    """Write baseline.json (version 2: mean + std per field) to path."""
    data = {
        "version": BASELINE_VERSION,
        "sample_count": sample_count,
        "duration_s": duration_s,
        "mean": {f: means[f] for f in BASELINE_FIELDS},
        "std": {f: stds[f] for f in BASELINE_FIELDS},
    }
    with open(path, "w", encoding='utf-8') as file:
        json.dump(data, file, indent=2)
    return data


def load_baseline(path):
    """Read baseline.json from path; raise if version mismatches."""
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    version = data.get("version")
    if version != BASELINE_VERSION:
        raise ValueError(
            f"baseline.json version {version} != {BASELINE_VERSION}; re-run calibrate.py"
        )
    return data


def apply_baseline(sample, baseline):
    """Tier 1 — raw delta from neutral, in radians.

    Return a copy of sample with each BASELINE_FIELD replaced by
    (value - μ). The threshold detector reads pitch delta in radians; this
    keeps the physical, interpretable unit ("X rad / degrees past neutral").
    """
    mean = baseline["mean"]
    out = dict(sample)
    for field in BASELINE_FIELDS:
        out[field] = sample[field] - mean[field]
    return out


def zscore(sample, baseline, sigma_floor=SIGMA_FLOOR):
    """Tiers 2-3 — per-axis z-score: (x - μ) / max(σ, floor).

    Strips out each user's neutral offset (μ) and movement scale (σ) so one
    shared model learns *deviation patterns*, not anatomy. ML lane only — the
    Tier 1 threshold uses apply_baseline() in raw radians instead.
    """
    