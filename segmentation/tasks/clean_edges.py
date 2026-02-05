import os
from pathlib import Path
import logging

import numpy as np
from dotenv import load_dotenv

from segmentation.core.cleaning import *
from segmentation.core.views import cleaning_comparison_plot
from segmentation.core.io import load_h5, save_h5, get_h5_files
from segmentation.core.logger import setup_logging

# Configure logging
logger = logging.getLogger(__name__)
setup_logging()

# Configure environment
load_dotenv()
data_path_env = os.getenv('DATA_PATH')
if not data_path_env or data_path_env == "path/to/your/data":
    logger.error("Environment variable DATA_PATH is not set. Please configure .env with DATA_PATH pointing to your data directory.")
    raise SystemExit("Missing required environment variable: DATA_PATH")

data_path = Path(data_path_env)
if not data_path.exists():
    logger.error(f"DATA_PATH '{data_path}' does not exist. Check your .env configuration.")
    raise SystemExit(f"DATA_PATH does not exist: {data_path}")

key = os.getenv('KEY')
if not key or key == "your_segmentation_key":
    logger.error("Environment variable KEY is not set. Please configure .env with KEY specifying the dataset key to use.")
    raise SystemExit("Missing required environment variable: KEY")


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
        tuple[np.ndarray, np.ndarray]: A tuple containing the raw dataset for the given key, and the cleaned version.
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


def main():    
    failed_files = []

    h5_files = get_h5_files(data_path)
    
    for h5_file in h5_files:
        try:
            logger.info(f"Processing {h5_file.name}...")
            segmentation, cleaned_segmentation = cleanup_segmentation(h5_file, key)
            cleaning_comparison_plot(segmentation, cleaned_segmentation, h5_file, save=True)
            save_h5(h5_file, cleaned_segmentation, key='cleaned')
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


if __name__ == "__main__":
    main()
