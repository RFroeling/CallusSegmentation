from pathlib import Path
import shutil

def headless_path_setup(user_path: str | Path) -> list[Path]:
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

    # Create directory if needed
    target_dir.mkdir(parents=True, exist_ok=True)

    moved_files: list[Path] = []

    for lif_file in source_files:
        destination = target_dir / lif_file.name

        # Move only if not already there
        if lif_file.resolve() != destination.resolve():
            shutil.move(str(lif_file), str(destination))

        moved_files.append(destination)

    return moved_files


def headless_workflow(user_path: str | Path):
    files = headless_path_setup(user_path)
    for file in files:
        print(file)

if __name__ == "__main__":
    user_path = Path('.data/testflow/250925_LowResSegmentation.lif')
    headless_workflow(user_path)