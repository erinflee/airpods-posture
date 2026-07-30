"""
Plot and summarize CSV recordings before training

  - summarize_file(path): sample count, pitch/roll mean/std
  - plot_file(path, out_dir): save pitch/roll vs time PNG to results/
  - main(): loop data/*.csv, print stats, optional --plot
"""

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyploy as plt
from statistics import fmean, pstdev
from config import BASELINE_PATH, DATA_DIR, CLASS_PREFIX_TO_ID

def load_csv(csv_path):
    with open(csv_path, 'r', newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def label_from_filename(path):
    filename = Path(path).stem # neutral_01.csv -> cuts .csv and returns neutral_01
    prefix = filename.split("_")[0]
    if prefix in CLASS_PREFIX_TO_ID.keys():
        return prefix
    raise ValueError("invalid file name")
    

def summarize_file(path, baseline):
    rows = load_csv(path)
    prefix = label_from_filename(path)
    baseline_mean_pitch = baseline["mean"]["pitch"]
    data = {
        "pitch": [],
        "roll": [], 
        "delta_pitch": []
    }

    for row in rows: 
        data["pitch"].append(float(row["pitch"]))
        data["roll"].append(float(row["roll"]))
        data["delta_pitch"].append(float(row["pitch"]) - baseline_mean_pitch)

    stats = {
        "sample_count": len(rows),
        "label": prefix,
        "pitch_mean": fmean(data["pitch"]),
        "roll_mean": fmean(data["roll"]),
        "delta_pitch_mean": fmean(data["delta_pitch"]),
        "pitch_std": pstdev(data["pitch"]),
        "roll_std": pstdev(data["roll"]),
        "delta_pitch_std": pstdev(data["delta_pitch"]),
    }
    return stats




