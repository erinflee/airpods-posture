"""
1D-CNN for posture windows 

"""

import torch
import torch.nn as nn
from config import NUM_CLASSES


class PostureCNN(nn.Module):
  def __init__(self, num_classes=NUM_CLASSES):
    super().__init__()
    self.conv1 = nn.Conv1d(in_channels=6, out_channels=32, kernel_size=5, padding=2)
    self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=5, padding=2)
    self.pool = nn.MaxPool1d(kernel_size=2)
    self.gap = nn.AdaptiveAvgPool1d(1) # global average pooling
    self.relu = nn.ReLU()
    self.fc = nn.Linear(in_features=64, out_features=num_classes)

  def forward(self, x):
    out1 = self.conv1(x)
    relu1 = self.relu(out1)
    pool1 = self.pool(relu1)

    out2 = self.conv2(pool1)
    relu2 = self.relu(out2)
    pool2 = self.pool(relu2)

    gap = self.gap(pool2) # how strong was this feature across whole window
    squeeze = gap.squeeze(-1) # remove leftover dimension size 1
    x = self.fc(squeeze)
    return x