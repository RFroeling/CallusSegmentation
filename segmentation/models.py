"""Module that provides function to deal with file handling for segmentation cleanup."""

from pathlib import Path

import h5py
import numpy as np


def load_h5(path: Path, key: str) -> np.ndarray:
    """Load a dataset as a numpy array using context manager by given key from a .h5 file.

    Args: 
        path (Path): Path to the .h5 file.
        key (str): Key of the dataset to load.

    Returns: 
        np.ndarray: The loaded dataset.
    """
    with h5py.File(path, 'r') as f:
        dataset = np.array(f[key])

    return dataset


def save_h5(path: Path, stack: np.ndarray, key: str, mode: str = "a") -> None:
    """
    Create a dataset inside a h5 file from a numpy array.

    Args:
        path (Path): path to the h5 file
        stack (np.ndarray): numpy array to save as dataset in the h5 file.
        key (str): key of the dataset in the h5 file.
        mode (str): mode to open the h5 file ['w', 'a'].

    """

    if key is None:
        raise ValueError("Key is required to create a dataset in a h5 file.")

    if key == "":
        raise ValueError("Key cannot be empty to create a dataset in a h5 file.")

    with h5py.File(path, mode) as f:
        if key in f:
            del f[key]
        f.create_dataset(key, data=stack, compression="gzip")
