"""Command-line entry point and dispatch for the segmentation utilities.

This module provides a small CLI used to call the different tools in the
`segmentation` package (reviewer GUI, cleaning routines, file conversion,
inspection helpers and PlantSeg workflows).

The module exposes a `main()` function intended to be used as a console
entry point.

Google-style docstrings are used for functions in this module.
"""

import argparse
from pathlib import Path

from segmentation.core.logger import setup_logging


def create_parser():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---------------- Review ----------------
    review_parser = subparsers.add_parser(
        "review",
        help="Launch an instance of the Image Reviewer.",
    )
    review_parser.set_defaults(func=lambda args: launch_reviewer())

    # ---------------- Clean ----------------
    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean images (requires input path and segmentation key)",
    )
    clean_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Directory containing images",
    )
    clean_parser.add_argument(
        "--key",
        required=True,
        help="Dataset key for segmentation",
    )
    clean_parser.set_defaults(
        func=lambda args: clean_edges(args.input, args.key)
    )

    # ---------------- Convert ----------------
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert .lif images to OME-TIFF",
    )
    convert_parser.set_defaults(func=lambda args: convert_images())

    # ---------------- Inspect ----------------
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect contents of .h5 file",
    )
    inspect_parser.set_defaults(func=lambda args: inspect_file())

    # ---------------- PlantSeg ----------------
    plantseg_parser = subparsers.add_parser(
        "plantseg",
        help="Run PlantSeg workflow from YAML config file",
    )
    plantseg_parser.add_argument(
        "config",
        type=Path,
        help="Path to YAML config file",
    )
    plantseg_parser.set_defaults(
        func=lambda args: run_plantseg_workflow(args.config)
    )

    # ---------------- Meshing ----------------
    meshing_parser = subparsers.add_parser(
        "meshing",
        help="Produce meshes from .h5 files",
    )
    meshing_parser.set_defaults(func=lambda args: create_meshes())

    # ---------------- Headless ----------------
    headless_parser = subparsers.add_parser(
        "headless",
        help="Path to .LIF or directory containing .LIF(s)",
    )
    headless_parser.add_argument(
        "path",
        type=Path,
        help="Path to LIF file or directory",
    )
    headless_parser.set_defaults(func=lambda args: headless_workflow(args.path))
    
    return parser.parse_args()


def launch_reviewer():
    """Start the reviewer GUI for manual image review.

    This function imports and launches :class:`segmentation.core.views.ImageReviewer`.
    """
    from segmentation.core.views import ImageReviewer

    viewer = ImageReviewer()
    viewer.run()


def clean_edges(h5_path, segmentation_key):
    """Run the boundary-cleaning task.

    Imports and runs :func:`segmentation.tasks.clean_edges.main`.
    """
    from segmentation.tasks.clean_edges import main

    main(h5_path, segmentation_key)


def convert_images():
    """Run the image conversion task to produce OME-TIFF files.

    Imports and runs :func:`segmentation.tasks.convert_lif.main`.
    """
    from segmentation.tasks.convert_lif import main

    main()


def inspect_file():
    """Run the interactive HDF5 inspection utility.

    Imports and runs :func:`segmentation.tasks.inspect_h5.main`.
    """
    from segmentation.tasks.inspect_h5 import main

    main()

def run_plantseg_workflow(yaml_path: Path):
    """Execute a PlantSeg headless workflow from a YAML config file.

    Args:
        yaml_path (Path): Path to the PlantSeg YAML configuration file.
    """
    from segmentation.tasks.run_plantseg_workflow import main

    main(yaml_path)


def create_meshes():
    """Runs a meshing task on .h5 files in input_path.

    Args:
        input_path (Path): Directory containing .h5 files.
    """
    from segmentation.tasks.create_meshes import main

    main()


def headless_workflow(path):
    # TODO
    # Implement correct file handling; fixed relative paths in workflow, 
    # CLI paths (and keys) for separate tasks
    pass


def main():
    """Main function to parse arguments and call corresponding functionality."""
    setup_logging()
    args = create_parser()

    args.func(args) # Call the function attached to the selected subcommand


if __name__ == "__main__":
    main()
