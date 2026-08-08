"""
PyTorch Dataset 

  - PostureWindowDataset(Dataset): __init__(x, y), __len__, __getitem__ -> (window, label)
  - build_datasets(data_dir, val_fraction):
      load baseline + windows from features.py, split train/val by session
      (not random frames), return train_ds, val_ds, source filenames
"""


