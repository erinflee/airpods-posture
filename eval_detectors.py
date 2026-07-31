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


