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

from segmentation.core.io import load_h5, read_h5_voxel_size
from segmentation.core.logger import setup_logging
from segmentation.core.meshes import (
    compute_label_bboxes,
    compute_label_sizes,
    extract_features,
    extract_label_surface,
    is_2d_label,
    is_too_small_label,
    keep_largest_component,
    numpy_to_vtk_image,
    save_mesh,
)

# Configure logging
logger = logging.getLogger(__name__)
setup_logging(logging.DEBUG)


def labels_to_meshes(
    labels: np.ndarray,
    voxel_size: Sequence[float],
    output_dir: Path,
    min_size: int,
    extract_cells: bool=True,
    extract_tissue: bool=True,
    calculate_features: bool=True,
) -> pd.DataFrame | None:
    """Extract and save surface meshes from a labeled volume.

    The function writes a tissue mesh file named ``tissue.ply`` (when
    ``extract_tissue`` is True) and a per-cell mesh file ``cell_XXXXX.ply``
    for each label that meets the heuristics.

    Args:
        labels (np.ndarray): 3D labeled image (ZYX).
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
    vtk_img = numpy_to_vtk_image(labels, voxel_size)

    bboxes = compute_label_bboxes(labels)
    sizes = compute_label_sizes(labels)

    unique_labels = np.unique(labels)
    unique_labels = unique_labels[unique_labels != 0]

    feature_rows = []

    if extract_tissue: # Extract whole tissue meshes

        logger.info("Extracting whole tissue...")

        binary = (labels > 0).astype(np.uint8)
        vtk_binary = numpy_to_vtk_image(binary, voxel_size)

        tissue_surface = extract_label_surface(vtk_binary, 1)

        tissue_surface = keep_largest_component(tissue_surface)

        if calculate_features:
            tissue_features = extract_features(tissue_surface)
            tissue_features.update({'Label': 'tissue'})
            feature_rows.append(tissue_features)

        save_mesh(tissue_surface, output_dir / "tissue.ply")

    if extract_cells: # Extract meshes for each cell

        for lbl in unique_labels:

            if is_2d_label(bboxes, lbl):
                logging.info(f"Skipping 2D artefact label {lbl}")
                continue

            if is_too_small_label(lbl, sizes, min_size):
                logging.info(f"Skipping tiny label {lbl}")
                continue

            logging.info(f"Extracting cell {lbl}")

            surface = extract_label_surface(vtk_img, lbl)

            if surface.GetNumberOfPoints() == 0: # Skip empty meshes
                continue

            if calculate_features:
                cell_features = extract_features(surface)
                cell_features.update({'Label': f'cell_{lbl:03d}'})
                feature_rows.append(cell_features)

            save_mesh(surface, output_dir / f"cell_{lbl:03d}.ply")
    
    if calculate_features:
        features = pd.DataFrame(feature_rows)
        logger.debug(f'\n{features.head()}')

        return features


def main():
    """Small test runner that converts a hard-coded test .h5 file to meshes.

    The function is primarily intended as a convenience for local testing and
    demonstration; paths and parameters are hard-coded.
    """
    h5_path = Path('.data/test_h5/251201_251215_Col-0_R01_W01_002.h5')
    h5_key = 'cleaned'
    output_dir = Path('.data/test_output')
    output_dir.mkdir(exist_ok=True, parents=True)
    MIN_SIZE=5000

    labels = load_h5(h5_path, h5_key)
    voxel_size = read_h5_voxel_size(h5_path, h5_key)

    features = labels_to_meshes(
        labels,
        voxel_size,
        output_dir=output_dir,
        min_size=MIN_SIZE,
        extract_cells=True,
        extract_tissue=True,
        calculate_features=False,
    )

if __name__ == "__main__":
    main()
