"""Module that provides functionality to deal with .h5 datasets."""
import logging
from os.path import getsize
from pathlib import Path

import bioio_lif
import h5py
import numpy as np
from bioio import BioImage

# Define logger
logger = logging.getLogger(__name__)


def load_h5(path: Path, key: str | None) -> np.ndarray:
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


def save_h5(path: Path, stack: np.ndarray, key: str | None, mode: str = "a") -> None:
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
            dataset = np.array(f[key])
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


def read_lif(filename: Path) -> BioImage:
    """Reads a .lif file into a BioImage object.

    Args:
        filename (Path): Path to the .lif file.

    Returns:
        BioImage: BioImage representation of .lif file

    Raises:
        ValueError: If provided filetype is not a .lif file.
    """
    if filename.suffix != '.lif':
        raise ValueError(f'Expected a .lif file, got {filename.suffix}')

    return BioImage(filename, reader=bioio_lif.Reader)


def safe_scenename(scene:str) -> str:
    """.lif files taken using navigator functionality might containt slashes in their scenenames, which makes them annoying to save.
    
    This function returns a safe scenename that can be used for saving.
    
    Args:
        scene (str): Scenename
        
    Returns:
        str: Safe scenename
    """
    if '/' in scene:
        safe_scene = scene.split('/')[-1]
    elif '\\' in scene:
        safe_scene = scene.split('\\')[-1]
    else:
        safe_scene = scene

    return safe_scene


def save_scenes_as_ome_tiff(bioimg: BioImage, output_dir: Path) -> None:
    """Iterates over all scenes in a BioImage object and saves each of them as ome.tiff
    while preserving physical pixel dimensions.

    Supports 5D (TCZYX) images, but provides no option to produce subsets. That means that
    dimensonality in == dimensionality out. When single timepoint and single channel images
    are required, such as for PlantSeg analysis, they should also be provided as such.

    Args:
        bioimg (BioImage): BioImage object (image) containing at least 1 scene.
        output_dir (Path): Directory where scenes are stored.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f'Found {len(bioimg.scenes)} scenes in BioImage: \n')

    for i, scene in enumerate(bioimg.scenes):
        safe_scene = safe_scenename(scene)
        path = output_dir / f'{safe_scene}.ome.tiff'
        try:
            bioimg.save(path, select_scenes=[scene])
            logger.info(f"Converted image {i +1}/{len(bioimg.scenes)}: {safe_scene}.ome.tiff")
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e} \n Could not save scene {safe_scene}.")
