"""
PyTorch Dataset 

  - PostureWindowDataset(Dataset): __init__(x, y), __len__, __getitem__ -> (window, label)
  - build_datasets(data_dir, val_fraction):
      load baseline + windows from features.py, split train/val by session
      (not random frames), return train_ds, val_ds, source filenames
"""

import torch
from torch.utils.data import Dataset
from shared_features import load_labeled_windows
from config import DATA_DIR, VAL_FRACTION
import numpy as np


class PostureWindowDataset(Dataset):
  def __init__(self, x, y):
    self.x = torch.tensor(x, dtype=torch.float32)
    self.y = torch.tensor(y, dtype=torch.int64)

  def __len__(self):
    return len(self.x)

  def __getitem__(self, i):
    x = self.x[i]
    y = self.y[i]
    return x, y


def build_datasets(data_dir=DATA_DIR, val_fraction=VAL_FRACTION):
  X, y, sessions = load_labeled_windows(data_dir)
  sorted_sessions = sorted(np.unique(sessions))
  val_session = sorted_sessions[-1:]
  mask = np.isin(sessions, val_session) # check each session against list val_sessions number, returns true or false if match
  train_dataset = PostureWindowDataset(X[~mask], y[~mask])
  val_dataset = PostureWindowDataset(X[mask], y[mask])
  return train_dataset, val_dataset, val_session