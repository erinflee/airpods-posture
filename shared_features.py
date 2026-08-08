"""
Shared feature extraction for training and inference 

"""

import csv
from pathlib import Path

import numpy as np

from baseline import baseline_for_csv, load_baseline, zscore, BASELINE_FIELDS
from config import CLASS_PREFIX_TO_ID, DATA_DIR, BASELINE_PATH, WINDOW_SIZE, WINDOW_STRIDE


def label_from_filename(path):
	"""Class id (0/1/2) from the filename prefix (neutral_/forward_/dynamic_)."""
	prefix = Path(path).stem.split("_")[0]
	if prefix not in CLASS_PREFIX_TO_ID:
		raise ValueError(f"unknown class prefix in filename: {prefix}")
	return CLASS_PREFIX_TO_ID[prefix]
  

def load_csv_rows(path, baseline=None):
	"""Read one recording CSV -> list of dicts with float values."""
	with open(path, 'r', encoding='utf-8') as file:
		rows = list(csv.DictReader(file))
	return [{key: float(value) for key, value in row.items()} for row in rows]
		

def rows_to_windows(rows):
	"""Sliding windows over rows -> (n_windows, channels, time) array."""
	values = []
	for row in rows:
		value = [row[field] for field in BASELINE_FIELDS]
		values.append(value)
	data = np.array(values)

	if len(data) < WINDOW_SIZE:
		return np.empty((0, len(BASELINE_FIELDS), WINDOW_SIZE))
	
	windows = []
	for start in range(0, len(data) - WINDOW_SIZE + 1, WINDOW_STRIDE):
		window = data[start:start+WINDOW_SIZE].T
		windows.append(window)
	return np.stack(windows)


def load_labeled_windows(data_dir=DATA_DIR):
	"""All labeled CSVs in data_dir -> X, y training arrays.

	Each file's rows are z-scored against its own session baseline
	(baseline_NN.json), then cut into sliding windows. Files without a
	class prefix (neutral_/forward_/dynamic_) are skipped.

	Returns X (n_windows, channels, time) and y (n_windows,) class ids.
	"""

	default_baseline = load_baseline(BASELINE_PATH)
	x_blocks = []
	y_blocks = []

	for csv_path in sorted(Path(data_dir).glob("*.csv")):
		if csv_path.stem.split("_")[0] not in CLASS_PREFIX_TO_ID:
			continue

		rows = load_csv_rows(csv_path)
		baseline = baseline_for_csv(csv_path, default_baseline)
		zrows = [zscore(row, baseline) for row in rows]
		windows = rows_to_windows(zrows)
		if len(windows) == 0:
			continue

		label = label_from_filename(csv_path)
		x_blocks.append(windows)
		y_blocks.append(np.full(len(windows), label)) # how many = length of windows, filled with one of three labels

	return np.concatenate(x_blocks), np.concatenate(y_blocks)
	
