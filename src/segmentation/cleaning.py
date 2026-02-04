"""Module contains functions for removing unwanted labels in segmentation results."""

import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from skimage.measure import regionprops_table


def make_binary(dataset: np.ndarray, threshold: float=0) -> np.ndarray:
    """Convert labeled dataset to binary image.

    - Label = 0: Background
    - Label > 0: Foreground

    Args:
        dataset (np.ndarray): Labeled image where each cell has a unique integer label.
        threshold (float, optional): Threshold value for binarization. Defaults to 0.

    Returns:
        np.ndarray: Binary image where foreground voxels are True, background voxels are False.
    """
    binary = dataset > threshold
    
    return binary


def apply_watershed_segmentation(binary: np.ndarray, min_distance: int=4) -> np.ndarray:
    """Apply watershed segmentation to separate connected tissue regions.

    Performs a distance transformation on the binary mask, then identifies local maxima
    using a minumum distance parameter to generate seeds for the watershed algorithm.

    Adjust the min_distance parameter to control sensitivity in seed detection; a larger value results in 
    fewer seeds and potentially undersegmenatation, while a smaller value may lead to oversegmentation.

    Args:
        binary (np.ndarray): Binary mask of the tissue volume.
        min_distance (int): Minimum distance between local maxima for seed generation.

    Returns:
        np.ndarray: Labeled image where each tissue has a unique integer label.
    """
    dist = ndi.distance_transform_edt(binary)
    
    # Find coordinates of local maxima
    coords = peak_local_max(
        dist,
        min_distance=min_distance,
        labels=binary
    )

    # Create seeds (= local maxima) array for watershed
    markers = np.zeros_like(binary, dtype=int)
    for i, c in enumerate(coords, start=1):
        markers[tuple(c)] = i

    # Apply watershed algorithm
    tissue_labels = watershed(dist, markers, mask=binary)

    return tissue_labels


def calculate_border_touch_fraction(binary: np.ndarray, tissues: np.ndarray, props: pd.DataFrame) -> np.ndarray:
    """Calculate the fraction of each tissue that touches the volume boundary.
    
    For each tissue region, computes what proportion of its voxels are located
    on the boundary planes (first/last slices in z, y, x dimensions).
    
    Args:
        binary (np.ndarray): Binary mask of the tissue volume.
        tissues (np.ndarray): Labeled image where each tissue has a unique integer label.
        props (pd.DataFrame): DataFrame with tissue properties including 'label' column.
    
    Returns:
        np.ndarray: Array of touch fractions for each tissue, one value per tissue.
    """
    # Create a mask marking all voxels on the boundary of the volume (z, y, x faces)
    border = np.zeros_like(binary)
    border[[0,-1],:,:] = 1  # First and last z-planes
    border[:,[0,-1],:] = 1  # First and last y-planes
    border[:,:,[0,-1]] = 1  # First and last x-planes

    # Calculate what fraction of each tissue touches the border
    touch_frac = []
    for lab in props["label"]:
        vox = tissues == lab  # Get all voxels belonging to this tissue
        # Numerator: count voxels that are both in tissue AND on border
        # Denominator: count total voxels in tissue
        touch_frac.append((vox & border).sum() / vox.sum())
    
    return np.array(touch_frac)


def calculate_distance_to_center(binary: np.ndarray, props: pd.DataFrame) -> np.ndarray:
    """Calculate Euclidean distance from each tissue centroid to the volume center.
    
    Computes the 3D distance from each tissue's centroid to the geometric center
    of the volume using the formula: sqrt((z1-z2)^2 + (y1-y2)^2 + (x1-x2)^2).
    
    Args:
        binary (np.ndarray): Binary mask of the tissue volume.
        props (pd.DataFrame): DataFrame with tissue properties including centroid columns.
    
    Returns:
        np.ndarray: Array of distances for each tissue, one value per tissue.
    """
    # Calculate the geometric center of the volume
    center = np.array(binary.shape) / 2
    # Compute Euclidean distance from each tissue's centroid to the volume center
    distances = np.sqrt(
        (props["centroid-0"] - center[0])**2 +  # z-axis difference squared
        (props["centroid-1"] - center[1])**2 +  # y-axis difference squared
        (props["centroid-2"] - center[2])**2    # x-axis difference squared
    )
    
    return distances


