import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from datetime import datetime
import pandas as pd
import numpy as np
import tifffile as tiff

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
        self.df = pd.DataFrame(columns=[
            "FileName", "Timestamp", "ID", "SizeX", "SizeY", "SizeZ",
            "Line", "Age", "CellCount", "State"
        ])

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

        # Filename label (shows currently displayed image)
        self.filename_label = tk.Label(root, text="", font=("TkDefaultFont", 10, "bold"))
        self.filename_label.pack(pady=(6,0))

        # Progress label
        self.progress_label = tk.Label(root, text="No files loaded")
        self.progress_label.pack(pady=5)

        # Key bindings
        self.root.bind("<Return>", lambda e: self.save_and_next())
        self.root.bind("<Tab>", lambda e: self.save_and_next())
        self.root.bind("<Shift-Right>", lambda e: self.save_and_next())
        self.root.bind("<Shift-Left>", lambda e: self.go_previous())

        # Keybinds for navigating frame scrollbar
        self.root.bind("<Left>", lambda e: self.scrollbar.set(max(0, self.frame_index - 1)))
        self.root.bind("<Right>", lambda e: self.scrollbar.set(min(len(self.frames)-1, self.frame_index + 1)))
        
        # New bindings for radio button navigation
        self.root.bind("<Up>", self.navigate_type_up)
        self.root.bind("<Down>", self.navigate_type_down)

    # Function to open folder and prepare files for review
    def open_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.folder = folder
        self.parent = os.path.dirname(folder)

        # Gather all image files in folder
        all_files = [f for f in os.listdir(self.folder) if f.lower().endswith(".tif")]
        all_files.sort()
        self.all_files = all_files.copy()

        # Check for review_log.csv
        review_log_path = os.path.join(self.parent, "_logs", "review_log.csv")
        if not os.path.exists(review_log_path):
            messagebox.showerror(
                "Review log missing",
                "No 'review_log.csv' found in this folder.\nPlease finish reviewing first."
            )
            return

        # Read review log and filter accepted files
        try:
            review_df = pd.read_csv(review_log_path, dtype=str)
            # Ensure columns present
            required = ["FileName", "Decision", "Timestamp"]
            for col in required:
                if col not in review_df.columns:
                    review_df[col] = ""
            # All reviewed files (accepted or declined)
            reviewed_files = set(review_df["FileName"].dropna().astype(str).tolist())
            # Only accepted files
            accepted_files = review_df[review_df["Decision"] == "accepted"]["FileName"].dropna().astype(str).tolist()
        except Exception as e:
            messagebox.showerror(
                "Review log error",
                f"Could not read 'review_log.csv':\n{e}\nPlease finish reviewing first."
            )
            return

        # Exception: more images in folder than reviewed
        if len(all_files) > len(reviewed_files):
            messagebox.showerror(
                "Unreviewed images",
                "There are more image files in the folder than reviewed files in 'review_log.csv'.\n"
                "Please finish reviewing all images first."
            )
            return

        # Only use accepted files for counting
        self.files = [f for f in all_files if f in accepted_files]

        if not self.files:
            messagebox.showinfo("No accepted files", "No accepted image files found for counting.")
            return

        # Prepare metric log path and load existing entries if present
        self.metric_log_file = os.path.join(self.parent, "_logs", "metric_log.csv")
        reviewed = set()
        if os.path.exists(self.metric_log_file):
            try:
                self.df = pd.read_csv(self.metric_log_file, dtype=str)
                required = ["FileName","Timestamp","ID","SizeX","SizeY","SizeZ","Line","Age","CellCount","State"]
                for col in required:
                    if col not in self.df.columns:
                        self.df[col] = ""
                self.df = self.df[required]
                reviewed = set(self.df["FileName"].dropna().astype(str).tolist())
            except Exception as e:
                messagebox.showwarning("Log read error", f"Could not read existing metric_log.csv:\n{e}")
                self.df = pd.DataFrame(columns=["FileName","Timestamp","ID","SizeX","SizeY","SizeZ","Line","Age","CellCount","State"])
        else:
            self.df = pd.DataFrame(columns=["FileName","Timestamp","ID","SizeX","SizeY","SizeZ","Line","Age","CellCount","State"])
            try:
                self.df.to_csv(self.metric_log_file, index=False)
            except Exception as e:
                messagebox.showwarning("Log write error", f"Could not create metric_log.csv:\n{e}")

        # Start reviewing 
        self.index = 0
        self.reviewed_files = list(reviewed)
        self.show_file()

    # Load all frames of the TIFF image
    def load_frames(self, path):
        self.frames = []
        # Read TIFF with tifffile (handles multi-page, multi-channel, various dtypes)
        arr = tiff.imread(path)
        # Normalize to a list of frame arrays
        frames_list = []
        if arr.ndim == 2:
            frames_list = [arr]
        elif arr.ndim == 3:
            # Heuristic: (pages, H, W) vs (H, W, C)
            if arr.shape[0] > 1 and arr.shape[0] != 3:
                # treat as pages
                frames_list = [arr[i] for i in range(arr.shape[0])]
            else:
                # treat as single image with channels
                frames_list = [arr]
        elif arr.ndim == 4:
            # (pages, H, W, C)
            frames_list = [arr[i] for i in range(arr.shape[0])]
        else:
            frames_list = [arr]

        for f in frames_list:
            # Convert 16-bit grayscale -> 8-bit, or ensure uint8 for color
            if f.dtype == np.uint16 and f.ndim == 2:
                arr8 = (f >> 8).astype(np.uint8)
                im8 = Image.fromarray(arr8, mode="L")
            elif f.ndim == 2:
                im8 = Image.fromarray(f.astype(np.uint8), mode="L")
            else:
                im8 = Image.fromarray(f.astype(np.uint8))

            # Convert to RGB for consistent display (matches previous behavior),
            # then resize to 512x512 (previous code used NEAREST).
            im8 = im8.convert("RGB")
            im8 = im8.resize((512, 512), Image.Resampling.NEAREST)
            self.frames.append(ImageTk.PhotoImage(im8))

        self.frame_index = 0
        self.scrollbar.config(to=max(0, len(self.frames)-1))

    # Function to display current file
    def show_file(self):
        if self.index < 0 or self.index >= len(self.files):
            messagebox.showinfo("Done", "All files reviewed!")
            self.progress_label.config(text="Review complete")
            self.filename_label.config(text="")  # clear filename when done
            return
        path = os.path.join(self.folder, self.files[self.index])
        self.load_frames(path)
        # display current filename
        self.filename_label.config(text=self.files[self.index])
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
    
        # Add this line to focus the count entry field
        self.count_entry.focus_set()
        self.count_entry.select_range(0, tk.END)

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
        # get image sizes using tifffile (more robust for multi-page/multi-channel)
        path = os.path.join(self.folder, fname)
        try:
            arr = tiff.imread(path)
            if arr.ndim == 2:
                size_y, size_x = arr.shape
                size_z = 1
            elif arr.ndim == 3:
                # distinguish (pages, H, W) vs (H, W, C)
                if arr.shape[0] > 1 and arr.shape[0] != 3:
                    size_z = arr.shape[0]
                    size_y = arr.shape[1]
                    size_x = arr.shape[2]
                else:
                    # single frame with channels
                    size_z = 1
                    size_y = arr.shape[0]
                    size_x = arr.shape[1]
            elif arr.ndim == 4:
                # (pages, H, W, C)
                size_z = arr.shape[0]
                size_y = arr.shape[1]
                size_x = arr.shape[2]
            else:
                # fallback
                size_y, size_x = (arr.shape[-2], arr.shape[-1])
                size_z = 1
        except Exception:
            # fallback to PIL if tifffile fails
            try:
                with Image.open(path) as img:
                    size_x, size_y = img.size
                    size_z = getattr(img, "n_frames", 1)
            except Exception as e:
                messagebox.showwarning("Image error", f"Could not read image sizes for {fname}:\n{e}")
                return False
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- Extract ID, Line, Age from filename ---
        # Assumes filename format: date1_date2_line_otherparts.tif
        # date1 and date2 are in yymmdd format (e.g. 230101)
        # ID: first three items separated by '_'
        # Line: third item
        # Age: difference in days between date2 and date1 (as int)
        id_str, line_str, age_val = "", "", ""
        try:
            parts = os.path.splitext(fname)[0].split("_")  # strip extension first
            if len(parts) >= 4:
                id_str = "_".join(parts[:4])
                line_str = parts[2]
                # parse yymmdd dates -> compute difference in days
                try:
                    d1 = datetime.strptime(parts[0], "%y%m%d").date()
                    d2 = datetime.strptime(parts[1], "%y%m%d").date()
                    age_days = (d2 - d1).days
                    age_val = int(age_days)
                except Exception:
                    age_val = ""
            else:
                id_str = ""
                line_str = ""
                age_val = ""
        except Exception:
            id_str = ""
            line_str = ""
            age_val = ""

        # prepare row as strings / values
        row = {
            "FileName": fname,
            "Timestamp": timestamp,
            "ID": id_str,
            "SizeX": int(size_x),
            "SizeY": int(size_y),
            "SizeZ": int(size_z),
            "Line": line_str,
            "Age": age_val,
            "CellCount": ("" if count_text == "" else int(count_text)),
            "State": state
        }

        # update dataframe: if exists, replace; else append
        if not self.df.empty and fname in self.df["FileName"].values:
            self.df.loc[self.df["FileName"] == fname, [
                "Timestamp","ID","SizeX","SizeY","SizeZ","Line","Age","CellCount","State"
            ]] = [
                row["Timestamp"], row["ID"], row["SizeX"], row["SizeY"], row["SizeZ"],
                row["Line"], row["Age"], row["CellCount"], row["State"]
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
            self.filename_label.config(text="")  # clear filename on completion

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

    # New methods for radio button navigation
    def navigate_type_up(self, event):
        current = self.type_var.get()
        if current == "Other":
            self.type_var.set("Loose")
        elif current == "Loose":
            self.type_var.set("Compact")
                
    def navigate_type_down(self, event):
        current = self.type_var.get()
        if current == "Compact":
            self.type_var.set("Loose")
        elif current == "Loose":
            self.type_var.set("Other")

# Main application loop
if __name__ == "__main__":
    root = tk.Tk()
    app = ManualCounter(root)
    root.mainloop()
