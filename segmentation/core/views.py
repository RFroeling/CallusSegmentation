"""Module containing the neccessary functions for visualization of segmentation cleanups."""
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from shutil import move

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageTk


def display_XY_slice(dataset: np.ndarray, LUT: str ='gray', show=True) -> None:
    z = dataset.shape[0] // 2

    plt.imshow(dataset[z], cmap=LUT)
    plt.title('XY cross-section')
    if show:
        plt.show()


def display_YZ_slice(dataset: np.ndarray, LUT: str='gray', show=True) -> None:
    x = dataset.shape[1] // 2

    plt.imshow(dataset[:, x, :], cmap=LUT)
    plt.title('YZ cross-section')
    if show:
        plt.show()


def display_intensity_projection(dataset: np.ndarray, LUT: str ='gray', show=True) -> None:
    mip = dataset.max(axis=0)

    plt.imshow(mip, cmap=LUT)
    plt.title('Maximum Intensity Projection')
    if show:
        plt.show()


def create_random_colormap(num_labels: int) -> mcolors.ListedColormap:
    """Create a random colormap for labeled images.
    
    Generates a colormap where each label gets a unique random color,
    and the background (label 0) is set to black.
    
    Args:
        num_labels (int): Number of unique labels in the image (including background).
    
    Returns:
        mcolors.ListedColormap: Colormap with random colors for each label.
    """
    # Generate random colors for each label
    colors = np.random.rand(num_labels, 3)

    # Set the first color (label 0/background) to black
    colors[0] = [0, 0, 0]

    return mcolors.ListedColormap(colors)


def cleaning_comparison_plot(
        dataset: np.ndarray, 
        cleaned_dataset: np.ndarray, 
        path: Path, 
        save: bool=False
        ) -> None:
    """Create comparison plots of original and cleaned datasets.
    
    Displays XY and YZ cross-sections of both the original and cleaned datasets
    side by side for visual comparison.
    
    Args:
        dataset (np.ndarray): Original dataset.
        cleaned_dataset (np.ndarray): Cleaned dataset.
        path (Path): Path to the original .h5 file (used for saving plots).
        save (bool): Whether to save the plot as a PNG file. Defaults to False.
    """
    _, axes = plt.subplots(2, 2, figsize=(12, 10))

    z = dataset.shape[0] // 2
    x = dataset.shape[1] // 2

    # Create random colormap for labeled images
    cmap = create_random_colormap(cleaned_dataset.max() + 1)

    axes[0, 0].imshow(dataset[z], cmap=cmap)
    axes[0, 0].set_title('Original XY')

    axes[0, 1].imshow(dataset[:, x, :], cmap=cmap)
    axes[0, 1].set_title('Original YZ')

    axes[1, 0].imshow(cleaned_dataset[z], cmap=cmap)
    axes[1, 0].set_title('Cleaned XY')

    axes[1, 1].imshow(cleaned_dataset[:, x, :], cmap=cmap)
    axes[1, 1].set_title('Cleaned YZ')

    if save:
        import matplotlib as mpl
        mpl.use('agg') # Non-interactive backend for writing to files

        save_path = path.parent / 'comparison_plots'
        save_path.mkdir(exist_ok=True)
        plt.savefig(save_path / f'comparison_{path.stem}.png', dpi=300)
        plt.close()
    else:
        plt.show()