def calculate_tissue_properties(binary: np.ndarray, tissues: np.ndarray) -> pd.DataFrame:
    """Calculates basic properties for each tissue region.

    Function returns basic metrics such as label, area, centroid, and bounding box,
    and more complex metrics like:
    - Border touch fraction: Proportion of tissue voxels touching volume boundaries.
    - Distance to center: Euclidean distance from tissue centroid to volume center.

    Args:
        binary (np.ndarray): Binary image where foreground voxels are True.
        tissues (np.ndarray): Labeled image where each tissue has a unique integer label.

    Returns:
        pd.DataFrame: DataFrame with properties for each tissue.
    """
    # Calculate 'standard' region properties
    props = pd.DataFrame(regionprops_table(
        tissues,
        properties=[
            "label",
            "area",
            "centroid",
            "bbox"
        ]
    ))
    
    # Calculate border touch fraction and distance to center
    props["touch_frac"] = calculate_border_touch_fraction(binary, tissues, props)
    props["dist_center"] = calculate_distance_to_center(binary, props)

    return props


def score_tissues(props: pd.DataFrame) -> pd.DataFrame:
    """Calculate a score for each tissue based on multiple criteria.

    Args:
        props (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: _description_
    """
    props["score"] = (
    props.area.rank(ascending=False) +
    props.dist_center.rank() +
    props.touch_frac.rank()
    )

    return props


def determine_main_tissue(props: pd.DataFrame) -> int:
    """Determine the main tissue by calculating a score for each tissue. 
    The tissue with the lowest score is selected.

    The score is computed as the sum of the ranks of each tissue in the following criteria:
    - Area (larger area = better rank)
    - Distance to center (closer to center = better rank)
    - Border touch fraction (lower fraction = better rank)
    
    Args:
        props (pd.DataFrame): DataFrame with tissue properties.
        
    Returns:
        int: Label of the main tissue.
    """
    scored_props = score_tissues(props)
    main_tissue = scored_props.sort_values("score").iloc[0].label

    return main_tissue


def create_mask(tissues: np.ndarray, main_tissue: int) -> np.ndarray:
    """Creates a binary mask for the main tissue.

    Checks each voxel in the tissues array and marks it as True if it belongs
    to the main tissue, otherwise marks it as False.

    Args:
        tissues (np.ndarray): Labeled image where each tissue has a unique integer label.
        main_tissue (int): Label of the main tissue.

    Returns:
        np.ndarray: Binary mask where voxels of the main tissue are True.
    """
    return tissues == main_tissue


