"""
1D CNN model for land-use classification using Sentinel-1/2 time-series data.
Input shape: (n_samples, 3, 13) — 3 channels (NDVI, VH, VV), 13 monthly timesteps.
"""

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


def reshape_for_cnn(X: np.ndarray) -> np.ndarray:
    """Reshape flat feature array to 3-channel time-series format.

    Parameters
    ----------
    X : np.ndarray, shape (n_samples, 39)
        Flat feature array where features are ordered as
        [NDVI_t0..NDVI_t12, VH_t0..VH_t12, VV_t0..VV_t12].

    Returns
    -------
    np.ndarray, shape (n_samples, 3, 13)
    """
    n_samples = X.shape[0]
    return X.reshape(n_samples, 3, 13)


# ---------------------------------------------------------------------------
# Model architecture
# ---------------------------------------------------------------------------

class _CNN1D(nn.Module):
    """Lightweight 1D CNN classifier."""

    def __init__(self, n_channels: int, n_timesteps: int, num_classes: int):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(n_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),          # -> (64, n_timesteps//2)
            nn.Dropout(0.25),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(4),              # -> (128, 4)
            nn.Dropout(0.25),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 4, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


# ---------------------------------------------------------------------------
# Trainer
# ---------------------------------------------------------------------------

class CNNTrainer:
    """Training wrapper for the 1D CNN classifier.

    Parameters
    ----------
    num_classes : int
        Number of output classes.
    learning_rate : float
        Initial learning rate for Adam optimiser.
    device : torch.device or str
        Device to train on ('cpu' or 'cuda').
    """

    def __init__(
        self,
        num_classes: int = 8,
        learning_rate: float = 0.001,
        device=None,
    ):
        self.num_classes = num_classes
        self.lr = learning_rate
        self.device = device or torch.device("cpu")

        self.model = _CNN1D(
            n_channels=3, n_timesteps=13, num_classes=num_classes
        ).to(self.device)

        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, patience=5, factor=0.5, verbose=False
        )

        self.history: dict = {
            "train_loss": [],
            "val_loss": [],
            "train_acc": [],
            "val_acc": [],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_tensor(self, X: np.ndarray, y: np.ndarray = None):
        X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
        if y is not None:
            y_t = torch.tensor(y.astype(np.int64)).to(self.device)
            return X_t, y_t
        return X_t

    def _make_loader(self, X, y, batch_size: int, shuffle: bool) -> DataLoader:
        X_t, y_t = self._to_tensor(X, y)
        dataset = TensorDataset(X_t, y_t)
        return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)

    def _run_epoch(self, loader: DataLoader, train: bool):
        self.model.train(train)
        total_loss, correct, total = 0.0, 0, 0
        ctx = torch.enable_grad() if train else torch.no_grad()
        with ctx:
            for X_batch, y_batch in loader:
                if train:
                    self.optimizer.zero_grad()
                logits = self.model(X_batch)
                loss = self.criterion(logits, y_batch)
                if train:
                    loss.backward()
                    self.optimizer.step()
                total_loss += loss.item() * len(y_batch)
                preds = logits.argmax(dim=1)
                correct += (preds == y_batch).sum().item()
                total += len(y_batch)
        return total_loss / total, correct / total

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        verbose: bool = True,
    ):
        """Train the CNN model.

        Parameters
        ----------
        X_train, X_val : np.ndarray, shape (n, 3, 13)
        y_train, y_val : np.ndarray, shape (n,) — integer class labels
        epochs : int
        batch_size : int
        verbose : bool
        """
        train_loader = self._make_loader(X_train, y_train, batch_size, shuffle=True)
        val_loader = self._make_loader(X_val, y_val, batch_size, shuffle=False)

        best_val_loss = float("inf")
        best_state = None

        for epoch in range(1, epochs + 1):
            train_loss, train_acc = self._run_epoch(train_loader, train=True)
            val_loss, val_acc = self._run_epoch(val_loader, train=False)
            self.scheduler.step(val_loss)

            self.history["train_loss"].append(train_loss)
            self.history["val_loss"].append(val_loss)
            self.history["train_acc"].append(train_acc)
            self.history["val_acc"].append(val_acc)

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}

            if verbose:
                print(
                    f"Epoch {epoch:3d}/{epochs} | "
                    f"train_loss={train_loss:.4f}  train_acc={train_acc:.4f} | "
                    f"val_loss={val_loss:.4f}  val_acc={val_acc:.4f}"
                )

        # Restore best weights
        if best_state is not None:
            self.model.load_state_dict(best_state)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """Evaluate on a held-out test set.

        Returns
        -------
        dict with keys: accuracy, precision, recall, f1, confusion_matrix
        """
        self.model.eval()
        X_t = self._to_tensor(X_test)
        with torch.no_grad():
            logits = self.model(X_t)
        preds = logits.argmax(dim=1).cpu().numpy()
        y_true = y_test.astype(np.int64)

        acc = accuracy_score(y_true, preds)
        prec = precision_score(y_true, preds, average="weighted", zero_division=0)
        rec = recall_score(y_true, preds, average="weighted", zero_division=0)
        f1 = f1_score(y_true, preds, average="weighted", zero_division=0)
        cm = confusion_matrix(y_true, preds)

        print(f"Accuracy : {acc:.4f}")
        print(f"Precision: {prec:.4f}")
        print(f"Recall   : {rec:.4f}")
        print(f"F1 Score : {f1:.4f}")

        return {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "confusion_matrix": cm,
        }

    def plot_history(self):
        """Plot loss and accuracy curves."""
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        axes[0].plot(self.history["train_loss"], label="Train Loss")
        axes[0].plot(self.history["val_loss"], label="Val Loss")
        axes[0].set_title("Loss")
        axes[0].set_xlabel("Epoch")
        axes[0].legend()

        axes[1].plot(self.history["train_acc"], label="Train Acc")
        axes[1].plot(self.history["val_acc"], label="Val Acc")
        axes[1].set_title("Accuracy")
        axes[1].set_xlabel("Epoch")
        axes[1].legend()

        plt.tight_layout()
        plt.show()

    def save(self, path: str):
        """Save model weights to a .pth file."""
        torch.save(self.model.state_dict(), path)
        print(f"Model saved to {path}")

    def load(self, path: str):
        """Load model weights from a .pth file."""
        state = torch.load(path, map_location=self.device)
        self.model.load_state_dict(state)
        self.model.to(self.device)
        print(f"Model loaded from {path}")
