"""
Training loop 

"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from config import BATCH_SIZE, EPOCHS, LEARNING_RATE, MODEL_PATH
from dataset import build_datasets
from model import PostureCNN


