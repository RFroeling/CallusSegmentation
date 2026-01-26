from pathlib import Path
import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from skimage.measure import regionprops_table

data_path = Path('.data/02_labels')
key = 'segmentation'

def load_h5_dataset(path: Path, key: str) -> np.ndarray:
    """Load a dataset as a numpy array using context manager by given key from a .h5 file.

    Args: 
        path (Path): Path to the .h5 file.
        key (str): Key of the dataset to load.

    Returns: 
        np.ndarray: The loaded dataset.
    """
    with h5py.File(path, 'r') as f:
        dataset = np.array(f[key])

    return dataset


def display_XY_slice(dataset: np.ndarray, LUT: str ='gray', show=True) -> None:
    z = dataset.shape[0] // 2

    plt.imshow(dataset[z], cmap=LUT)
    plt.title('XY cross-section')
    if show:
        plt.show()


def display_YZ_slice(dataset: np.ndarray, LUT: str='gray', show=True) -> None:
    x = dataset.shape[1] // 2

    plt.imshow(dataset[:, x, :], cmap=LUT)
    plt.title('YZ cross-section')
    if show:
        plt.show()


def display_intensity_projection(dataset: np.ndarray, LUT: str ='gray', show=True) -> None:
    mip = dataset.max(axis=0)

    plt.imshow(mip, cmap=LUT)
    plt.title('Maximum Intensity Projection')
    if show:
        plt.show()


def make_binary(dataset: np.ndarray, threshold: float=0) -> np.ndarray:
    binary = dataset > threshold
    
    return binary


def apply_watershed_segmentation(binary: np.ndarray, min_distance: int=3) -> np.ndarray:
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
    # Create a mask marking all voxels on the boundary of the volume
    border = np.zeros_like(dataset)
    border[[0,-1],:,:] = 1  # First and last z-planes
    border[:,[0,-1],:] = 1  # First and last y-planes
    border[:,:,[0,-1]] = 1  # First and last x-planes
    
    # Find all unique labels in the dataset
    labels = np.unique(dataset)
    
    # Create output array
    cleaned = dataset.copy()
    
    # For each label, check if it touches the border
    for label in labels:
        if label == 0:  # Skip background
            continue
        
        label_mask = dataset == label
        # If any voxel of this label touches the border, remove the entire label
        if (label_mask & border).sum() > 0:
            cleaned[label_mask] = 0
    
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
    dataset = load_h5_dataset(path, key)
    binary = make_binary(dataset)
    tissues = apply_watershed_segmentation(binary)
    tissue_properties = calculate_tissue_properties(binary, tissues)
    main_tissue = determine_main_tissue(tissue_properties)

    mask = create_mask(tissues, main_tissue)
    masked_dataset = apply_mask(dataset, mask)
    cleaned_dataset = post_cleanup(masked_dataset)

    return dataset, cleaned_dataset


def create_random_colormap(num_labels: int) -> mcolors.ListedColormap:
    """Create a random colormap for labeled images.
    
    Generates a colormap where each label gets a unique random color,
    and the background (label 0) is set to black.
    
    Args:
        num_labels (int): Number of unique labels in the image (including background).
    
    Returns:
        mcolors.ListedColormap: Colormap with random colors for each label.
    """
    # Generate random colors for each label
    colors = np.random.rand(num_labels, 3)
    
    # Set the first color (label 0/background) to black
    colors[0] = [0, 0, 0]
    
    return mcolors.ListedColormap(colors)


def create_comparison_plot(dataset: np.ndarray, cleaned_dataset: np.ndarray, path: Path, save: bool=False) -> None:
    """Create comparison plots of original and cleaned datasets.
    
    Displays XY and YZ cross-sections of both the original and cleaned datasets
    side by side for visual comparison.
    
    Args:
        dataset (np.ndarray): Original dataset.
        cleaned_dataset (np.ndarray): Cleaned dataset.
        path (Path): Path to the original .h5 file (used for saving plots).
        save (bool): Whether to save the plot as a PNG file. Defaults to False.
    """
    _, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    z = dataset.shape[0] // 2
    x = dataset.shape[1] // 2
    
    # Create random colormap for labeled images
    cmap = create_random_colormap(cleaned_dataset.max() + 1)
    
    axes[0, 0].imshow(dataset[z], cmap=cmap)
    axes[0, 0].set_title('Original XY')
    
    axes[0, 1].imshow(dataset[:, x, :], cmap=cmap)
    axes[0, 1].set_title('Original YZ')
    
    axes[1, 0].imshow(cleaned_dataset[z], cmap=cmap)
    axes[1, 0].set_title('Cleaned XY')
    
    axes[1, 1].imshow(cleaned_dataset[:, x, :], cmap=cmap)
    axes[1, 1].set_title('Cleaned YZ')
    
    if save:
        save_path = data_path / 'comparison_plots'
        save_path.mkdir(exist_ok=True)
        plt.savefig(save_path / f'comparison_{path.stem}.png', dpi=300)
    else:
        plt.show()


def main():    
    for h5_file in data_path.glob('*.h5'):
        print(f"Processing {h5_file.name}...")
        segmentation, cleaned_segmentation = cleanup_segmentation(h5_file, key)
        create_comparison_plot(segmentation, cleaned_segmentation, h5_file, save=True)


if __name__ == "__main__":
    main()

# TODO
# - Remove border-closeness from scoring criterium and use as pre-cleanup step
# - Add CLI with argparse?
# - Add postcleanup with shared-surface / non-shared surface filter.
# - Identify border-touching labels, and remove other lables if they share more surface with border-touching labels than with main tissue