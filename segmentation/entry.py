import argparse
from pathlib import Path


def create_parser():
    """Create and return the argument parser for the CLI."""
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
    """Start the reviewer to review files."""
    from segmentation.core.views import ImageReviewer

    viewer = ImageReviewer()
    viewer.run()


def clean_edges():
    """Cleans the boundary labels from segmented images"""
    from segmentation.tasks.clean_edges import main

    main()


def convert_images():
    """Convert .lif file(s) to .ome.tiff"""
    from segmentation.tasks.convert_lif import main

    main()


def inspect_file():
    """Inspect the content of user specified file(s)"""
    from segmentation.tasks.inspect_h5 import main

    main()

def run_plantseg_workflow(yaml_path: Path):
    """Run a PlantSeg workflow based on config YAML"""
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
