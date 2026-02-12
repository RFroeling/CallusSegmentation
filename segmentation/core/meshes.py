"""VTK helper functions for converting labeled numpy volumes to surface meshes.
"""

import logging
from collections.abc import Sequence
from pathlib import Path

logger = logging.getLogger(__name__)

import numpy as np
from scipy import ndimage
from vtkmodules.util.data_model import PolyData
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import VTK_INT
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkFiltersCore import vtkConnectivityFilter, vtkMassProperties
from vtkmodules.vtkFiltersGeneral import vtkDiscreteMarchingCubes
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
    vtk_array = numpy_to_vtk(
        num_array=flat,
        deep=True,
        array_type=VTK_INT,
    )

    img.GetPointData().SetScalars(vtk_array)

    return img


def extract_label_surface(image, label) -> PolyData:
    """Extract the surface mesh for a single label using discrete marching cubes.

    Args:
        image (vtkImageData): Input volume where scalar values encode labels.
        label (int): Label value for which the surface should be extracted.

    Returns:
        PolyData: VTK polydata containing the extracted surface for ``label``.
    """
    dmc = vtkDiscreteMarchingCubes()
    dmc.SetInputData(image)
    dmc.SetValue(0, int(label))
    dmc.Update()

    return dmc.GetOutput()


def keep_largest_component(polydata: PolyData) -> PolyData:
    """Return a new PolyData containing only the largest connected component.

    This uses a connectivity filter to identify connected regions and keeps
    the single largest region by surface connectivity.

    Args:
        polydata (PolyData): Input mesh to be filtered.

    Returns:
        PolyData: Mesh containing only the largest connected component.
    """
    connectivity = vtkConnectivityFilter()
    connectivity.SetInputData(polydata)
    connectivity.SetExtractionModeToLargestRegion()
    connectivity.Update()

    return connectivity.GetOutput()


def save_mesh(polydata, filename: Path):
    """Write a mesh to disk in STL or PLY format.

    The writer is selected based on the file extension of ``filename``.

    Args:
        polydata (PolyData): Mesh to write.
        filename (Path): Destination path. Supported extensions: ``.stl``, ``.ply``.

    Raises:
        ValueError: If the provided filename has an unsupported extension.
    """
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
    """Compute bounding boxes for all labeled objects in a volume.

    The returned list is indexable by ``label-1``.

    Args:
        labels (np.ndarray): Integer labeled volume where 0 is background.

    Returns:
        list[tuple]: List of slice tuples describing object bounding boxes.
    """
    return ndimage.find_objects(labels)


def compute_label_sizes(labels: np.ndarray):
    """Compute the voxel count for each label in the labeled volume.

    The return value is a 1D array such that ``sizes[label]`` gives the
    number of voxels belonging to ``label``. Note that ``sizes[0]`` is the
    background count.

    Args:
        labels (np.ndarray): Integer labeled volume.

    Returns:
        np.ndarray: 1D array of counts per label.
    """
    flat = labels.ravel()
    sizes = np.bincount(flat)

    return sizes  # sizes[lbl] = voxel count


def is_2d_label(bboxes: list[tuple], lbl: int) -> bool:
    """Returns True if the given label only spans one voxel in at least one dimension (Z, Y, or X).

    Args:
        bboxes (list[tuple]): Bounding boxes for each label.
        lbl (int): Label value to check.

    Returns:
        bool: True if ``lbl`` is 2D and should be excluded.
    """
    bbox = bboxes[lbl - 1]  # labels assumed 1..N

    if bbox is None:
        return True

    dz = bbox[0].stop - bbox[0].start
    dy = bbox[1].stop - bbox[1].start
    dx = bbox[2].stop - bbox[2].start

    return (dz == 1) or (dy == 1) or (dx == 1)


def is_too_small_label(lbl: int, sizes: np.ndarray, min_voxels: int) -> bool:
    """Return True when a label is smaller than a minimum voxel threshold.

    If the label index is out-of-range for the provided ``sizes`` array the
    function conservatively returns True.

    Args:
        lbl (int): Label value to check.
        sizes (np.ndarray): 1D array where ``sizes[label]`` gives voxel count.
        min_voxels (int): Minimum allowed voxel count.

    Returns:
        bool: True if ``lbl`` should be considered too small and excluded.
    """
    if lbl >= len(sizes):
        return True
    return sizes[lbl] < min_voxels


def compute_volume_area(polydata):
    mass = vtkMassProperties()
    mass.SetInputData(polydata)
    mass.Update()
    return mass.GetVolume(), mass.GetSurfaceArea()


def compute_principal_axes(polydata):

    pts = vtk_to_numpy(polydata.GetPoints().GetData())
    centered = pts - pts.mean(axis=0)

    cov = np.cov(centered.T)
    eigvals, eigvecs = np.linalg.eigh(cov)

    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    axis_lengths = 2 * np.sqrt(np.maximum(eigvals, 0))

    return eigvals, eigvecs, axis_lengths


def compute_sphericity(volume, area):
    return (np.pi ** (1/3) * (6 * volume) ** (2/3)) / area


def compute_bbox(polydata) -> tuple:
    bounds = polydata.GetBounds()
    dx = bounds[1] - bounds[0]
    dy = bounds[3] - bounds[2]
    dz = bounds[5] - bounds[4]
    
    return (dx, dy, dz)


def extract_features(polydata):

    volume, area = compute_volume_area(polydata)

    bounds = compute_bbox(polydata)

    sphericity = compute_sphericity(volume, area)

    logger.debug(f'Sanity check: Coordinates of polydata are {polydata.GetPoint(0)}')

    return {
        "surface_area": area,
        "volume": volume,
        "bbox_dx": bounds[0],
        "bbox_dy": bounds[1],
        "bbox_dz": bounds[2],
        "sphericity": sphericity,
        "n_vertices": polydata.GetNumberOfPoints(),
        "n_faces": polydata.GetNumberOfCells(),
    }


