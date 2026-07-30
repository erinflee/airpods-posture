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
    pitch = []
    roll = []
    delta_pitch = []
    stats = {}    
    for row in rows: 
        pitch.append(float(row["pitch"]))
        roll.append(float(row["roll"]))
        pitch_delta.append(float(row["pitch"]) - float(baseline["mean"]["pitch"]))

    pitch_mean = statistics.fmean(pitch)
    roll_mean = statistics.fmean(roll)
    delta_pitch_mean = statistics.fmean(delta_pitch)
    
    pitch_std = statistics.pstdev(pitch)
    roll_std = statistics.pstdev(roll)
    delta_pitch_std = statistics.pstdev(delta_pitch)

    stats["sample_count"] = len(rows)
    stats["label"] = prefix
    stats["pitch_mean"] = pitch_mean
    stats["roll_mean"] = roll_mean
    stats["delta_pitch_mean"] = delta_pitch_mean
    stats["pitch_std"] = pitch_std
    stats["roll_std"] = roll_std
    stats["delta_pitch_std"] = delta_pitch_std

    return stats





