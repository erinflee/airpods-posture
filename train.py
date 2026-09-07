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
  total_loss = 0.0
  model.train()

  for X, y in loader:
    X, y = X.to(device), y.to(device)
    optimizer.zero_grad()
    output = model(X)
    loss = criterion(output, y)
    loss.backward()
    optimizer.step()

    total_loss += loss.item() * len(y)

  return total_loss / len(loader.dataset)


def main():

  train, val, session = build_datasets(DATA_DIR)

  device = "mps" if torch.backends.mps.is_available() else "cpu" # because i'm on mac and gpu not available
  model = PostureCNN().to(device)

  train_dataloader = DataLoader(dataset=train, batch_size=BATCH_SIZE, shuffle=True)
  val_dataloader = DataLoader(dataset=val, batch_size=BATCH_SIZE, shuffle=False)

  optimizer = torch.optim.Adam(params=model.parameters(), lr=LEARNING_RATE)
  criterion = nn.CrossEntropyLoss() # common loss for classification problems
 
  train_one_epoch(model, train_dataloader, optimizer, criterion, device)
