from pathlib import Path

from segmentation.core.io import get_h5_files, print_h5_metrics


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
