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


def resolve_dirs(input_path: Path, headless: bool=False) -> Path:
    if not headless:
        base_dir = input_path.parent
    else: # headless
        base_dir = input_path.parents[3]

    base_dir.mkdir(parents=True, exist_ok=True)

    return base_dir


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
    base_dir: Path,
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
    mesh_dir = base_dir / 'mesh' / callus_id
    # num_dir = base_dir / 'num'
    mesh_dir.mkdir(parents=True, exist_ok=True)
    # num_dir.mkdir(parents=True, exist_ok=True)

    vtk_img = numpy_to_vtk_image(data, voxel_size)
    logger.info(f"Extracting meshes for callus '{callus_id}':\n")

    # Analysis only on unique labels, that are no artefacts (small, 2D labels)
    filtered_labels = filter_unique_labels(data, min_size=min_size)

    age = calculate_age_from_id(callus_id)
    contact_pairs, background_contact, neighbor_count = compute_contacts_and_neighbors(data, filtered_labels, voxel_size)

    feature_rows = []

    if extract_tissue: # Extract whole tissue meshes

        logger.info("Extracting whole tissue")

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

        save_mesh(tissue_surface, mesh_dir / "tissue.ply")

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

            save_mesh(surface, mesh_dir / f"cell_{lbl:03d}.ply")
    
    logger.info(f"Extracted {len(filtered_labels)} meshes from '{callus_id}'\n")

    # if calculate_features:
    #     features = pd.DataFrame(feature_rows)
        # output_path = num_dir / f'{callus_id}_features.csv'
        # save_df_to_csv(features, output_path)
    if calculate_features:
        features = pd.DataFrame(feature_rows)
        logger.debug(f'\n{features.head()}')
        return features

    return None


def h5_to_mesh(h5_path: Path, 
               cleaned_key: str, 
               base_dir: Path,
               min_size: int
    ) -> pd.DataFrame | None:

    data = load_h5(h5_path, cleaned_key)
    voxel_size = read_h5_voxel_size(h5_path, cleaned_key)
    callus_id = h5_path.stem

    features = labels_to_meshes(
        data,
        voxel_size,
        callus_id,
        base_dir=base_dir,
        min_size=min_size,
        extract_cells=True,
        extract_tissue=True,
        calculate_features=True,
    )
    
    return features


def main(input_path: Path, cleaned_key: str, headless: bool=True, min_size: int=1000):
    """Convert .h5 datasets to meshes. Accepts file or directory."""
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    # Determine files
    if input_path.is_file():
        files = [input_path]
    else:
        files = list(input_path.glob("*.h5"))
        if not files:
            logger.warning(f"No .h5 files found in directory: {input_path}")
            return []

    # Global output
    base_dir = resolve_dirs(files[0], headless=headless) # Check base for first file
    output_path = base_dir / "num" / f"features_{base_dir.name}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    first = True
    processed = []

    for file in files:
        try:
            if file.suffix.lower() != ".h5":
                raise ValueError(f"{file} is not a .h5 dataset")

            features = h5_to_mesh(
                h5_path=file,
                cleaned_key=cleaned_key,
                base_dir=base_dir,
                min_size=min_size
            )

            if features is not None and not features.empty:
                features.to_csv(
                    output_path,
                    mode="w" if first else "a",
                    header=first,
                    index=False
                )
                first = False

            processed.append(file)

        except Exception:
            logger.exception(f"Failed processing {file}")
    
    if first:
        logger.warning("No features were extracted from any dataset")
    else:
        logger.info(f"Combined feature table written to: {output_path}")
    return processed

