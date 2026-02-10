# CallusSegmentation

![alt text](docs/img/logo.png)

A Python toolkit for automated image segmentation of plant callus tissue from Leica LIF microscopy files. It is meant as a tool to automate processes around the [PlantSeg](https://github.com/kreshuklab/plant-seg) segmentation workflow, and specifically designed for the segmentation of callus tissue. 

This package provides tools for converting multi-scene LIF files to OME-TIFF format, cleaning segmented images, running PlantSeg workflows, and interactively reviewing results.

## Features

- **LIF to OME-TIFF conversion**: Batch convert Leica LIF files with multiple scenes to standardized OME-TIFF format
- **PlantSeg integration**: Run deep learning-based segmentation workflows using [PlantSeg](https://github.com/kreshuklab/plant-seg)
- **Image cleaning**: Automated post-processing of segmented images with watershed segmentation and edge artifact removal
- **Interactive image review**: GUI for reviewing and validating segmentation results

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast dependency management. If you don't have uv installed, install it first, then clone the repository and install the package:

```bash
git clone git@github.com:RFroeling/CallusSegmentation.git
cd CallusSegmentation
uv sync
```

On Linux with GPU support, PyTorch will be installed with CUDA 12.6. On other platforms (macOS, Windows), CPU-only PyTorch is used.

## Configuration

Create a `.env` file in the project root to configure paths for different tasks:

```env
# For LIF to OME-TIFF conversion
LIF_PATH="/path/to/lif/files"
OME_TIFF_PATH="/path/to/output/ome-tiff"

# For edge cleaning
DATA_PATH="/path/to/h5/segmentation/results"
KEY="H5_uncleaned_dataset_key"
```

## Usage

The package provides a command-line interface with several subcommands:

### Convert LIF files to OME-TIFF

```bash
uv run run_segmentation.py --convert
```

Removes all LIF files in `LIF_PATH` (specified in `.env`) and saves their scenes as separate OME-TIFF files in `OME_TIFF_PATH`.

### Run PlantSeg segmentation

```bash
uv run run_segmentation.py --plantseg path/to/config.yaml
```

Execute PlantSeg segmentation workflow using a configuration YAML file. See [PlantSeg documentation](https://github.com/kreshuklab/plant-seg/tree/2.0.0rc12) for configuration details.

### Clean segmentation edges

```bash
uv run run_segmentation.py --clean
```

Post-process segmented images from `DATA_PATH` to remove edge artifacts using watershed segmentation and connected component analysis. Outputs cleaned H5 files and comparison visualizations.

### Interactive Image Review

```bash
uv run run_segmentation.py --review
```

Launch an interactive GUI for reviewing segmentation results. Use this to validate automated results and identify any artifacts.

### Inspect H5 Files

```bash
uv run run_segmentation.py --inspect
```

Print the structure and metadata of H5 segmentation files to the console for debugging and verification.

## Project Structure

```bash
CallusSegmentation/
├── segmentation/                     # Main package
│   ├── entry.py                      # CLI entry point
│   ├── core/                         # Core utilities
│   │   ├── cleaning.py               # Image cleaning functions
│   │   ├── io.py                     # File I/O operations
│   │   ├── logger.py                 # Logging configuration
│   │   └── views.py                  # Visualization tools
│   └── tasks/                        # Individual workflow tasks
│       ├── clean_edges.py            # Edge cleaning workflow
│       ├── convert_lif.py            # LIF to OME-TIFF conversion
│       ├── inspect_h5.py             # H5 file inspection
│       ├── move_files.py             # File management utilities
│       ├── review.py                 # Image review interface
│       └── run_plantseg_workflow.py  # PlantSeg integration
├── docs/                             # Documentation
├── run_segmentation.py               # Quick-start entry point
└── pyproject.toml                    # Project configuration & dependencies
```

## Dependencies

- **plantseg** (2.0.0rc12): Deep learning segmentation
- **bioio**: General image I/O support
- **bioio-lif** & **bioio-ome-tiff**: Format-specific readers/writers
- **h5py**: HDF5 file handling
- **scikit-image**: Image processing algorithms
- **torch** & **torchvision**: Deep learning framework
- **numpy**, **scipy**, **pandas**: Scientific computing
- **matplotlib**: Visualization

## Requirements

- Python ≥ 3.13
- macOS, Linux, or Windows

## License

This project is licensed under the [Creative Commons Attribution 4.0 International License](LICENSE).
