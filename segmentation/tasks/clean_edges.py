"""Task module to clean segmentation results by removing boundary-touching labels.

This module contains the command-line task used to process a directory of
.h5 segmentation files, locate the main tissue and remove unwanted labels
including those that touch the volume boundary.
"""

import logging
from pathlib import Path

import numpy as np

from segmentation.core.cleaning import (
    apply_mask,
    apply_watershed_segmentation,
    calculate_tissue_properties,
    create_mask,
    determine_main_tissue,
    get_edge_labels,
    get_recursive_edge_label_neighbors,
    make_binary,
    remove_labels,
)
from segmentation.core.io import get_h5_files, load_h5, move_h5, read_h5_voxel_size, save_h5
from segmentation.core.logger import setup_logging
from segmentation.core.views import cleaning_comparison_plot

# Configure logging
logger = logging.getLogger(__name__)
setup_logging()


def resolve_h5_dirs(h5_dir: Path | str, move: bool) -> tuple[Path, Path]:
    h5_dir = Path(h5_dir)

    if not h5_dir.is_dir():
        raise ValueError(f"Expected a directory path, got: {h5_dir}")

    # No movement → same directory
    if not move:
        return h5_dir, h5_dir

    # Determine base dataset directory
    if h5_dir.name == "raw":
        base = h5_dir.parent
        input_dir = h5_dir
    else:
        base = h5_dir
        input_dir = base / "raw"

    output_dir = base / "clean"

    # Ensure structure exists
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Move files to input_dir
    for file in h5_dir.glob('*.h5'):
        move_h5(file, input_dir)

    return input_dir, output_dir


def post_cleanup(dataset: np.ndarray) -> np.ndarray:
    """Remove labels that touch the volume boundaries.
    
    Identifies any labels that have voxels on the boundary planes (first/last slices
    in z, y, x dimensions) and removes them by setting those voxels to 0. This ensures
    that only fully contained tissue regions remain.
    
    Args:
        dataset (np.ndarray): Labeled image where each tissue has a unique integer label.
    
    Returns:
        np.ndarray: Cleaned labeled image with border-touching labels removed.
    """
    edge_labels = get_edge_labels(dataset)
    edge_edge_labels = get_recursive_edge_label_neighbors(dataset, edge_labels)
    labels_to_remove = edge_labels.union(edge_edge_labels) # Combine both sets of labels to remove

    cleaned = remove_labels(dataset, labels_to_remove)

    return cleaned


def cleanup_segmentation(path: Path, key: str | None) -> tuple[np.ndarray, np.ndarray]:
    """Removes unwanted labels bordering the main tissue.

    Performs the following actions:
    - Opens a dataset for a given key
    - Binarizes the dataset
    - Applies watershed algorithm to obtain separate tissues
    - Scores each tissue on how likely it is to be main tissue
    - Produces mask from main tissue and removes other tissues
    - Removes any remaining labels that touch the borders

    Args:
        path (Path): Path to the file to be cleaned.
        key (str): The key specifying which dataset should be used for analysis.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing the raw dataset for the given key, 
            and the cleaned version.
    """
    dataset = load_h5(path, key)
    binary = make_binary(dataset)
    tissues = apply_watershed_segmentation(binary)
    tissue_properties = calculate_tissue_properties(binary, tissues)
    main_tissue = determine_main_tissue(tissue_properties)

    mask = create_mask(tissues, main_tissue)
    masked_dataset = apply_mask(dataset, mask)
    cleaned_dataset = post_cleanup(masked_dataset)

    return dataset, cleaned_dataset


def main(input_dir: Path, segmentation_key: str, move: bool):
    """Process all configured .h5 files and save cleaned segmentations.

    Iterates over the files returned by :func:`segmentation.core.io.get_h5_files`,
    runs :func:`cleanup_segmentation` on each, writes comparison plots and
    stores the cleaned segmentation under the key ``'cleaned'``. Errors are
    logged and collected in ``failed_files`` for reporting.
    """
    input_dir, output_dir = resolve_h5_dirs(input_dir, move=move)
    
    failed_files = []

    h5_files = get_h5_files(input_dir)

    for h5_file in h5_files:
        try:
            logger.info(f"Processing {h5_file.name}...")
            segmentation, cleaned_segmentation = cleanup_segmentation(h5_file, segmentation_key)
            cleaning_comparison_plot(segmentation, cleaned_segmentation, h5_file, save=True)
            voxel_size = read_h5_voxel_size(path=h5_file, key=segmentation_key)
            save_h5(h5_file, cleaned_segmentation, voxel_size=voxel_size, key='cleaned')
            if move:
                move_h5(h5_file, output_dir)
            logger.info(f"✓ {h5_file.name} processed successfully")
        
        except (FileNotFoundError, KeyError) as e:
            logger.error(f"✗ {h5_file.name}: {e}")
            failed_files.append((h5_file.name, str(e)))
        
        except Exception as e:
            logger.error(f"✗ {h5_file.name}: Unexpected error: {type(e).__name__}: {e}")
            failed_files.append((h5_file.name, str(e)))

    if failed_files:
        logger.warning(f"{len(failed_files)} file(s) failed processing")
    else:
        logger.info("All files processed successfully!")