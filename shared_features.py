"""
Shared feature extraction for training and inference 

"""

import csv
from pathlib import Path

import numpy as np

from baseline import baseline_for_csv, load_baseline, zscore
from config import CLASS_PREFIX_TO_ID, DATA_DIR, WINDOW_SIZE, WINDOW_STRIDE
