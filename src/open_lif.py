"""Converts a (series of) .lif files to OME.tiff files"""

from pathlib import Path
import logging

import dotenv

from segmentation.models import read_lif, save_scenes_as_ome_tiff
from segmentation.logging_config import setup_logging

# Setup logger
logger = logging.getLogger(__name__)
setup_logging()

# Get environment variables


input = Path(".data/00_raw/250915_251013_NLS_001_128_CFW.ome.tiff")
out_dir = Path(".data/ome-tiff")

def main():
    if input.is_file():
        bioimg = read_lif(input)
        save_scenes_as_ome_tiff(bioimg, out_dir)
        logging.info(f'Done! \n')

    if input.is_dir():
        files = input.glob('*.lif')
        for file in files:
            logger.info(f'Converting the contents of {file.name}:')
            bioimg = read_lif(file)
            save_scenes_as_ome_tiff(bioimg, out_dir)
            logging.info(f'Done with {file}! \n')


if __name__ == '__main__':
    main()