import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageSequence
from datetime import datetime
import pandas as pd

# Class for reviewing multi-layer TIFF images
class ManualCounter:
    def __init__(self, root):
        self.root = root # Main window
        self.root.title("Manual callus scoring")

        # State variables
        self.folder = None
        self.files = []
        self.all_files = []
        self.reviewed_files = []
        self.index = 0
        self.frames = []
        self.frame_index = 0
        self.metric_log_file = None
        self.df = pd.DataFrame(columns=["FileName","Timestamp","SizeX","SizeY","SizeZ","CellCount","State"])

        # UI Elements
        self.canvas = tk.Label(root) # Image display area
        self.canvas.pack()

        self.controls = tk.Frame(root) # Control buttons frame
        self.controls.pack(fill=tk.X)

        # Buttons for folder selection and navigation/saving
        tk.Button(self.controls, text="Open Folder", command=self.open_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(self.controls, text="Save and next", command=self.save_and_next).pack(side=tk.RIGHT, padx=5)
        tk.Button(self.controls, text="Previous", command=self.go_previous).pack(side=tk.RIGHT, padx=5)

        # Scrollbar for frames
        self.scrollbar = tk.Scale(self.controls, from_=0, to=0, orient=tk.HORIZONTAL, command=self.scroll_frame)
        self.scrollbar.pack(fill=tk.X, expand=True, padx=5)

        # Input area for manual counting and classification
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(fill=tk.X, pady=6)

        tk.Label(self.input_frame, text="Cell count:").pack(side=tk.LEFT, padx=(6,2))
        self.count_var = tk.StringVar()
        self.count_entry = tk.Entry(self.input_frame, textvariable=self.count_var, width=8)
        self.count_entry.pack(side=tk.LEFT, padx=(0,10))

        self.type_var = tk.StringVar(value="Compact")
        type_frame = tk.Frame(self.input_frame)
        type_frame.pack(side=tk.LEFT, padx=6)
        tk.Label(type_frame, text="Type:").pack(anchor="w")
        tk.Radiobutton(type_frame, text="Compact", variable=self.type_var, value="Compact").pack(anchor="w")
        tk.Radiobutton(type_frame, text="Loose",    variable=self.type_var, value="Loose").pack(anchor="w")
        tk.Radiobutton(type_frame, text="Other",    variable=self.type_var, value="Other").pack(anchor="w")

        # Progress label
        self.progress_label = tk.Label(root, text="No files loaded")
        self.progress_label.pack(pady=5)

    # Function to open folder and prepare files for review
    def open_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.folder = folder

        # Gather all image files in folder
        exts = (".tif", ".tiff", ".png")
        all_files = [f for f in os.listdir(self.folder) if f.lower().endswith(exts)]
        all_files.sort()
        self.all_files = all_files.copy()

        if not all_files:
            messagebox.showinfo("No files", "No image files found in folder")
            return

        # Prepare metric log path and load existing entries if present
        self.metric_log_file = os.path.join(self.folder, "metric_log.csv")
        reviewed = set()
        if os.path.exists(self.metric_log_file):
            try:
                self.df = pd.read_csv(self.metric_log_file, dtype=str)
                # ensure columns present
                required = ["FileName","Timestamp","SizeX","SizeY","SizeZ","CellCount","State"]
                for col in required:
                    if col not in self.df.columns:
                        self.df[col] = ""
                # normalize types as string for ease of use
                self.df = self.df[required]
                reviewed = set(self.df["FileName"].dropna().astype(str).tolist())
            except Exception as e:
                messagebox.showwarning("Log read error", f"Could not read existing metric_log.csv:\n{e}")
                # fall back to empty df
                self.df = pd.DataFrame(columns=["FileName","Timestamp","SizeX","SizeY","SizeZ","CellCount","State"])

        # Determine new files
        new_files = [f for f in all_files if f not in reviewed]

        # If a log exists and there are new files, ask whether to re-review all or only new ones
        if reviewed:
            if new_files:
                resp = messagebox.askyesno(
                    "Existing metric log",
                    f"A metric log was found with {len(reviewed)} reviewed file(s).\n"
                    f"{len(new_files)} file(s) are new in the folder.\n\n"
                    "Re-review all files? (Yes = all files, No = only new files)"
                )
                if resp:
                    # Reset log (clear dataframe and file) and review all files
                    self.df = pd.DataFrame(columns=["FileName","Timestamp","SizeX","SizeY","SizeZ","CellCount","State"])
                    try:
                        self.df.to_csv(self.metric_log_file, index=False)
                    except Exception as e:
                        messagebox.showwarning("Log write error", f"Could not reset metric_log.csv:\n{e}")
                    self.files = all_files.copy()
                else:
                    # Only review new files, keep existing log
                    self.files = new_files
            else:
                # No new files
                resp = messagebox.askyesno(
                    "No new files",
                    "All files in the folder are already reviewed.\nDo you want to re-review all files?"
                )
                if resp:
                    # Reset log and re-review
                    self.df = pd.DataFrame(columns=["FileName","Timestamp","SizeX","SizeY","SizeZ","CellCount","State"])
                    try:
                        self.df.to_csv(self.metric_log_file, index=False)
                    except Exception as e:
                        messagebox.showwarning("Log write error", f"Could not reset metric_log.csv:\n{e}")
                    self.files = all_files.copy()
                else:
                    messagebox.showinfo("Nothing to do", "No new files to review.")
                    return
        else:
            # No existing log; create one and review all files
            self.df = pd.DataFrame(columns=["FileName","Timestamp","SizeX","SizeY","SizeZ","CellCount","State"])
            try:
                self.df.to_csv(self.metric_log_file, index=False)
            except Exception as e:
                messagebox.showwarning("Log write error", f"Could not create metric_log.csv:\n{e}")
            self.files = all_files.copy()

        # Start reviewing 
        self.index = 0
        if not self.files:
            messagebox.showinfo("No files", "No image files selected for review")
            return
        # ensure reviewed_files list for reference
        self.reviewed_files = list(reviewed)
        self.show_file()

    # Load all frames of the TIFF image
    def load_frames(self, path):
        self.frames = []
        img = Image.open(path)
        for frame in ImageSequence.Iterator(img):
            self.frames.append(ImageTk.PhotoImage(frame.copy().convert("RGB")))
        self.frame_index = 0
        self.scrollbar.config(to=max(0, len(self.frames)-1))

    # Function to display current file
    def show_file(self):
        if self.index < 0 or self.index >= len(self.files):
            messagebox.showinfo("Done", "All files reviewed!")
            self.progress_label.config(text="Review complete")
            return
        path = os.path.join(self.folder, self.files[self.index])
        self.load_frames(path)
        self.show_frame()
        self.update_progress()
        # populate input fields if there is a saved entry in dataframe
        fname = self.files[self.index]
        row = None
        if not self.df.empty:
            matches = self.df[self.df["FileName"] == fname]
            if not matches.empty:
                row = matches.iloc[0]
        if row is not None:
            # set count and type from dataframe (may be NaN)
            self.count_var.set("" if pd.isna(row["CellCount"]) else str(row["CellCount"]))
            st = "" if pd.isna(row["State"]) else str(row["State"])
            if st:
                self.type_var.set(st)
        else:
            self.count_var.set("")
            self.type_var.set("Compact")

    # Function to display current frame based on scrollbar
    def show_frame(self):
        if self.frames:
            self.canvas.config(image=self.frames[self.frame_index])
            self.scrollbar.set(self.frame_index)
    
    # Function to handle scrollbar movement
    def scroll_frame(self, val):
        self.frame_index = int(val)
        self.show_frame()

    def save_current_entry(self):
        """Validate and save current entry into dataframe and write to metric_log.csv."""
        if not self.files or self.index < 0 or self.index >= len(self.files):
            return False
        fname = self.files[self.index]
        count_text = self.count_var.get().strip()
        state = self.type_var.get().strip() if self.type_var.get() else "Other"
        # validate count if provided
        if count_text != "":
            try:
                int(count_text)
            except ValueError:
                messagebox.showwarning("Invalid input", "Cell count must be an integer or left empty.")
                return False
        # get image sizes
        path = os.path.join(self.folder, fname)
        try:
            with Image.open(path) as img:
                size_x, size_y = img.size
                size_z = getattr(img, "n_frames", 1)
        except Exception as e:
            messagebox.showwarning("Image error", f"Could not read image sizes for {fname}:\n{e}")
            return False
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # prepare row as strings
        row = {
            "FileName": fname,
            "Timestamp": timestamp,
            "SizeX": int(size_x),
            "SizeY": int(size_y),
            "SizeZ": int(size_z),
            "CellCount": ("" if count_text == "" else int(count_text)),
            "State": state
        }

        # update dataframe: if exists, replace; else append
        if not self.df.empty and fname in self.df["FileName"].values:
            self.df.loc[self.df["FileName"] == fname, ["Timestamp","SizeX","SizeY","SizeZ","CellCount","State"]] = [
                row["Timestamp"], row["SizeX"], row["SizeY"], row["SizeZ"], row["CellCount"], row["State"]
            ]
        else:
            self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)

        # immediately write to disk
        try:
            self.df.to_csv(self.metric_log_file, index=False)
        except Exception as e:
            messagebox.showwarning("Log write error", f"Could not write to metric_log.csv:\n{e}")
            return False

        return True

    def save_and_next(self):
        if not self.files:
            return
        ok = self.save_current_entry()
        if not ok:
            return
        # move to next
        self.index += 1
        if self.index < len(self.files):
            self.show_file()
        else:
            messagebox.showinfo("Done", "All files processed!")
            self.canvas.config(image='')
            self.progress_label.config(text="Processing complete")

    def go_previous(self):
        if not self.files:
            return
        # save current before going back
        ok = self.save_current_entry()
        if not ok:
            return
        if self.index > 0:
            self.index -= 1
            self.show_file()
        else:
            messagebox.showinfo("Start", "Already at first file.")

    # Update progress label
    def update_progress(self):
        total = len(self.files)
        current = self.index + 1
        self.progress_label.config(text=f"Item {current}/{total}")

# Main application loop
if __name__ == "__main__":
    root = tk.Tk()
    app = ManualCounter(root)
    root.mainloop()
