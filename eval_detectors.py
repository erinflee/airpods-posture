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


def expected_label(path):
    stem = Path(path).stem
    prefix = stem.split("_")[0]
    if prefix != "forward":
        return 0
    return 1


def pitch_deltas(path, baseline):
    with open(path, 'r', newline='', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))

    deltas = []
    baseline_mean_pitch = baseline["mean"].get("pitch")
    for row in rows:
        deltas.append(float(row['pitch']) - baseline_mean_pitch)

    return deltas


def eval_file(path, baseline):

    spc = SmoothedPitchClassifier()

    expected = expected_label(path)
    deltas = pitch_deltas(path, baseline)
    total = len(deltas)
    a_correct = 0
    b_correct = 0
    for delta in deltas:
        baselinea = pitch_only_label(delta)
        baselineb = spc.predict(delta)

        if baselinea == expected:
            a_correct += 1
        
        if baselineb == expected:
            b_correct += 1

    return {"total": total, "a_correct": a_correct, "b_correct": b_correct}


def main():
    parser = argparse.ArgumentParser(description="This will determine slouch vs. no-slouch")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    args = parser.parse_args()

    baseline = load_baseline(args.baseline)
    csv_file = sorted(args.data_dir.glob("*.csv")) # glob("*.csv") -> grab all files ending in .csv
    if not csv_file:
        return 1
    
    a_correct_total = []
    b_correct_total = []
    n_total = []
    for csv_path in csv_file:
        result = eval_file(csv_path, baseline)
        accuracy_a = result["a_correct"] / result["total"] * 100
        accuracy_b = result["b_correct"] / result["total"] * 100
        a_correct_total.append(result["a_correct"])
        b_correct_total.append(result["b_correct"])
        n_total.append(result["total"])
        print(f"{csv_path}: Baseline A: {accuracy_a}%, Baseline B: {accuracy_b}%")

    overall_a = sum(a_correct_total) / sum(n_total) * 100
    overall_b = sum(b_correct_total) / sum(n_total) * 100

    print(f"overall: Baseline A: {overall_a}%, Baseline B: {overall_b}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())