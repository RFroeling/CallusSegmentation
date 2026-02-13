"""Helpers to extract surface meshes from labeled volume datasets.

This module contains a utility to convert labeled 3D images into surface
meshes using VTK. It supports exporting the whole tissue mesh as well as
individual cell meshes and performs simple filters (2D artefacts, small
objects) before writing files.
"""

import logging
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from segmentation.core.io import (
    calculate_age_from_id,
    load_h5,
    read_h5_voxel_size,
    save_df_to_csv,
)
from segmentation.core.meshes import (
    compute_contacts_and_neighbors,
    compute_label_bboxes,
    compute_label_sizes,
    extract_features_from_mesh,
    extract_label_surface,
    is_2d_label,
    is_too_small_label,
    keep_largest_component,
    numpy_to_vtk_image,
    save_mesh,
)

# Configure logging
logger = logging.getLogger(__name__)


def filter_unique_labels(data: np.ndarray, min_size: int) -> np.ndarray:
    """Filters labels from a 3D label image.

    Keeps only labels that:
    - are 3D (not 2D artefacts)
    - have a size >= min_size

    Args:
        data (np.ndarray): 3D label image.
        labels (np.ndarray): Array of unique labels in the image.
        min_size (int) : Minimum voxel size threshold.

    Returns:
        np.ndarray: Filtered labels.
    """
    bboxes = compute_label_bboxes(data)
    sizes = compute_label_sizes(data)

    unique_labels = np.unique(data)
    unique_labels = unique_labels[unique_labels != 0]

    filtered_labels = []

    for lbl in unique_labels:

        if is_2d_label(bboxes, lbl):
            logging.info(f"Skipping 2D artefact label {lbl}")
            continue

        if is_too_small_label(lbl, sizes, min_size):
            logging.info(f"Skipping tiny label {lbl}")
            continue

        filtered_labels.append(lbl)

    return np.array(filtered_labels)


def labels_to_meshes(
    data: np.ndarray,
    voxel_size: Sequence[float],
    callus_id: str,
    output_dir: Path,
    min_size: int,
    extract_cells: bool=True,
    extract_tissue: bool=True,
    calculate_features: bool=True,
) -> None:
    """Extract and save surface meshes from a labeled volume.

    The function writes a tissue mesh file named ``tissue.ply`` (when
    ``extract_tissue`` is True) and a per-cell mesh file ``cell_XXXXX.ply``
    for each label that meets the heuristics.

    Args:
        data (np.ndarray): 3D labeled image (ZYX).
        voxel_size (Sequence[float]): Voxel size in micrometers (zyx).
        output_dir (Path): Directory where meshes are written.
        min_size (int): Minimum voxel count for a label to be exported.
        extract_cells (bool): Whether to export individual cell meshes.
        extract_tissue (bool): Whether to export the whole tissue mesh.
        extract_featues (bool): Whether to extract numerical features from meshes.

    Returns:
        pd.DataFrame: Dataframe containing calculated features from meshes if
            extract_features was set to `True`.
    """
    vtk_img = numpy_to_vtk_image(data, voxel_size)

    # Analysis only on unique labels, that are no artefacts (small, 2D labels)
    filtered_labels = filter_unique_labels(data, min_size=min_size)


    age = calculate_age_from_id(callus_id)
    contact_pairs, background_contact, neighbor_count = compute_contacts_and_neighbors(data, filtered_labels, voxel_size)

    feature_rows = []

    if extract_tissue: # Extract whole tissue meshes

        logger.info("Extracting whole tissue...")

        binary = (data > 0).astype(np.uint8)
        vtk_binary = numpy_to_vtk_image(binary, voxel_size)

        tissue_surface = extract_label_surface(vtk_binary, 1)

        tissue_surface = keep_largest_component(tissue_surface)

        if calculate_features:
            tissue_features = extract_features_from_mesh(tissue_surface)
            tissue_features.update({'label': 'tissue', 
                                    'callus_id': callus_id, 
                                    'age': age,
                                    })
            feature_rows.append(tissue_features)

        save_mesh(tissue_surface, output_dir / "tissue.ply")

    if extract_cells: # Extract meshes for each cell

        for lbl in filtered_labels:

            logging.info(f"Extracting cell {lbl}")

            surface = extract_label_surface(vtk_img, lbl)

            if surface.GetNumberOfPoints() == 0: # Skip empty meshes
                continue

            if calculate_features:
                cell_features = extract_features_from_mesh(surface)
                neighbour_area = sum(
                    area for (l1, l2), area in contact_pairs.items() 
                    if lbl in (l1, l2) and 0 not in (l1, l2)
                    )
                cell_features.update({'label': f'cell_{lbl:03d}', 
                                      'callus_id': callus_id, 
                                      'age': age,
                                      'neighbors': int(neighbor_count[lbl]),
                                      'neighbor_area': neighbour_area,
                                      'background_area': background_contact[lbl],
                                      })
                feature_rows.append(cell_features)

            save_mesh(surface, output_dir / f"cell_{lbl:03d}.ply")
    
    if calculate_features:
        features = pd.DataFrame(feature_rows)
        logger.debug(f'\n{features.head()}')

        output_path = output_dir / f'{callus_id}_features.csv'
        save_df_to_csv(features, output_path)


def main():
    """Small test runner that converts a hard-coded test .h5 file to meshes.

    The function is primarily intended as a convenience for local testing and
    demonstration; paths and parameters are hard-coded.
    """
    h5_path = Path('.data/test_h5/251201_251215_Col-0_R01_W01_002.h5')
    h5_key = 'cleaned'
    callus_id = h5_path.stem
    output_dir = Path('.data/test_output')
    output_dir.mkdir(exist_ok=True, parents=True)
    MIN_SIZE=1000

    data = load_h5(h5_path, h5_key)
    voxel_size = read_h5_voxel_size(h5_path, h5_key)

    labels_to_meshes(
        data,
        voxel_size,
        callus_id,
        output_dir=output_dir,
        min_size=MIN_SIZE,
        extract_cells=True,
        extract_tissue=True,
        calculate_features=True,
    )

if __name__ == "__main__":
    main()
