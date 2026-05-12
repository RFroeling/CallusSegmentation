"""Command-line entry point and dispatch for the segmentation utilities.

This module provides a small CLI used to call the different tools in the
`segmentation` package (reviewer GUI, cleaning routines, file conversion,
inspection helpers and PanSeg workflows).

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
        type=str,
        help="(opt.) Dataset key for segmentation. Defaults to 'segmentation'.",
        default="segmentation"
    )
    clean_parser.set_defaults(
        func=lambda args: run_clean_edges(args.input, args.key)
    )

    # ---------------- Convert ----------------
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert .lif images to OME-TIFF",
    )
    convert_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Either .LIF file or directory containing .LIF files.",
    )
    convert_parser.set_defaults(func=lambda args: run_convert_lif(args.input))

    # ---------------- Inspect ----------------
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect contents of .h5 file",
    )
    inspect_parser.set_defaults(func=lambda args: run_inspect_h5())

    # ---------------- PanSeg ----------------
    panseg_parser = subparsers.add_parser(
        "panseg",
        help="Run PanSeg workflow from YAML config file",
    )
    panseg_parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to YAML config file",
    )
    panseg_parser.add_argument(
        "--exe",
        type=Path,
        help="(opt.) Path to local PanSeg executable. Defaults to 'None'.",
        default=None,
    )
    panseg_parser.set_defaults(
        func=lambda args: run_panseg_workflow(args.config, args.exe)
    )

    # ---------------- Meshing ----------------
    meshing_parser = subparsers.add_parser(
        "meshing",
        help="Produce meshes from .h5 files",
    )
    meshing_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Either a .h5 file or directory containing .h5 files.",
    )
    meshing_parser.add_argument(
        "--key",
        type=str,
        help="(Opt.) Key to dataset that will be meshed. Defaults to 'cleaned'.",
        default="cleaned"
    )
    meshing_parser.set_defaults(func=lambda args: run_create_meshes(args.input, args.key))

    # ---------------- Headless ----------------
    headless_parser = subparsers.add_parser(
        "headless",
        help="Path to .LIF or directory containing .LIF(s)",
    )
    headless_parser.add_argument(
        "--input",
        type=Path,
        help="Path to LIF file or directory",
    )
    headless_parser.add_argument(
        "--exe",
        type=Path,
        help="(opt.) Path to local PanSeg executable. Defaults to 'None'.",
        default=None,
    )
    headless_parser.set_defaults(func=lambda args: run_headless(args.input, args.exe))
    
    return parser.parse_args()


# ---------------- Launchers ----------------


def launch_reviewer():
    """Start the reviewer GUI for manual image review.

    This function imports and launches :class:`segmentation.core.views.ImageReviewer`.
    """
    from segmentation.core.views import ImageReviewer

    viewer = ImageReviewer()
    viewer.run()


def run_clean_edges(h5_path, segmentation_key):
    """Run the boundary-cleaning task.

    Imports and runs :func:`segmentation.tasks.clean_edges.main`.
    """
    from segmentation.tasks.clean_edges import main

    main(h5_path, segmentation_key, move=False)


def run_convert_lif(input_path):
    """Run the image conversion task to produce OME-TIFF files.

    Imports and runs :func:`segmentation.tasks.convert_lif.main`.
    """
    from segmentation.tasks.convert_lif import main

    main(input_path)


def run_inspect_h5():
    """Run the interactive HDF5 inspection utility.

    Imports and runs :func:`segmentation.tasks.inspect_h5.main`.
    """
    from segmentation.tasks.inspect_h5 import main

    main()


def run_panseg_workflow(yaml_path: Path, panseg_path: str | Path | None = None):
    """Execute a PanSeg headless workflow from a YAML config file.

    Args:
        yaml_path (Path): Path to the PanSeg YAML configuration file.
        panseg_path (str | Path | None): Path to local PanSeg executable. Defaults to None.
    """
    from segmentation.tasks.panseg_workflow import run_panseg

    run_panseg(yaml_path, panseg_path)


def run_create_meshes(input_path: Path, segmentation_key: str):
    """Runs a meshing task on .h5 files in input_path.

    Args:
        input_path (Path): Directory containing .h5 files.
    """
    from segmentation.tasks.create_meshes import main

    main(input_path, segmentation_key)


def run_headless(input_path, panseg_path: str | Path | None = None):
    from segmentation.tasks.headless import main

    main(input_path, panseg_path)


def main():
    """Main function to parse arguments and call corresponding functionality."""
    setup_logging()
    args = create_parser()

    args.func(args) # Call the function attached to the selected subcommand


if __name__ == "__main__":
    main()
