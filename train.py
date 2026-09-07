"""
Training loop 

"""

import sys
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


def evaluate(model, loader, device):
  correct = 0
  model.eval()

  with torch.no_grad():
    for X, y in loader:
      X, y = X.to(device), y.to(device)
      output = model(X)
      preds = output.argmax(dim=1)
      correct += (preds == y).sum().item()
    
  return correct / len(loader.dataset)


def main():

  train, val, session = build_datasets(DATA_DIR)

  device = "mps" if torch.backends.mps.is_available() else "cpu" # because i'm on mac and gpu not available
  model = PostureCNN().to(device)

  train_dataloader = DataLoader(dataset=train, batch_size=BATCH_SIZE, shuffle=True)
  val_dataloader = DataLoader(dataset=val, batch_size=BATCH_SIZE, shuffle=False)

  optimizer = torch.optim.Adam(params=model.parameters(), lr=LEARNING_RATE)
  criterion = nn.CrossEntropyLoss() # common loss for classification problems

  best_acc = 0
  for epoch in range(EPOCHS):
    training_loss = train_one_epoch(model, train_dataloader, optimizer, criterion, device)
    val_acc = evaluate(model, val_dataloader, device)
    print(f"epoch: {epoch + 1:02d}  loss={training_loss:.4f} val_acc={val_acc:.3f}")

    if val_acc > best_acc:
      best_acc = val_acc
      torch.save(model.state_dict(), MODEL_PATH)

  print(f"best val_acc={best_acc:.3f}  saved to {MODEL_PATH}")
  return 0


if __name__ == "__main__":
  sys.exit(main())