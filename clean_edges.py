import logging
from pathlib import Path

import numpy as np

from segmentation.cleaning import *
from segmentation.models import load_h5, save_h5
from segmentation.views import cleaning_comparison_plot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

data_path = Path('/media/beta/rikfroeling/experiments/251201_CallusSegmentation/trained_workflow_output')
key = 'segmentation'


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


def cleanup_segmentation(path: Path, key: str) -> tuple[np.ndarray, np.ndarray]:
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
    
    for h5_file in data_path.glob('*.h5'):
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
