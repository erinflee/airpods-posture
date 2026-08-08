"""
1D-CNN for posture windows (TODO: implement).

  - PostureCNN(nn.Module):
      __init__(num_classes=3): Conv1d stack + Linear head
      forward(x): (batch, features, time) -> logits (batch, num_classes)
"""

import torch
import torch.nn as nn
from config import NUM_CLASSES

