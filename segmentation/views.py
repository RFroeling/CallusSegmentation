"""Module containing the neccessary functions for visualization of segmentation cleanups."""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


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


def cleaning_comparison_plot(dataset: np.ndarray, cleaned_dataset: np.ndarray, path: Path, save: bool=False) -> None:
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
        save_path = path.parent / 'comparison_plots'
        save_path.mkdir(exist_ok=True)
        print(f'Saving to: {save_path}')
        plt.savefig(save_path / f'comparison_{path.stem}.png', dpi=300)
    else:
        plt.show()
