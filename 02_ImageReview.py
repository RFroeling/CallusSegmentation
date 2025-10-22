import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageSequence
from datetime import datetime

class TIFFReviewer:
    def __init__(self, root):
        self.root = root
        self.root.title("TIFF Reviewer")

        self.folder = None
        self.files = []
        self.index = 0
        self.frames = []
        self.frame_index = 0
        self.log_file = None

        # UI Elements
        self.canvas = tk.Label(root)
        self.canvas.pack()

        self.controls = tk.Frame(root)
        self.controls.pack(fill=tk.X)

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

    def open_folder(self):
        self.folder = filedialog.askdirectory()
        if not self.folder:
            return
        self.files = [f for f in os.listdir(self.folder) if f.lower().endswith(".tif") or f.lower().endswith(".tiff") or f.lower().endswith(".png")]
        self.index = 0
        if not self.files:
            messagebox.showinfo("No files", "No image files found in folder")
            return
        # Create/reset log file
        self.log_file = os.path.join(self.folder, "review_log.txt")
        with open(self.log_file, "w") as log:
            log.write("File,Decision,Timestamp\n")
        self.show_file()

    def load_frames(self, path):
        self.frames = []
        img = Image.open(path)
        for frame in ImageSequence.Iterator(img):
            self.frames.append(ImageTk.PhotoImage(frame.copy().convert("RGB")))
        self.frame_index = 0
        self.scrollbar.config(to=len(self.frames)-1)

    def show_file(self):
        if self.index < 0 or self.index >= len(self.files):
            messagebox.showinfo("Done", "All files reviewed!")
            self.progress_label.config(text="Review complete")
            return
        path = os.path.join(self.folder, self.files[self.index])
        self.load_frames(path)
        self.show_frame()
        self.update_progress()

    def show_frame(self):
        if self.frames:
            self.canvas.config(image=self.frames[self.frame_index])
            self.scrollbar.set(self.frame_index)

    def scroll_frame(self, val):
        self.frame_index = int(val)
        self.show_frame()

    def sort_file(self, decision):
        if self.log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a") as log:
                log.write(f"{self.files[self.index]},{decision},{timestamp}\n")

        self.index += 1
        if self.index < len(self.files):
            self.show_file()
        else:
            messagebox.showinfo("Done", "All files reviewed!")
            self.canvas.config(image='')
            self.progress_label.config(text="Review complete")

    def update_progress(self):
        total = len(self.files)
        current = self.index + 1
        self.progress_label.config(text=f"Item {current}/{total}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TIFFReviewer(root)
    root.mainloop()
