"""Module that provides functionality to deal with .h5 datasets."""
from os.path import getsize
from pathlib import Path
from typing import Optional

import h5py
import numpy as np


def load_h5(path: Path, key: str) -> np.ndarray:
    """Load a dataset as a numpy array using context manager by given key from a .h5 file.

    Args: 
        path (Path): Path to the .h5 file.
        key (str): Key of the dataset to load.

    Returns: 
        np.ndarray: The loaded dataset.
        
    Raises:
        KeyError: If the key doesn't exist in the file.
        FileNotFoundError: If the file doesn't exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if key is None or key == "":
        raise ValueError("Key is required to load a dataset from a .h5 file")
    
    with h5py.File(path, 'r') as f:
        if key not in f:
            available_keys = list(f.keys())
            raise KeyError(f"Key '{key}' not found in {path.name}. Available keys: {available_keys}")
        dataset = np.array(f[key])

    return dataset


def save_h5(path: Path, stack: np.ndarray, key: Optional[str], mode: str = "a") -> None:
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


def move_h5(file: Path, dest_path: Path) -> None:
        
    destination = dest_path / file.name

    file.rename(destination)


def get_h5_files(folder_path: Path) -> list[Path]:
    """Get all .h5 files in a folder.
    
    Args:
        folder_path (Path): Path to the folder to search.
    
    Returns:
        list[Path]: List of .h5 file paths.
    """
    h5_files = list(folder_path.glob('*.h5'))
    return sorted(h5_files)


def print_h5_metrics(file_path: Path) -> None:
    """Inspect and print metrics about a .h5 file.
    
    Args:
        file_path (Path): Path to the .h5 file to inspect.
    """
    # File size
    file_size_mb = getsize(file_path) / (1024 ** 2)
    
    print(f"\n{'='*60}")
    print(f"File: {file_path.name}")
    print(f"{'='*60}")
    print(f"Path: {file_path}")
    print(f"Size: {file_size_mb:.2f} MB")
    print(f"\n{'Datasets:':<50}")
    print(f"{'-'*60}")
    
    with h5py.File(file_path, 'r') as f:
        # Print all keys and their properties
        for key in f.keys():
            dataset = f[key]
            shape = dataset.shape
            dtype = dataset.dtype
            
            print(f"\nKey: {key}")
            print(f"  Shape: {shape}")
            print(f"  Data type: {dtype}")
            print(f"  Size: {dataset.nbytes / (1024 ** 2):.2f} MB")
            
            # Print statistics for numeric datasets
            if dataset.dtype.kind in ['f', 'i', 'u']:  # float, signed int, unsigned int
                print(f"  Min: {dataset[()].min():.4f}")
                print(f"  Max: {dataset[()].max():.4f}")
                print(f"  Mean: {dataset[()].mean():.4f}")
    
    print(f"\n{'='*60}\n")