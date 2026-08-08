"""
Shared feature extraction for training and inference 

"""

import csv
from pathlib import Path

import numpy as np

from baseline import baseline_for_csv, load_baseline, zscore
from config import CLASS_PREFIX_TO_ID, DATA_DIR, WINDOW_SIZE, WINDOW_STRIDE


def label_from_filename(path):
	"""Class id (0/1/2) from the filename prefix (neutral_/forward_/dynamic_)."""
	prefix = Path(path).stem.split("_")[0]
	if prefix not in CLASS_PREFIX_TO_ID:
		raise ValueError(f"unknown class prefix in filename: {prefix}")
  	return CLASS_PREFIX_TO_ID[prefix]
  



