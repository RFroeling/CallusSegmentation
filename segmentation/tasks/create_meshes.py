from pathlib import Path
from typing import Sequence

import numpy as np
import logging

from segmentation.core.logger import setup_logging
from segmentation.core.io import load_h5, read_h5_voxel_size
from segmentation.core.meshes import (
    numpy_to_vtk_image,
    extract_label_surface,
    keep_largest_component,
    save_mesh,
    compute_label_bboxes,
    compute_label_sizes,
    is_2d_label,
    is_too_small_label,
)

# Configure logging
logger = logging.getLogger(__name__)
setup_logging()


def labels_to_meshes(
    labels: np.ndarray,
    voxel_size: Sequence[float],
    output_dir: Path,
    min_size: int,
    extract_cells: bool=True,
    extract_tissue: bool=True,
) -> None:
    vtk_img = numpy_to_vtk_image(labels, voxel_size)

    bboxes = compute_label_bboxes(labels)
    sizes = compute_label_sizes(labels)

    unique_labels = np.unique(labels)
    unique_labels = unique_labels[unique_labels != 0]

    if extract_tissue: # Extract whole tissue meshes

        logger.info("Extracting whole tissue...")

        binary = (labels > 0).astype(np.uint8)
        vtk_binary = numpy_to_vtk_image(binary, voxel_size)

        tissue_surface = extract_label_surface(vtk_binary, 1)

        tissue_surface = keep_largest_component(tissue_surface)

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

            save_mesh(surface, output_dir / f"cell_{lbl:05d}.ply")


def main():
    h5_path = Path('.data/test_h5/251201_251215_Col-0_R01_W01_002.h5')
    h5_key = 'cleaned'
    output_dir = Path('.data/test_output')
    output_dir.mkdir(exist_ok=True, parents=True)
    MIN_SIZE=5000

    labels = load_h5(h5_path, h5_key)
    voxel_size = read_h5_voxel_size(h5_path, h5_key)

    labels_to_meshes(
        labels,
        voxel_size,
        output_dir=output_dir,
        min_size=MIN_SIZE,
        extract_cells=True,
        extract_tissue=True,
    )

if __name__ == "__main__":
    main()
