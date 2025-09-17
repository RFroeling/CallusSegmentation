# CallusSegmentation

A set of [ImageJ](https://imagej.nih.gov/ij/) macros for automated extraction, cleaning, and segmentation of microscopy images from Leica LIF files. The workflow converts LIF files to TIFF stacks, applies cleaning and masking, and generates quality control montages.

## Features

- **Batch extraction** of TIFF images from LIF files using Bio-Formats.
- **Automated cleaning** and masking of image stacks.
- **Montage generation** for quality control.
- **Logging** of all export actions for reproducibility.

## Folder Structure

```bash
callussegmentation/
├── 00_ExtractTIF-Folder.ijm      # Batch extract TIFFs from all LIF files in a folder
├── 00_ExtractTIF-SingleFile.ijm  # Extract TIFFs from a single LIF file
├── 01_CleanStack.ijm             # Clean and mask TIFF stacks, generate montages
├── .gitignore
├── LICENSE
└── README.md 
```

## Usage

### 1. Extract TIFFs from LIF files

- **Batch mode:**  
  Run [`00_ExtractTIF-Folder.ijm`](00_ExtractTIF-Folder.ijm) in ImageJ/Fiji.  
  Select the folder containing `.lif` files.  
  Output TIFFs and logs will be saved in a new `01_tif` folder.

- **Single file mode:**  
  Run [`00_ExtractTIF-SingleFile.ijm`](00_ExtractTIF-SingleFile.ijm) in ImageJ/Fiji.  
  Select a `.lif` file.  
  Output TIFFs and logs will be saved in a new `01_tif` folder.

### 2. Clean and Mask TIFF Stacks

- Run [`01_CleanStack.ijm`](01_CleanStack.ijm) in ImageJ/Fiji.
- Select the parent directory containing the `01_tif` folder.
- Cleaned stacks, masks, and montages will be saved in a new `02_cleaned` folder.

## Requirements

- [ImageJ/Fiji](https://fiji.sc/)
- [Bio-Formats plugin](https://www.openmicroscopy.org/bio-formats/downloads/)

## License

This project is licensed under the [Creative Commons Attribution 4.0 International License](LICENSE).
