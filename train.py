"""
Training loop 

"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from config import BATCH_SIZE, EPOCHS, LEARNING_RATE, MODEL_PATH, DATA_DIR
from dataset import build_datasets
from model import PostureCNN


def train_one_epoch(model, loader, optimizer, criterion, device):




def main():

  train, val, session = build_datasets(DATA_DIR)

  model = PostureCNN()
  train_dataloader = DataLoader(dataset=train, batch_size=BATCH_SIZE, shuffle=False)
  val_dataloader = DataLoader(dataset=val, batch_size=BATCH_SIZE, shuffle=False)

  optimizer = torch.optim.SGD(params=model.params, lr=LEARNING_RATE)
  criterion = nn.CrossEntropyLoss() # common loss for classification problems

  device = model.to("mps") # because i'm on mac and gpu not available
  train_one_epoch(model, train_dataloader, optimizer, criterion, device)

