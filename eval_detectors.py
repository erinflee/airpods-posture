"""
Evaluate pitch detectors on recorded CSVs -> tune config.py from results

  - load baseline.json
  - per labeled CSV, compare pitch_only_label and SmoothedPitchClassifier to truth
  - print accuracy for Baseline A and B
"""

import sys
import csv
import argparse
from pathlib import Path

from baseline import load_baseline
from config import BASELINE_PATH, CLASS_PREFIX_TO_ID, DATA_DIR
from pitch_director import SmoothedPitchClassifier, pitch_only_label


def truth_label(path):
    stem = Path(path).stem
    prefix = stem.split("_")[0]
    if prefix in CLASS_PREFIX_TO_ID:
        return CLASS_PREFIX_TO_ID.get(prefix)
    raise ValueError("incorrect file path name")


def pitch_deltas(path, baseline):
    with open(path, 'r', newline='', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))

    deltas = []
    baseline_mean_pitch = baseline["mean"].get("pitch")
    for row in rows:
        deltas.append(float(row['pitch']) - baseline_mean_pitch)

    return deltas
