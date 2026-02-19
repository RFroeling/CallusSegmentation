
# CallusSegmentation

![alt text](docs/img/logo.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**CallusSegmentation** is a Python toolkit for automated image segmentation of plant callus tissue from Leica LIF microscopy files. It automates the [PlantSeg](https://github.com/kreshuklab/plant-seg) segmentation workflow, with a focus on callus tissue.

The toolkit provides:

- **LIF to OME-TIFF conversion**: Batch convert Leica LIF files (multi-scene) to OME-TIFF
- **PlantSeg integration**: Run deep learning-based segmentation workflows (headless or interactive)
- **Automated cleaning**: Remove edge artifacts and unwanted labels from segmentations
- **3D mesh extraction**: Generate meshes and calculate features for segmented tissues/cells
- **Interactive review**: GUI for reviewing and validating segmentation results

See the full [documentation](https://rfroeling.github.io/CallusSegmentation/).

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast dependency management. If you don't have uv installed, install it first, then clone the repository and install dependencies:

```bash
git clone https://github.com/RFroeling/CallusSegmentation.git
cd CallusSegmentation
uv sync
```

### PlantSeg dependencies

There seems to be an issue with accessing the PlantSeg dependencies through uv. A simple workaround is to make sure there's also a proper [PlantSeg installation](https://kreshuklab.github.io/plant-seg/latest/chapters/getting_started/installation/) available on your machine.

> PlantSeg requires Pytorch; on Linux with GPU, CUDA 12.6 is used; otherwise, CPU-only PyTorch is installed.

## Usage

The toolkit provides a headless workflow and access to the individual tasks through a command-line interface with several subcommands.

### Headless workflow

The toolkit is designed to run in a full headless mode, allowing (near) full-automatic analyis of callus images.

```bash
uv run run_segmentation.py headless --input <path/to/lif>
```

The provided path can either point to a single LIF file, or a directory containing multiple LIF files (these will all be processed). There should be PlantSeg [config YAML](https://kreshuklab.github.io/plant-seg/latest/chapters/workflow_gui/) present in the same directory as the LIF input file(s). The minimal output requirement for the config YAML is saving the label layer produces by PlantSeg with the key `segmentation` as a .h5.

#### File Structure After Headless Workflow

When running the full workflow in headless mode, the following directory structure is created (relative to your input directory):

```text
img/
├── lif/           # Original LIF files (input)
├── ometiff/       # OME-TIFF files (converted from LIF)
├── h5/
│   ├── raw/       # Raw PlantSeg segmentation outputs (.h5)
│   └── clean/     # Cleaned segmentations (edge artifacts removed)
├── mesh/          # 3D mesh files (PLY format)
└── num/           # Extracted mesh features (CSV)
```

Typical output after running the headless workflow:

- `img/lif/`: Input LIF files (moved/copied here)
- `img/ometiff/`: OME-TIFF files for PlantSeg
- `img/h5/raw/`: Raw PlantSeg segmentation results
- `img/h5/clean/`: Cleaned segmentations (no edge artifacts)
- `img/mesh/<sample_id>/`: 3D meshes for tissue and cells (PLY)
- `img/num/features.csv`: Table of mesh features for all samples

### Tasks

It is also possible to run individual tasks:

```bash
uv run run_segmentation.py <task>
```

This works with any of these tasks:

- `convert`: Converts LIF files to OME-TIFF format. Input can be a file or directory.
- `plantseg`: Runs PlantSeg segmentation workflow using a YAML configuration.
- `clean`: Removes edge artifacts and unwanted labels from segmentations.
- `meshing`: Extracts 3D meshes and features from cleaned segmentations.
- `review`: Launches a GUI for reviewing segmentation results.
- `inspect`: Prints structure and metadata of H5 segmentation files.

For a more detailed description on runnings tasks, use the `-h` flag:

```bash
uv run run_segmentation.py <task> -h
```

## Project Structure

```text
CallusSegmentation/
├── segmentation/           # Main package
│   ├── entry.py            # CLI entry point
│   ├── core/               # Core utilities (I/O, cleaning, meshes, etc.)
│   └── tasks/              # Workflow tasks (convert, clean, mesh, etc.)
├── run_segmentation.py     # Main script for CLI
├── docs/                   # Documentation
├── pyproject.toml          # Project config & dependencies
└── ...
```

## Dependencies

- **plantseg** (2.0.0rc12): Deep learning segmentation
- **VTK**: Meshing
- **bioio**, **bioio-lif**, **bioio-ome-tiff**: Image I/O
- **h5py**: HDF5 file handling
- **scikit-image**: Image processing
- **torch**, **torchvision**: Deep learning
- **numpy**, **scipy**, **pandas**: Scientific computing
- **matplotlib**: Visualization

## License

This project is licensed under the [MIT](LICENSE) license.
