# src/dataset.py

import os
import pickle
from typing import List, Optional

import numpy as np
import torch
from torch.utils.data import Dataset, WeightedRandomSampler

from .config import Config


def _load_full_feature_names(data_dir: str) -> List[str]:
    path = os.path.join(data_dir, "feature_names.pkl")
    with open(path, "rb") as f:
        return list(pickle.load(f))


def _slice_features(X: np.ndarray, indices: Optional[List[int]]) -> np.ndarray:
    if indices is None:
        return X
    return X[:, :, indices]


class TimeSeriesFaultDataset(Dataset):
    def __init__(self, X: np.ndarray, y: np.ndarray, transform=None):
        self.X = torch.from_numpy(X).float()
        if y.ndim == 2:
            self.y = torch.from_numpy(y).float()
        else:
            self.y = torch.from_numpy(y).long()
        self.transform = transform

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        x = self.X[idx]
        y = self.y[idx]
        if self.transform:
            x = self.transform(x)
        return x, y


def _feature_indices(full_names: List[str], active: List[str]) -> List[int]:
    index = {n: i for i, n in enumerate(full_names)}
    return [index[c] for c in active]


def load_preprocessed_data(config: Config, split: Optional[str] = None):
    data_dir = config.processed_data_dir
    X_train = np.load(os.path.join(data_dir, "X_train.npy"))
    X_val = np.load(os.path.join(data_dir, "X_val.npy"))
    X_test = np.load(os.path.join(data_dir, "X_test.npy"))
    y_train = np.load(os.path.join(data_dir, "y_train.npy"))
    y_val = np.load(os.path.join(data_dir, "y_val.npy"))
    y_test = np.load(os.path.join(data_dir, "y_test.npy"))

    full_names = _load_full_feature_names(data_dir)
    active = getattr(config, "active_feature_columns", None)
    if active is not None and list(active) != full_names:
        idx = _feature_indices(full_names, list(active))
        X_train = _slice_features(X_train, idx)
        X_val = _slice_features(X_val, idx)
        X_test = _slice_features(X_test, idx)

    return X_train, X_val, X_test, y_train, y_val, y_test


def _sample_weights_for_classes(y: np.ndarray, num_classes: int) -> np.ndarray:
    y = np.asarray(y, dtype=np.int64)
    counts = np.bincount(y, minlength=num_classes).astype(np.float64)
    counts = np.maximum(counts, 1.0)
    class_weights = y.shape[0] / (num_classes * counts)
    return class_weights[y]


def create_dataloaders(config: Config):
    X_train, X_val, X_test, y_train, y_val, y_test = load_preprocessed_data(config)

    train_dataset = TimeSeriesFaultDataset(X_train, y_train)
    val_dataset = TimeSeriesFaultDataset(X_val, y_val)
    test_dataset = TimeSeriesFaultDataset(X_test, y_test)

    loader_kw = dict(
        batch_size=config.batch_size,
        num_workers=getattr(config, "num_workers", 0),
        pin_memory=torch.cuda.is_available(),
    )

    train_sampler = None
    if getattr(config, "use_weighted_sampler", False):
        sample_weights = _sample_weights_for_classes(y_train, int(config.num_classes))
        train_sampler = WeightedRandomSampler(
            weights=torch.from_numpy(sample_weights).double(),
            num_samples=len(sample_weights),
            replacement=True,
        )

    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        shuffle=train_sampler is None,
        sampler=train_sampler,
        **loader_kw,
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, shuffle=False, **loader_kw
    )
    test_loader = torch.utils.data.DataLoader(
        test_dataset, shuffle=False, **loader_kw
    )
    return train_loader, val_loader, test_loader
