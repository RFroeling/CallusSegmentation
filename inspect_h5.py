from pathlib import Path
import h5py
import os


def get_h5_files(folder_path: Path) -> list[Path]:
    """Get all .h5 files in a folder.
    
    Args:
        folder_path (Path): Path to the folder to search.
    
    Returns:
        list[Path]: List of .h5 file paths.
    """
    h5_files = list(folder_path.glob('*.h5'))
    return sorted(h5_files)


def print_h5_metrics(file_path: Path) -> None:
    """Inspect and print metrics about a .h5 file.
    
    Args:
        file_path (Path): Path to the .h5 file to inspect.
    """
    # File size
    file_size_mb = os.path.getsize(file_path) / (1024 ** 2)
    
    print(f"\n{'='*60}")
    print(f"File: {file_path.name}")
    print(f"{'='*60}")
    print(f"Path: {file_path}")
    print(f"Size: {file_size_mb:.2f} MB")
    print(f"\n{'Datasets:':<50}")
    print(f"{'-'*60}")
    
    with h5py.File(file_path, 'r') as f:
        # Print all keys and their properties
        for key in f.keys():
            dataset = f[key]
            shape = dataset.shape
            dtype = dataset.dtype
            
            print(f"\nKey: {key}")
            print(f"  Shape: {shape}")
            print(f"  Data type: {dtype}")
            print(f"  Size: {dataset.nbytes / (1024 ** 2):.2f} MB")
            
            # Print statistics for numeric datasets
            if dataset.dtype.kind in ['f', 'i', 'u']:  # float, signed int, unsigned int
                print(f"  Min: {dataset[()].min():.4f}")
                print(f"  Max: {dataset[()].max():.4f}")
                print(f"  Mean: {dataset[()].mean():.4f}")
    
    print(f"\n{'='*60}\n")


def main():
    """Main function to inspect H5 files interactively."""
    # Get folder path from user
    folder_input = input("Enter folder path (or press Enter for current directory): ").strip()
    
    if not folder_input:
        folder_path = Path('.')
    else:
        folder_path = Path(folder_input)
    
    if not folder_path.exists():
        print(f"Error: Folder '{folder_path}' does not exist.")
        return
    
    # Get all .h5 files
    h5_files = get_h5_files(folder_path)
    
    if not h5_files:
        print(f"No .h5 files found in {folder_path}")
        return
    
    # Display available files
    print(f"\nFound {len(h5_files)} .h5 file(s):")
    print(f"{'-'*60}")
    for i, file in enumerate(h5_files, 1):
        print(f"{i}. {file.name}")
    
    # Get user selection
    while True:
        try:
            choice = input(f"\nSelect file (1-{len(h5_files)}) or 'all' to inspect all: ").strip()
            
            if choice.lower() == 'all':
                for file in h5_files:
                    print_h5_metrics(file)
            else:
                file_index = int(choice) - 1
                if 0 <= file_index < len(h5_files):
                    print_h5_metrics(h5_files[file_index])
                else:
                    print("Invalid selection. Please try again.")
                    continue
            break
        except ValueError:
            print("Invalid input. Please enter a number or 'all'.")


if __name__ == "__main__":
    main()