def apply_mask(labels: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Apply a binary mask to the labeled image.

    Sets all voxels in the labels array to 0 where the corresponding voxel
    in the mask is False, effectively removing unwanted tissues.

    Args:
        labels (np.ndarray): Segmentatation output, NumPy array where each cell has a unique integer label.
        mask (np.ndarray): Binary mask where voxels to keep are True.

    Returns:
        np.ndarray: Cleaned labeled image with unwanted tissues removed.
    """
    cleaned_labels = labels.copy()
    cleaned_labels[~mask] = 0

    return cleaned_labels


def get_edge_labels(dataset: np.ndarray) -> set[int]:
    """Identify labels that touch the volume boundaries.
    
    Scans the boundary planes (first/last slices in z, y, x dimensions)
    to find all unique labels present on these edges.
    
    Args:
        dataset (np.ndarray): Labeled image where each tissue has a unique integer label.
    
    Returns:
        set[int]: Set of labels that touch the volume boundaries.
    """
    edge_labels = set()
    
    # Check all six faces of the 3D volume
    edge_labels.update(np.unique(dataset[0, :, :]))      # First z-plane
    edge_labels.update(np.unique(dataset[-1, :, :]))     # Last z-plane
    edge_labels.update(np.unique(dataset[:, 0, :]))      # First y-plane
    edge_labels.update(np.unique(dataset[:, -1, :]))     # Last y-plane
    edge_labels.update(np.unique(dataset[:, :, 0]))      # First x-plane
    edge_labels.update(np.unique(dataset[:, :, -1]))     # Last x-plane
    
    return edge_labels


def get_edge_label_neighbors(dataset: np.ndarray, edge_labels: set[int], strictness: float=2) -> set[int]:
    """Identify neighbor labels that should be removed based on surface contact.
    
    Collects all labels touching edge-bordering cells and evaluates whether they should
    be removed based on their surface contact patterns:
    - If a neighbor touches only edge-bordering labels, mark for removal
    - If a neighbor touches both edge and non-edge labels, compare surface areas using strictness parameter:
      - Remove if: surface_touching_edge > strictness * surface_touching_other
      - Keep otherwise
    
    Args:
        dataset (np.ndarray): Labeled image where each tissue has a unique integer label.
        edge_labels (set[int]): Set of labels touching the volume boundaries.
        strictness (float): Multiplier for removal threshold. Higher values are more conservative 
            (fewer labels removed). For example: strictness=1.0 removes if edge contact > other contact,
            strictness=2.0 removes only if edge contact is more than twice the other contact.
            Defaults to 2.0 (more conservative).
    
    Returns:
        set[int]: Set of neighbor labels that should be removed.
    """
    labels_to_remove = set()
    
    # Find all neighbors of edge labels by dilating edge regions
    edge_mask = np.isin(dataset, list(edge_labels))
    dilated_edge = ndi.binary_dilation(edge_mask)
    neighbor_labels = set(np.unique(dataset[dilated_edge & (dataset != 0)])) - edge_labels
    
    for neighbor in neighbor_labels:
        neighbor_mask = (dataset == neighbor)
        
        # Count face contacts with edge labels and other labels
        faces_with_edge = 0
        faces_with_other = 0
        
        # Check 6-connected neighbors (faces in 3D)
        for shift, axis in [((1, 0, 0), 0), ((-1, 0, 0), 0), 
                           ((0, 1, 0), 1), ((0, -1, 0), 1),
                           ((0, 0, 1), 2), ((0, 0, -1), 2)]:
            shifted_neighbor = np.roll(neighbor_mask, shift[axis], axis=axis)
            
            # Count adjacency to edge labels
            faces_with_edge += (shifted_neighbor & edge_mask).sum()
            
            # Count adjacency to other non-edge labels
            other_mask = (dataset != 0) & ~edge_mask & ~neighbor_mask
            faces_with_other += (shifted_neighbor & other_mask).sum()
        
        # Remove if only touches edge labels or touches edge more than others
        if faces_with_other == 0 or faces_with_edge > strictness * faces_with_other:
            labels_to_remove.add(neighbor)
    
    return labels_to_remove


def get_recursive_edge_label_neighbors(dataset: np.ndarray, edge_labels: set[int], strictness: float=2) -> set[int]:
    """Recursively identify labels to remove based on proximity to edge labels.
    
    Iteratively applies get_edge_label_neighbors, expanding the set of labels to remove
    by treating previously identified neighbors as new "edge labels" in subsequent iterations.
    Continues until the set of labels to remove no longer changes.
    
    Args:
        dataset (np.ndarray): Labeled image where each tissue has a unique integer label.
        edge_labels (set[int]): Set of labels touching the volume boundaries.
        strictness (float): Multiplier for removal threshold (see get_edge_label_neighbors).
            Defaults to 2.0.
    
    Returns:
        set[int]: Set of all labels that should be removed (includes edge labels and their neighbors).
    """
    labels_to_remove = edge_labels.copy()
    
    while True:
        # Find neighbors of current labels_to_remove set
        new_neighbors = get_edge_label_neighbors(dataset, labels_to_remove, strictness)
        
        # Add newly found neighbors to the removal set
        updated_labels = labels_to_remove | new_neighbors
        
        # If the set didn't change, we've reached convergence
        if updated_labels == labels_to_remove:
            break
        
        labels_to_remove = updated_labels
    
    return labels_to_remove



def remove_labels(dataset: np.ndarray, labels: set[int]) -> np.ndarray:
    """Remove all voxels belonging to labels in the provided set.
    
    Args:
        dataset (np.ndarray): Labeled image where each tissue has a unique integer label.
        labels (set[int]): Set of label values to remove.
    
    Returns:
        np.ndarray: Cleaned labeled image with specified labels removed.
    """
    cleaned = dataset.copy()
    
    for label in labels:
        if label == 0:  # Skip background
            continue
        cleaned[dataset == label] = 0
    
    return cleaned