class ImageReviewer(tk.Tk):
    """GUI for checking the quality of segmentation and cleaning of callus tissue.

    Currently only supports .png images.
    """
    def __init__(self):
        super().__init__()
        self.title("Image Reviewer")
        self.geometry("700x700")
        self.ui_elements()
        self.state_variables()
        self.set_icon()


    def ui_elements(self):
        """Creates all widgets and binds events."""

        # Canvas for image display
        self.canvas = tk.Label(self, text=
                               "Open folder containing .pngs that need reviewing" \
                               "\n Use buttons or <A> and <D> to save decision" \
                               "\n Use <Left> and <Right> to navigate " \
                               "\n Use CRTL + Z to undo (in MOVE mode)", 
                               fg='grey', bg='lightgrey')
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # Controls frame
        self.controls = tk.Frame(self)
        self.controls.pack(fill="x", padx=5, pady=5)

        # Left: Open Folder button
        self.open_button = tk.Button(
            self.controls, text="Open Folder", command=self.open_folder
        )
        self.open_button.grid(row=0, column=0, sticky="w", padx=5)

        # Center: filename label
        self.filename_label = tk.Label(self.controls, text="", anchor="center")
        self.filename_label.grid(row=0, column=1, sticky="ew", padx=5)

        # Right: Decision buttons
        right_frame = tk.Frame(self.controls)
        right_frame.grid(row=0, column=2, sticky="e", padx=5)

        self.accept_button = tk.Button(
            right_frame, text="Accept", bg="lightgreen",
            command=lambda: self.sort_file("accepted")
        )
        self.decline_button = tk.Button(
            right_frame, text="Decline", bg="tomato",
            command=lambda: self.sort_file("declined")
        )

        # Pack horizontally inside right_frame
        self.accept_button.pack(side="left", padx=(0,5))
        self.decline_button.pack(side="left")

        # Configure column weights for flexible resizing
        self.controls.columnconfigure(0, weight=1)  # left
        self.controls.columnconfigure(1, weight=2)  # center (filename label stretches)
        self.controls.columnconfigure(2, weight=1)  # right

        # Progress label below controls
        self.progress_label = tk.Label(self, text="No files loaded")
        self.progress_label.pack(pady=5)

        # Key bindings
        self.bind("<a>", lambda e: self.sort_file("accepted"))
        self.bind("<d>", lambda e: self.sort_file("declined"))
        self.bind("<A>", lambda e: self.sort_file("accepted"))
        self.bind("<D>", lambda e: self.sort_file("declined"))
        self.bind("<Left>", lambda e: self.navigate(-1))
        self.bind("<Right>", lambda e: self.navigate(1))
        self.bind("<Control-z>", lambda e: self.undo_last_action())
        self.bind("<Control-Z>", lambda e: self.undo_last_action())


    def state_variables(self):
        """Define empty state variables"""
        self.folder = Path.cwd()
        self.files = []
        self.all_files = []
        self.reviewed_files = []
        self.index = 0
        self.frames = []
        self.frame_index = 0
        self.log_file = None
        self.df = pd.DataFrame(columns=["FileName", "Decision", "Timestamp"])
        self.history = []


    def set_icon(self):
        parent_dir = Path(__file__).parents[2]
        icon_path = parent_dir / "docs" / "img" / "icon.png"

        if icon_path.exists():
            self.iconphoto(False, tk.PhotoImage(file=icon_path))


    def restore_h5_files_from_log(self):
        # Move all h5 files from accepted/declined back to clean
        for _, row in self.df.iterrows():
            png_name = row["FileName"]
            h5_name = png_name.replace('comparison_', "").replace('.png', '.h5')
            for decision in ["accepted", "declined"]:
                src = self.parent / 'h5' / decision / h5_name
                dst = self.parent / 'h5' / 'clean' / h5_name
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        move(str(src), str(dst))
                    except Exception as e:
                        messagebox.showwarning(
                            "Restore error",
                            f"Could not move {src} back to clean folder:\n{e}"
                        )


    def open_folder(self):
        """Open folder and prepare files for review"""
        folder = filedialog.askdirectory()
        if not folder:
            return

        self.folder = Path(folder)
        self.parent = self.folder.parent

        # Gather all png files in folder
        all_files = sorted(self.folder.glob('*.png'))
        self.all_files = all_files

        # Prepare logging dir and file
        log_dir = self.parent / "_logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = log_dir / "review_log.csv"

        reviewed = set()
        required_cols = ["FileName", "Decision", "Timestamp"]

        # Load existing log if present
        if self.log_file.exists():
            try:
                self.df = pd.read_csv(self.log_file, dtype=str)

                # Ensure columns present
                for col in required_cols:
                    if col not in self.df.columns:
                        self.df[col] = ""

                self.df = self.df[required_cols]

                reviewed = set(
                    self.df["FileName"]
                    .dropna()
                    .astype(str)
                    .tolist()
                )

            except Exception as e:
                messagebox.showwarning(
                    "Log read error",
                    f"Could not read existing log file:\n{e}"
                )

                self.df = pd.DataFrame(columns=required_cols)

        # Save reviewed file names into separate list
        self.reviewed_files = sorted(reviewed)

        # Determine new files
        new_files = [f for f in all_files if f.name not in reviewed]

        # If a log exists and there are new files, ask whether to re-review all or only new ones
        if reviewed:
            if new_files:
                resp = messagebox.askyesno(
                    "Existing review log",
                    f"A review log was found with {len(reviewed)} reviewed file(s).\n"
                    f"{len(new_files)} file(s) are new in the folder.\n\n"
                    "Re-review all files? (Yes = all files, No = only new files)"
                )
                if resp:
                    self.restore_h5_files_from_log()
                    # Reset log and review all files
                    self.df = pd.DataFrame(columns=["FileName", "Decision", "Timestamp"])
                    try:
                        self.df.to_csv(self.log_file, index=False)
                    except Exception as e:
                        messagebox.showwarning(
                            "Log write error",
                            f"Could not reset log file:\n{e}"
                        )
                    self.files = all_files.copy()
                else:
                    # Only review new files, keep existing log
                    self.files = new_files
            else:
                # No new files
                resp = messagebox.askyesno(
                    "No new files",
                    "All files in the folder are already reviewed.  \
                    \nDo you want to re-review all files?"
                )
                if resp:
                    self.restore_h5_files_from_log()
                    self.df = pd.DataFrame(columns=["FileName", "Decision", "Timestamp"])
                    try:
                        self.df.to_csv(self.log_file, index=False)
                    except Exception as e:
                        messagebox.showwarning(
                            "Log write error",
                            f"Could not reset log file:\n{e}"
                        )
                    self.files = all_files.copy()
                else:
                    messagebox.showinfo(
                        "Nothing to do",
                        "No new files to review."
                    )
                    return
        else:
            # No existing log; create one and review all files
            self.df = pd.DataFrame(columns=required_cols)

            try:
                self.df.to_csv(self.log_file, index=False)
            except Exception as e:
                messagebox.showwarning(
                    "Log create error",
                    f"Could nog create log file:\n{e}"
                )

            self.files = all_files.copy()

        # Start reviewing
        self.index = 0
        if not self.files:
            messagebox.showinfo("No files", "No image files found in folder")
            return
        self.show_file()


    def show_file(self):
        """Function to display current file"""
        if self.index < 0 or self.index >= len(self.files):
            messagebox.showinfo("Done", "All files reviewed!")
            self.progress_label.config(text="Review complete")
            self.filename_label.config(text="")  # clear filename when done
            return

        if self.folder == Path.cwd() or not self.folder.is_dir(): # I.e. no path selected
            messagebox.showerror("Error", "No folder selected")
            return

        # Load and display image
        image_path = self.folder / self.files[self.index]
        try:
            # Load image
            image = Image.open(image_path)

            # Resize to fit canvas while maintaining aspect ratio
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width > 1:  # winfo_width returns 1 if widget not yet rendered
                image.thumbnail((canvas_width - 10, canvas_height - 10), Image.Resampling.LANCZOS)

            # Convert to PhotoImage and display
            self.photo_image = ImageTk.PhotoImage(image)
            self.canvas.config(image=self.photo_image)

            # Update labels
            filename = self.files[self.index].name
            self.filename_label.config(text=filename)
            self.update_progress()

        except Exception as e:
            messagebox.showerror("Error", f"Could not load image:\n{e}")
            self.index += 1
            self.show_file()


    def sort_file(self, decision):
        """ Function to sort file based on user decision"""
        # Move associated .h5 file
        if not self.move_associated_h5(decision):
            return

        # If succes > add logging
        if self.log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fname = self.files[self.index].name
            # Update dataframe: if exists, replace; else append
            if not self.df.empty and fname in self.df["FileName"].values:
                self.df.loc[self.df["FileName"] == fname, 
                            ["Decision", "Timestamp"]] = [decision, timestamp]
            else:
                new_row = {"FileName": fname, "Decision": decision, "Timestamp": timestamp}
                self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
            # Write to disk
            try:
                self.df.to_csv(self.log_file, index=False)
            except Exception as e:
                messagebox.showwarning(
                    "Log write error",
                    f"Could not write to log file:\n{e}"
                )

        # Move to next file
        self.index += 1
        if self.index < len(self.files):
            self.show_file()
        else:
            messagebox.showinfo("Done", "All files reviewed!")
            self.canvas.config(image='')
            self.progress_label.config(text="Review complete")
            self.filename_label.config(text="")  # clear filename when finished

    
    def move_associated_h5(self, decision):
        """Move associated h5 file. Returns True if success, False if failed."""
        target_dir = self.parent / 'h5' / decision
        target_dir.mkdir(parents=True, exist_ok=True)

        png_name = self.files[self.index].name
        h5_name = png_name.replace('comparison_', "").replace('.png', '.h5')

        source_h5 = self.parent / 'h5' / 'clean' / h5_name
        dest_h5 = target_dir / h5_name

        # Validation checks
        if not source_h5.exists():
            messagebox.showerror(
                "Missing H5 file",
                f"Expected file not found:\n{source_h5}\n\n"
                "Decision cancelled."
            )
            return False

        if dest_h5.exists():
            resp = messagebox.askyesno(
                "File exists",
                f"{dest_h5.name} already exists in target folder.\n"
                "Overwrite?"
            )
            if not resp:
                return False
            dest_h5.unlink()

        # Try moving
        try:
            move(str(source_h5), str(dest_h5))
            self.history.append({
            "filename": h5_name,
            "decision": decision,
            "source": str(dest_h5),     # where it was moved TO
            "destination": str(source_h5)  # original location
            })
            return True

        except PermissionError:
            messagebox.showerror(
                "Permission error",
                f"Cannot move file:\n{source_h5}\n\n"
                "The file may be open in another program."
            )
            return False

        except Exception as e:
            messagebox.showerror(
                "Move failed",
                f"Unexpected error while moving file:\n{source_h5}\n\n{e}"
            )
            return False

    def undo_last_action(self):
        """Undo the most recent decision."""
        
        if not self.history:
            return

        last_action = self.history.pop()

        source = Path(last_action["source"])
        destination = Path(last_action["destination"])
        filename = last_action["filename"]

        try:
            # Move file back
            if source.exists():
                move(str(source), str(destination))

            # Remove entry from dataframe
            self.df = self.df[self.df["FileName"] != filename]

            # Rewrite log file
            if self.log_file:
                self.df.to_csv(self.log_file, index=False)

            # Move index back
            self.index = max(0, self.index - 1)

            # Show file again
            self.show_file()

        except Exception as e:
            messagebox.showerror(
                "Undo failed",
                f"Could not undo action:\n{e}"
            )

    def navigate(self, step):
        """Move through images without making decisions."""
        if not self.files:
            return  # No files loaded

        new_index = self.index + step
        # Clamp index within valid range
        if new_index < 0:
            return
        elif new_index >= len(self.files):
            return

        self.index = new_index
        self.show_file()


    def update_progress(self):
        """Update progress label"""
        total = len(self.files)
        current = self.index + 1
        self.progress_label.config(text=f"Item {current}/{total}")


    def run(self):
        self.mainloop()
