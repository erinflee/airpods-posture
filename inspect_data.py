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
from config import BASELINE_PATH, DATA_DIR


def load_csv(csv_path):
    with open(csv_path, 'r', newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)
