from typing import Sequence
from pathlib import Path
import numpy as np
from scipy import ndimage

from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkCommonCore import VTK_INT
from vtkmodules.util import numpy_support
from vtkmodules.util.data_model import PolyData
from vtkmodules.vtkFiltersGeneral import vtkDiscreteMarchingCubes
from vtkmodules.vtkFiltersCore import vtkConnectivityFilter
from vtkmodules.vtkIOGeometry import vtkSTLWriter
from vtkmodules.vtkIOPLY import vtkPLYWriter


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

def save_mesh(polydata, filename: Path):
    if filename.suffix.lower() == ".stl":
        writer = vtkSTLWriter()
    elif filename.suffix.lower() == ".ply":
        writer = vtkPLYWriter()
    else:
        raise ValueError("Unsupported extension")

    writer.SetFileName(str(filename))
    writer.SetInputData(polydata)
    writer.Write()


def compute_label_bboxes(labels) -> list[tuple]:
    return ndimage.find_objects(labels)


def compute_label_sizes(labels: np.ndarray):

    flat = labels.ravel()
    sizes = np.bincount(flat)

    return sizes  # sizes[lbl] = voxel count


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