from pathlib import Path
from typing import Sequence

import numpy as np
import h5py
from scipy import ndimage
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkCommonCore import VTK_INT
from vtkmodules.util import numpy_support
from vtkmodules.util.data_model import PolyData
from vtkmodules.vtkFiltersGeneral import vtkDiscreteMarchingCubes
from vtkmodules.vtkFiltersCore import vtkConnectivityFilter
from vtkmodules.vtkIOGeometry import vtkSTLWriter
from vtkmodules.vtkIOPLY import vtkPLYWriter

MIN_SIZE=5000

def load_h5(path: Path, key: str | None) -> np.ndarray:
    """Load a dataset as a numpy array using context manager by given key from a .h5 file.

    Args: 
        path (Path): Path to the .h5 file.
        key (str): Key of the dataset to load.

    Returns: 
        np.ndarray: The loaded dataset.
        
    Raises:
        KeyError: If the key doesn't exist in the file.
        FileNotFoundError: If the file doesn't exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if key is None or key == "":
        raise ValueError("Key is required to load a dataset from a .h5 file")

    with h5py.File(path, 'r') as f:
        if key not in f:
            available_keys = list(f.keys())
            raise KeyError(f"Key '{key}' not found in {path.name}. Available keys: {available_keys}")
        dataset = np.array(f[key])

    return dataset


def read_h5_voxel_size(
    path: Path,
    key: str | None,
) -> Sequence[float]:
    """
    Load the voxel size from a h5 file.

    Args:
        path (Path): path to the h5 file
        key (str | None): key of the dataset in the h5 file.

    Returns:
        np.ndarray: Voxel size (ZYX) represented as a numpy array

    Raises:
        ValueError: If key is not present in .h5 dataset.
    """
    with h5py.File(path, "r") as f:
        data = f[key]
        
        if not isinstance(data, h5py.Dataset):
            raise ValueError(f"'{key}' is not a h5py.Dataset.")
    
        voxel_size = data.attrs.get("element_size_um", None)

    return voxel_size


def compute_label_bboxes(labels) -> list[tuple]:
    return ndimage.find_objects(labels)


def is_2d_label(bboxes: list[tuple], lbl: int) -> bool:
    """Returns True if the given label only spans one voxel in at least one dimension (Z, Y, or X).
    """
    bbox = bboxes[lbl - 1]  # labels assumed 1..N

    if bbox is None:
        return True

    dz = bbox[0].stop - bbox[0].start
    dy = bbox[1].stop - bbox[1].start
    dx = bbox[2].stop - bbox[2].start

    return (dz == 1) or (dy == 1) or (dx == 1)


def is_too_small_label(lbl: int, sizes: np.ndarray, min_voxels: int) -> bool:
    if lbl >= len(sizes):
        return True
    return sizes[lbl] < min_voxels


def compute_label_sizes(labels: np.ndarray):

    flat = labels.ravel()
    sizes = np.bincount(flat)

    return sizes  # sizes[lbl] = voxel count


def numpy_to_vtk_image(data: np.ndarray, voxel_size: Sequence[float]) -> vtkImageData:
    """Builds an instance of vtkImageData from a numpy array with given voxel size.

    Args:
        data (np.ndarray): Label image as a numpy.ndarray
        voxel_size (np.ndarray): 1D numpy array with voxel size (zyx) in um.

    Returns:
        vtkImageData: VTK representation of 3D numpy array.
    """
    img = vtkImageData()

    depth, height, width = data.shape

    img.SetDimensions(width, height, depth)
    img.SetSpacing(voxel_size[::-1])  # vtk uses (x,y,z)
    img.SetOrigin(0, 0, 0)

    flat = data.ravel() # Flatten 3D array to 1D array > required for numpy_to_vtk()
    vtk_array = numpy_support.numpy_to_vtk(
        num_array=flat,
        deep=True,
        array_type=VTK_INT,
    )

    img.GetPointData().SetScalars(vtk_array)

    return img


# ----------------------------
# Extract surface for a given label
# ----------------------------

def extract_label_surface(image, label) -> PolyData:
    dmc = vtkDiscreteMarchingCubes()
    dmc.SetInputData(image)
    dmc.SetValue(0, int(label))
    dmc.Update()

    return dmc.GetOutput()


# ----------------------------
# Keep only largest connected component
# ----------------------------

def keep_largest_component(polydata: PolyData) -> PolyData:

    connectivity = vtkConnectivityFilter()
    connectivity.SetInputData(polydata)
    connectivity.SetExtractionModeToLargestRegion()
    connectivity.Update()

    return connectivity.GetOutput()



# ----------------------------
# Save mesh
# ----------------------------

def save_mesh(polydata, filename):

    filename = Path(filename)

    if filename.suffix.lower() == ".stl":
        writer = vtkSTLWriter()
    elif filename.suffix.lower() == ".ply":
        writer = vtkPLYWriter()
    else:
        raise ValueError("Unsupported extension")

    writer.SetFileName(str(filename))
    writer.SetInputData(polydata)
    writer.Write()


# ----------------------------
# MAIN PIPELINE
# ----------------------------

def labels_to_meshes(
    labels: np.ndarray,
    voxel_size: Sequence[float],
    output_dir: Path,
    min_size: int,
    extract_cells: bool=True,
    extract_tissue: bool=True,
):

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    vtk_img = numpy_to_vtk_image(labels, voxel_size)

    bboxes = compute_label_bboxes(labels)
    sizes = compute_label_sizes(labels)

    unique_labels = np.unique(labels)
    unique_labels = unique_labels[unique_labels != 0]

    # =====================
    # WHOLE TISSUE MESH
    # =====================

    if extract_tissue:

        print("Extracting whole tissue...")

        binary = (labels > 0).astype(np.uint8)
        vtk_binary = numpy_to_vtk_image(binary, voxel_size)

        tissue_surface = extract_label_surface(vtk_binary, 1)

        tissue_surface = keep_largest_component(tissue_surface)

        save_mesh(tissue_surface, output_dir / "tissue.ply")

    # =====================
    # INDIVIDUAL CELLS
    # =====================

    if extract_cells:

        for lbl in unique_labels:

            if is_2d_label(bboxes, lbl):
                print(f"Skipping 2D artefact label {lbl}")
                continue

            if is_too_small_label(lbl, sizes, min_size):
                print(f"Skipping tiny label {lbl}")
                continue

            print(f"Extracting cell {lbl}")

            surface = extract_label_surface(vtk_img, lbl)

            if surface.GetNumberOfPoints() == 0:
                continue

            save_mesh(surface, output_dir / f"cell_{lbl:05d}.ply")


# ----------------------------
# Example usage
# ----------------------------

if __name__ == "__main__":

    h5_path = Path('.data/test_h5/251201_251215_Col-0_R01_W01_002.h5')
    h5_key = 'cleaned'
    output_dir = Path('.data/test_output')

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
