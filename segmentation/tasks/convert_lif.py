"""Converts a (series of) .lif files to OME.tiff files"""

import logging
from pathlib import Path

from segmentation.core.io import read_lif, save_scenes_as_ome_tiff
from segmentation.core.logger import setup_logging

# Configure logger
logger = logging.getLogger(__name__)

def convert(file, output_dir):
    """Convert a single .lif file into OME-TIFF scenes.

    Args:
        file (Path): Path to the .lif file to convert.
        out_dir (Path): Directory where converted scenes will be saved.
    """
    logger.info(f'Converting the contents of {file.name}:')
    bioimg = read_lif(file)
    save_scenes_as_ome_tiff(bioimg, output_dir)
    logging.info(f'Done with {file.name}! \n')


def main(input_path: Path):
    """Entry point for the conversion task.

    If the configured `LIF_PATH` points to a file, convert that file. If it
    points to a directory, convert all ``*.lif`` files inside it.
    """

    if input_path.is_file():
        output_dir = input_path.parents[1] / 'ometiff'
        output_dir.mkdir(parents=True, exist_ok=True)
        convert(input_path, output_dir)

    if input_path.is_dir():
        files = input_path.glob('*.lif')
        output_dir = input_path.parents[0] / 'ometiff'
        output_dir.mkdir(parents=True, exist_ok=True)
        for file in files:
            convert(file, output_dir)
