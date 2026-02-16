"""Converts a (series of) .lif files to OME.tiff files"""

import logging
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from segmentation.core.io import read_lif, save_scenes_as_ome_tiff
from segmentation.core.logger import setup_logging

# Configure logger
logger = logging.getLogger(__name__)
setup_logging()

# Configure environment
load_dotenv()
input_env = getenv('LIF_PATH')
if not input_env:
    logger.error(
        "Environment variable LIF_PATH is not set. " \
        "Please configure .env with LIF_PATH pointing to your data directory."
        )
    raise SystemExit("Missing required environment variable: LIF_PATH")

output_env = getenv('OME_TIFF_PATH')
if not output_env:
    logger.error(
        "Environment variable OME_TIFF_PATH is not set. " \
        "Please configure .env with OME_TIFF_PATH pointing to your output directory."
    )
    raise SystemExit("Missing required environment variable: OME_TIFF_PATH")

input = Path(input_env)
out_dir = Path(output_env)


def convert(file, out_dir):
    """Convert a single .lif file into OME-TIFF scenes.

    Args:
        file (Path): Path to the .lif file to convert.
        out_dir (Path): Directory where converted scenes will be saved.
    """
    logger.info(f'Converting the contents of {file.name}:')
    bioimg = read_lif(file)
    save_scenes_as_ome_tiff(bioimg, out_dir)
    logging.info(f'Done with {file.name}! \n')


def main():
    """Entry point for the conversion task.

    If the configured `LIF_PATH` points to a file, convert that file. If it
    points to a directory, convert all ``*.lif`` files inside it.
    """
    if input.is_file():
        convert(input, out_dir)

    if input.is_dir():
        files = input.glob('*.lif')
        for file in files:
            convert(file, out_dir)
