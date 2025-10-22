import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class TiffViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-layer TIFF Viewer")

        # UI Elements
        self.select_button = tk.Button(root, text="Select Folder", command=self.select_folder)
        self.select_button.pack(pady=5)

        self.canvas = tk.Canvas(root, width=512, height=512, bg='gray')
        self.canvas.pack()

        self.scrollbar = tk.Scale(root, from_=0, to=0, orient=tk.HORIZONTAL, label="Layer", command=self.change_layer)
        self.scrollbar.pack(fill=tk.X, padx=10, pady=5)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack()

        self.prev_button = tk.Button(self.button_frame, text="Previous", command=self.previous_image)
        self.prev_button.grid(row=0, column=0, padx=5)

        self.next_button = tk.Button(self.button_frame, text="Next", command=self.next_image)
        self.next_button.grid(row=0, column=1, padx=5)

        # State
        self.image_paths = []
        self.current_index = 0
        self.current_tiff = None
        self.current_layer = 0
        self.tk_image = None

    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        self.image_paths = [os.path.join(folder, f) for f in os.listdir(folder)
                            if f.lower().endswith(('.tif', '.tiff'))]
        self.image_paths.sort()
        if not self.image_paths:
            messagebox.showerror("No TIFFs Found", "No .tif or .tiff files found in the selected folder.")
            return

        self.current_index = 0
        self.load_image()

    def load_image(self):
        try:
            if self.current_tiff:
                self.current_tiff.close()

            image_path = self.image_paths[self.current_index]
            self.current_tiff = Image.open(image_path)

            # Count layers (frames/pages)
            self.layer_count = 1
            try:
                while True:
                    self.current_tiff.seek(self.layer_count)
                    self.layer_count += 1
            except EOFError:
                pass

            self.scrollbar.config(to=self.layer_count - 1)
            self.current_layer = 0
            self.scrollbar.set(0)

            self.display_layer(0)
            self.root.title(f"{os.path.basename(image_path)} ({self.current_index + 1}/{len(self.image_paths)})")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def display_layer(self, layer_index):
        try:
            self.current_tiff.seek(layer_index)
            img = self.current_tiff.copy()
            img.thumbnail((512, 512))
            self.tk_image = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(256, 256, image=self.tk_image)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display layer: {e}")

    def change_layer(self, value):
        layer_index = int(value)
        if layer_index < self.layer_count:
            self.current_layer = layer_index
            self.display_layer(layer_index)

    def previous_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()

    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_image()

if __name__ == "__main__":
    root = tk.Tk()
    app = TiffViewerApp(root)
    root.mainloop()
