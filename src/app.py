import threading
from argparse import ArgumentError

import cv2
import numpy as np
import tkinter as tk
import src.searcher
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

SIZE_RATIO = 0.75
CIR_SIZE = 3
LINE_WIDTH = 2


class ImageViewer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Image Viewer")
        self.resizable(False, False)

        # main frame
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')

        # image label
        self.image_label = tk.Label(self.main_frame)
        self.image_label.pack(expand=True, fill='both', padx=10, pady=10)
        self.image_label.bind('<Button-1>', self.on_click)

        # button frame
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(fill='x', padx=5, pady=5)

        # Create buttons
        self.open_button = tk.Button(self.button_frame, text="Open",
                                     command=self.open_image)
        self.open_button.pack(side='left', padx=5)

        self.save_button = tk.Button(self.button_frame, text="Save",
                                     command=self.save)
        self.save_button.pack(side='left', padx=5)
        self.save_button.configure(state='disabled')

        self.clear_button = tk.Button(self.button_frame, text="Clear",
                                      command=self.clear)
        self.clear_button.pack(side='left', padx=5)
        self.clear_button.configure(state='disabled')

        self.cancel_search_button = (
            tk.Button(self.button_frame, text="Cancel Search",
                      command=self.cancel_search))
        self.cancel_search_button.pack(side='left', padx=5)
        self.cancel_search_button.configure(state='disabled')

        self.curr_image = None
        self.orig_image = None
        self.searching = 0
        self.lock = threading.Lock()
        self.searcher = src.searcher.Searcher()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = int(screen_width * SIZE_RATIO)
        window_height = int(screen_height * SIZE_RATIO)
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2
        self.geometry(
            f"{window_width}x{window_height}+{position_x}+{position_y}")

    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tif *.tiff"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            # Open and display the image
            image = Image.open(file_path)

            # Resize image if it's too large (maintaining aspect ratio)
            display_size = (800, 600)  # Maximum display size
            image.thumbnail(display_size, Image.Resampling.LANCZOS)

            # Update the label with new image
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.curr_image = image, photo  # Keep a reference
            self.orig_image = image, photo
            self.cancel_search()
            self.clear_button.configure(state='disabled')
            self.save_button.configure(state='disabled')

            data = np.array(image)
            print(data)
            print("Shape:", data.shape)

    def save(self):
        if not self.curr_image: return

        if self.searching:
            messagebox.showwarning("Searches ongoing",
                                   "One or more searches are ongoing.\n"
                                   "Wait or cancel them before saving.")
            return

        image, _ = self.curr_image
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg;*.jpeg"),
                ("BMP files", "*.bmp"),
                ("GIF files", "*.gif"),
                ("TIFF files", "*.tif;*.tiff"),
                ("WebP files", "*.webp"),
                ("ICO files", "*.ico"),
                ("PPM files", "*.ppm"),
                ("PGM files", "*.pgm"),
                ("PBM files", "*.pbm"),
                ("EPS files", "*.eps"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            try:
                image.save(file_path)
                messagebox.showinfo("Success", "Image saved at"
                                               f"\n{file_path}\n"
                                               "successfully.")
            except OSError as e:
                messagebox.showerror("Error", "An error occured while saving:"
                                              f"\n{str(e)}")

    def clear(self):
        if not self.orig_image: return
        _, photo = self.orig_image
        self.image_label.configure(image=photo)
        self.curr_image = self.orig_image
        self.cancel_search()
        self.clear_button.configure(state='disabled')
        self.save_button.configure(state='disabled')

    def cancel_search(self):
        with self.lock:
            self.searching = 0
            self.searcher.canceled = True
            self.cancel_search_button.configure(state='disabled')

    def on_click(self, event):
        try:
            x, y, image = self._get_coor_on_clicked(event)
        except ArgumentError:
            return

        data = np.array(image)

        with self.lock:
            self.searcher.add((x, y))
            cv2.circle(data, (x, y), CIR_SIZE, (0, 0, 0), -1)
            self.search_stack.push(src.stack.SearchResult([(x, y)], 0, data))
            self._draw(data)
            self.undo_button.configure(state='normal')
            self.save_button.configure(state='normal')
            self.clear_button.configure(state='normal')
            print(f"Click detected at x={x}, y={y}")

            if len(self.searcher.clicks) > 1:
                self.searching = 1
                self.after_idle(
                    lambda: self.cancel_search_button.configure(state='normal'))

                search_thread = threading.Thread(
                    target=self._search, args=(np.array(self.orig_image[0]),))
                search_thread.daemon = True
                search_thread.start()

    def _draw(self, data):
        image = Image.fromarray(data)
        photo = ImageTk.PhotoImage(image)  # Convert to PhotoImage
        self.image_label.configure(image=photo)
        self.curr_image = image, photo  # Keep a reference

    def _get_coor_on_clicked(self, event):
        try:
            image, _ = self.curr_image
            orig_height, orig_width = np.array(image).shape[:2]
        except (TypeError, ValueError):
            raise ArgumentError(None, "")

        photo_width = image.width
        photo_height = image.height

        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()

        pad_x = (label_width - photo_width) // 2
        pad_y = (label_height - photo_height) // 2

        photo_x = event.x - pad_x
        photo_y = event.y - pad_y

        width_scale = orig_width / photo_width
        height_scale = orig_height / photo_height

        x = int(photo_x * width_scale)
        y = int(photo_y * height_scale)

        if x < 0 or y < 0 or x >= orig_height or y >= orig_width:
            raise ArgumentError(None, "")

        return x, y, image

    def _search(self, orig):
        try:
            line = self.searcher.search(orig)
            with self.lock:
                if line and not self.searcher.canceled:
                    data = np.array(self.curr_image[0])
                    points = np.array(line)
                    cv2.polylines(data, [points], False, (0, 0, 0), LINE_WIDTH)
                    # Store result in stack
                    self.after_idle(self.search_stack.push,
                                    (src.stack.SearchResult(line, 1, data)))
                    self.after_idle(self._draw, data)
        finally:
            with self.lock:
                self.searching = 0
                self.after_idle(lambda: self.cancel_search_button.configure(
                    state='disabled'))

    def _check_searching(self):
        if not self.searching:
            self.cancel_search_button.configure(state='disabled')
