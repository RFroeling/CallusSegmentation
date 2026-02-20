from pathlib import Path
import logging
import shutil
import yaml

from segmentation.tasks import (
    convert_lif,
    plantseg_workflow)

# Configure logging
logger = logging.getLogger(__name__)


def find_yaml(base_dir: Path) -> Path:
    files = [file for file in base_dir.rglob("*.yaml") if "workflow" in file.name.lower()]

    if len(files) == 1:
        return files[0]
    elif len(files) == 0:
        raise FileNotFoundError(f"No YAML config file found in {base_dir}")
    else:
        raise RuntimeError(f"Multiple YAML config files found in {base_dir}: {files} /n \
                           Make sure there's only one config YAML in {base_dir}")
    

def configure_yaml(
    yaml_path: Path | str,
    input_dir: Path | str,
    export_dir: Path | str,
):
    """
    Update PlantSeg YAML so all export_directory* fields point to one folder.

    Args:
        yaml_path (Path | str): Path to the PlantSeg YAML config file
        input_path (Path | str): Path to input images (file or directory)
        export_directory (Path | str): Single output directory used for ALL exports
    """
    yaml_path = Path(yaml_path)
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    # Load YAML
    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)

    if "inputs" not in config or not config["inputs"]:
        raise ValueError("Invalid PlantSeg YAML: missing 'inputs' section")

    input_block = config["inputs"][0]

    # Update input path
    input_block["input_path"] = str(input_dir)

    # Find export_directory keys automatically
    export_keys = [k for k in input_block.keys() if k.startswith("export_directory")]

    if not export_keys:
        raise ValueError("No export_directory fields found in YAML")

    # Update all export directories
    for key in export_keys:
        input_block[key] = str(export_dir)

    # Save YAML back
    with open(yaml_path, "w") as f:
        yaml.dump(config, f, sort_keys=False)

    logger.debug(f"Updated {len(export_keys)} export directories → {export_dir}")


def headless_path_setup(user_path: str | Path) -> tuple[Path, list[Path]]:
    """
    Ensures that .lif files are located in .../img/lif/.
    
    If user_path is:
        - A single .lif file -> moves it if needed
        - A directory -> collects all .lif files and moves them if needed

    Returns:
        Iterable of Path objects pointing to .lif files inside .../img/lif/
    """
    
    user_path = Path(user_path).resolve()

    if not user_path.exists():
        raise FileNotFoundError(f"Path does not exist: {user_path}")

    # Determine base project directory (where img/lif should live)
    if user_path.is_file():
        if user_path.suffix.lower() != ".lif":
            raise ValueError("Provided file is not a .lif file.")
        source_files = [user_path]
        base_dir = user_path.parent
    elif user_path.is_dir():
        source_files = list(user_path.glob("*.lif"))
        if not source_files:
            raise ValueError("No .lif files found in provided directory.")
        base_dir = user_path
    else:
        raise ValueError("Invalid path provided.")

    # Target directory: .../img/lif/
    target_dir = base_dir / "img" / "lif"

    # If already in .../img/lif/, detect and reuse
    if user_path.is_file():
        parts = user_path.parts
    else:
        parts = source_files[0].parts

    if len(parts) >= 2 and parts[-3:-1] == ("img", "lif"):
        target_dir = Path(*parts[:-1])  # already correct directory
        base_dir = target_dir.parents[1]

    # Create directory if needed
    target_dir.mkdir(parents=True, exist_ok=True)

    moved_files: list[Path] = []

    for lif_file in source_files:
        destination = target_dir / lif_file.name

        # Move only if not already there
        if lif_file.resolve() != destination.resolve():
            shutil.move(str(lif_file), str(destination))

        moved_files.append(destination)

    return base_dir, moved_files


def main(user_path: str | Path):
    # Setup correct file structure
    base_dir, files = headless_path_setup(user_path)
    
    # Configure PlantSeg YAML
    yaml_path = find_yaml(base_dir)
    configure_yaml(yaml_path, 
                   input_dir=base_dir / 'img' / 'ometiff', 
                   export_dir=base_dir / 'img'/ 'h5' / 'raw',
                   )

    logger.debug(f'Base dir: {base_dir}')
    logger.info(f'Found YAML: {yaml_path.name}')

    # Convert LIFs to OME-TIFF
    for file in files:
        convert_lif.main(file)

    # Run PlantSeg headless on OME-TIFFs
    plantseg_workflow.main(yaml_path)

    


if __name__ == "__main__":
    user_path = Path('.testflow/img/lif/250925_LowResSegmentation.lif')
    main(user_path)