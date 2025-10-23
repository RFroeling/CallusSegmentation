import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageSequence
from datetime import datetime
import pandas as pd

# Class for reviewing multi-layer TIFF images
class TIFFReviewer:
    def __init__(self, root):
        self.root = root # Main window
        self.root.title("TIFF Reviewer")

        # State variables
        self.folder = None
        self.files = []
        self.all_files = []
        self.reviewed_files = []
        self.index = 0
        self.frames = []
        self.frame_index = 0
        self.log_file = None
        self.df = pd.DataFrame(columns=["FileName", "Decision", "Timestamp"])

        # UI Elements
        self.canvas = tk.Label(root) # Image display area
        self.canvas.pack()

        self.controls = tk.Frame(root) # Control buttons frame
        self.controls.pack(fill=tk.X)

        # Buttons for folder selection and sorting
        tk.Button(self.controls, text="Open Folder", command=self.open_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(self.controls, text="Accept", bg="lightgreen", command=lambda: self.sort_file("accepted")).pack(side=tk.RIGHT, padx=5)
        tk.Button(self.controls, text="Decline", bg="tomato", command=lambda: self.sort_file("declined")).pack(side=tk.RIGHT, padx=5)

        # Scrollbar for frames
        self.scrollbar = tk.Scale(self.controls, from_=0, to=0, orient=tk.HORIZONTAL, command=self.scroll_frame)
        self.scrollbar.pack(fill=tk.X, expand=True, padx=5)

        # Progress label
        self.progress_label = tk.Label(root, text="No files loaded")
        self.progress_label.pack(pady=5)

        # Key bindings
        self.root.bind("<a>", lambda e: self.sort_file("accepted"))
        self.root.bind("<d>", lambda e: self.sort_file("declined"))
        self.root.bind("<A>", lambda e: self.sort_file("accepted"))
        self.root.bind("<D>", lambda e: self.sort_file("declined"))

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
        self.all_files = all_files

        # Prepare log path and read existing log if present
        self.log_file = os.path.join(self.parent, "_logs", "review_log.csv")
        reviewed = set()
        if os.path.exists(self.log_file):
            try:
                self.df = pd.read_csv(self.log_file, dtype=str)
                # Ensure columns present
                required = ["FileName", "Decision", "Timestamp"]
                for col in required:
                    if col not in self.df.columns:
                        self.df[col] = ""
                self.df = self.df[required]
                reviewed = set(self.df["FileName"].dropna().astype(str).tolist())
            except Exception as e:
                messagebox.showwarning("Log read error", f"Could not read existing log file:\n{e}")
                self.df = pd.DataFrame(columns=["FileName", "Decision", "Timestamp"])

        # Save reviewed file names into separate list
        self.reviewed_files = sorted(list(reviewed))

        # Determine new files
        new_files = [f for f in all_files if f not in reviewed]

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
                    # Reset log and review all files
                    self.df = pd.DataFrame(columns=["FileName", "Decision", "Timestamp"])
                    try:
                        self.df.to_csv(self.log_file, index=False)
                    except Exception as e:
                        messagebox.showwarning("Log write error", f"Could not reset log file:\n{e}")
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
                    self.df = pd.DataFrame(columns=["FileName", "Decision", "Timestamp"])
                    try:
                        self.df.to_csv(self.log_file, index=False)
                    except Exception as e:
                        messagebox.showwarning("Log write error", f"Could not reset log file:\n{e}")
                    self.files = all_files.copy()
                else:
                    messagebox.showinfo("Nothing to do", "No new files to review.")
                    return
        else:
            # No existing log; create one and review all files
            self.df = pd.DataFrame(columns=["FileName", "Decision", "Timestamp"])
            try:
                self.df.to_csv(self.log_file, index=False)
            except Exception as e:
                messagebox.showwarning("Log write error", f"Could not create log file:\n{e}")
            self.files = all_files.copy()
        
        # Start reviewing 
        self.index = 0
        if not self.files:
            messagebox.showinfo("No files", "No image files found in folder")
            return
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

    # Function to display current frame based on scrollbar
    def show_frame(self):
        if self.frames:
            self.canvas.config(image=self.frames[self.frame_index])
            self.scrollbar.set(self.frame_index)
    
    # Function to handle scrollbar movement
    def scroll_frame(self, val):
        self.frame_index = int(val)
        self.show_frame()

    # Function to sort file based on user decision
    def sort_file(self, decision):
        if self.log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fname = self.files[self.index]
            # Update dataframe: if exists, replace; else append
            if not self.df.empty and fname in self.df["FileName"].values:
                self.df.loc[self.df["FileName"] == fname, ["Decision", "Timestamp"]] = [decision, timestamp]
            else:
                new_row = {"FileName": fname, "Decision": decision, "Timestamp": timestamp}
                self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
            # Immediately write to disk
            try:
                self.df.to_csv(self.log_file, index=False)
            except Exception as e:
                messagebox.showwarning("Log write error", f"Could not write to log file:\n{e}")
        
        # Move to next file
        self.index += 1
        if self.index < len(self.files):
            self.show_file()
        else:
            messagebox.showinfo("Done", "All files reviewed!")
            self.canvas.config(image='')
            self.progress_label.config(text="Review complete")
    
    # Update progress label
    def update_progress(self):
        total = len(self.files)
        current = self.index + 1
        self.progress_label.config(text=f"Item {current}/{total}")

# Main application loop
if __name__ == "__main__":
    root = tk.Tk()
    app = TIFFReviewer(root)
    root.mainloop()
