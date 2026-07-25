"""
Read/write baseline.json, the user's neutral posture reference.

calibrate.py records ~10s of motion and saves μ/σ per field. The rest load it
back and either:
  apply_baseline() - Tier 1: raw delta from neutral (radians)
  zscore()         - Tiers 2-3: (x - μ) / σ, anatomy-invariant

Orientation is in radians; gravity in g.
"""

import json
import statistics

# Orientation + gravity define posture. Acceleration/rotationRate average ~0 at
# rest, so they're excluded.
BASELINE_FIELDS = ("pitch", "roll", "yaw", "gravityX", "gravityY", "gravityZ")

# Floor for σ. If the user sits perfectly still, σ ≈ 0 and z-scores blow up.
SIGMA_FLOOR = 1e-3


def mean_std_fields(samples):
    """Return (means, stds) dicts over BASELINE_FIELDS.

    samples is a list of motion dicts. Uses mean and population std per field.
    """
    means = {}
    stds = {}

    for field in BASELINE_FIELDS:
        values = [sample[field] for sample in samples]
        means[field] = statistics.fmean(values)
        stds[field] = statistics.pstdev(values)

    return (means, stds)


def save_baseline(means, stds, sample_count, duration_s, path):
    """Write baseline.json (mean + std per field) to path."""
    data = {
        "sample_count": sample_count,
        "duration_s": duration_s,
        "mean": {field: means[field] for field in BASELINE_FIELDS},
        "std": {field: stds[field] for field in BASELINE_FIELDS},
    }
    with open(path, "w", encoding='utf-8') as file:
        json.dump(data, file, indent=2)
    return data


def load_baseline(path):
    """Read baseline.json from path."""
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def apply_baseline(sample, baseline):
    """Tier 1: raw delta from neutral, in radians.

    Copy of sample with each BASELINE_FIELD replaced by (value - μ). Keeps the
    interpretable unit for the pitch threshold detector.
    """
    mean = baseline["mean"]
    out = {}
    for field in BASELINE_FIELDS:
        out[field] = sample[field] - mean[field]
    return out


def zscore(sample, baseline, sigma_floor=SIGMA_FLOOR):
    """Tiers 2-3: per-axis z-score, (x - μ) / max(σ, floor).

    Removes each user's neutral offset and movement scale so one shared model
    learns deviation patterns, not anatomy. ML lane only.
    """
    mean = baseline['mean']
    std = baseline['std']
    z_score = {}
    for field in BASELINE_FIELDS:
        z_score[field] = (sample[field] - mean[field]) / max(std[field], sigma_floor)
    return z_score

    