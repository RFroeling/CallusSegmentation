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


def create_parser():
    """Create and return the argument parser for the CLI.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    arg_parser = argparse.ArgumentParser()
    mode = arg_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--review",
        "-r",
        action='store_true',
        help="Launch an instance of the Image Reviewer.",
    )
    mode.add_argument(
        "--clean",
        "-c",
        action='store_true',
        help="Cleans images (Specify Path and key in .env file.)",
    )
    mode.add_argument(
        "--convert",
        "-cv",
        action='store_true',
        help="Converts .lif images to OME-tiff (Specify Paths in .env file.)",
    )
    mode.add_argument(
        "--inspect",
        "-i",
        action='store_true',
        help="Inspects the contents of .h5 file, prints to console.",
    )
    mode.add_argument(
        "--plantseg",
        "-p",
        type=Path,
        help="Run PlantSeg workflow from YAML config file",
    )
    # Add arguments here if neccesary
    return arg_parser.parse_args()


def launch_reviewer():
    """Start the reviewer GUI for manual image review.

    This function imports and launches :class:`segmentation.core.views.ImageReviewer`.
    """
    from segmentation.core.views import ImageReviewer

    viewer = ImageReviewer()
    viewer.run()


def clean_edges():
    """Run the boundary-cleaning task.

    Imports and runs :func:`segmentation.tasks.clean_edges.main`.
    """
    from segmentation.tasks.clean_edges import main

    main()


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


def main():
    """Main function to parse arguments and call corresponding functionality."""
    args = create_parser()

    if args.review:
        launch_reviewer()
    elif args.clean:
        clean_edges()
    elif args.convert:
        convert_images()
    elif args.inspect:
        inspect_file()
    elif args.plantseg:
        run_plantseg_workflow(args.plantseg)
    else:
        raise ValueError(
            "Wrong arguments. Run `segmentation -h` to see the available options."
        )


if __name__ == "__main__":
    main()
