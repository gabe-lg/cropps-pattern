import cv2
import numpy as np
import os
import threading
import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import src.history
import src.searcher
from argparse import ArgumentError
from lib.doubly_linked_list import DoublyLinkedList, DoublyLinkedNode
from lib.point import Point, PointNode
from tkinter import filedialog, messagebox
from PIL import Image, ImageFile, ImageTk

SIZE_RATIO = 0.75
CIR_SIZE = 3
LINE_WIDTH = 2


class ImageNode(DoublyLinkedNode[ImageFile.ImageFile]): pass


class ImageList(DoublyLinkedList[ImageNode]): pass


class ImageViewer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Image Viewer")

        # keyboard shortcuts
        self.bind('<Left>', lambda _: self.prev_image())
        self.bind('<Right>', lambda _: self.next_image())
        self.bind('<Home>', lambda _: self.first_image())
        self.bind('<End>', lambda _: self.last_image())

        # paned window
        self.main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        # image + arrows frame
        self.content_frame = tk.Frame(self.main_pane, bg="lightgray")
        self.main_pane.add(self.content_frame)

        # graph frame
        self.graph_frame = tk.Frame(self.main_pane, bg="white")
        self.main_pane.add(self.graph_frame)

        self.brightness_graph_frame = tk.Frame(self.graph_frame)
        self.brightness_graph_frame.pack(fill='both',
                                         expand=True,padx=20, pady=20)

        self.main_pane.sash_place(0, int(self.winfo_width() * 0.7), 0)

        # left button frame
        self.left_button_frame = tk.Frame(self.content_frame, bd=2,
                                          relief='groove')
        self.left_button_frame.pack(side='left', anchor='center', padx=(0, 10))

        # right button frame
        self.right_button_frame = tk.Frame(self.content_frame, bd=2,
                                           relief='groove')
        self.right_button_frame.pack(
            side='right', anchor='center', padx=(0, 10))

        # image label
        self.image_label = tk.Label(self.content_frame)
        self.image_label.pack(expand=True, fill='both', padx=10, pady=10)
        self.image_label.bind('<Button-1>', self.on_click)

        # bottom button frame
        self.button_frame = tk.Frame(self)
        self.button_frame.pack(fill='x', padx=5, pady=5)

        # buttons
        self.first_button = (tk.Button(self.left_button_frame, text="<<",
                                       command=self.first_image))
        self.first_button.pack(side='left', padx=5)

        self.prev_button = (tk.Button(self.left_button_frame, text="<",
                                      command=self.prev_image))

        self.prev_button.pack(side='left', padx=5)

        self.next_button = (tk.Button(self.right_button_frame, text=">",
                                      command=self.next_image))
        self.next_button.pack(side='left', padx=5)

        self.last_button = (tk.Button(self.right_button_frame, text=">>",
                                      command=self.last_image))
        self.last_button.pack(side='left', padx=5)

        ###
        self.undo_button = tk.Button(self.button_frame, text="Undo",
                                     command=self.undo)
        self.undo_button.pack(side='left', padx=5)

        self.redo_button = tk.Button(self.button_frame, text="Redo",
                                     command=self.redo)
        self.redo_button.pack(side='left', padx=5)

        self.open_button = tk.Menubutton(self.button_frame, text="Open...")
        self.open_menu = tk.Menu(self.open_button, tearoff=0)
        self.open_button.config(menu=self.open_menu)
        self.open_menu.add_command(
            label="Open file", command=lambda: self.open(is_folder=False))
        self.open_menu.add_command(
            label="Open folder", command=lambda: self.open(is_folder=True))
        self.open_button.pack(side='left', padx=5)

        self.save_button = tk.Button(self.button_frame, text="Save",
                                     command=self.save)
        self.save_button.pack(side='left', padx=5)

        self.clear_button = (
            tk.Button(self.button_frame, text="Clear",
                      command=lambda: self.clear(is_button=True)))
        self.clear_button.pack(side='left', padx=5)

        self.cancel_search_button = (
            tk.Button(self.button_frame, text="Cancel Search",
                      command=self.cancel_search))
        self.cancel_search_button.pack(side='left', padx=5)

        self.image_list = ImageList()
        self.curr_image = None
        self.orig_image = None
        self.lock = threading.Lock()

        self.searching = 0
        self.searcher = src.searcher.Searcher(self.lock)
        self.history = src.history.History()

        self._config_button()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = int(screen_width * SIZE_RATIO)
        window_height = int(screen_height * SIZE_RATIO)
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2
        self.geometry(
            f"{window_width}x{window_height}+{position_x}+{position_y}")

    def undo(self):
        res = self.history.undo()
        self.searcher.undo()
        if self.history.is_init_state():
            self.clear()
        else:
            self._draw(res.value.data)
        self._config_button()

        return res

    def redo(self):
        self.searcher.redo()
        self._draw(self.history.redo().value.data)
        self._config_button()

    def open(self, is_folder: bool):
        """ :param is_folder: True iff the open folder button is clicked. """
        if self.save_button['state'] == 'normal':
            if not messagebox.askokcancel("Open file",
                                          "Any edits to the current image "
                                          "will be lost. Proceed?"): return

        file_path = (filedialog.askdirectory() if is_folder else
                     filedialog.askopenfilename(
                         filetypes=[
                             ("Image files",
                              "*.png *.jpg *.jpeg *.gif *.bmp *.tif *.tiff"),
                             ("All files", "*.*")
                         ]
                     ))

        if not file_path: return

        self.cancel_search()
        self.clear()
        self.history.clear()
        self.image_list.clear()

        # push images to list
        if is_folder:
            self.image_list.push_all(
                [f[2] for f in sorted(
                    [(os.path.getmtime(os.path.join(file_path, f)), f,
                      ImageNode(Image.open(os.path.join(file_path, f))))
                     for f in os.listdir(file_path)
                     if f.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif",
                         ".tiff"))])
                 ])
        else:
            self.image_list.push(ImageNode(Image.open(file_path)))

        # Open and display the image
        self.image_list.init()  # navigate to the start of the list
        try:
            image = self.image_list.next().value
        except IndexError:
            self.image_label.configure(image=tk.PhotoImage())
            messagebox.showerror("Open folder",
                                 "This folder does not contain any image files.")
            return

        # Resize image if it's too large (maintaining aspect ratio)
        display_size = (800, 600)  # Maximum display size
        image.thumbnail(display_size, Image.Resampling.LANCZOS)

        # Update the label with new image
        photo = ImageTk.PhotoImage(image)
        self.image_label.configure(image=photo)
        self.curr_image = image, photo  # Keep a reference
        self.orig_image = image, photo
        self.history.init(np.array(image))
        self.cancel_search()
        self._config_button()

    def save(self):
        if not self.curr_image: return

        if self.searching:
            messagebox.showwarning("Searches ongoing",
                                   "Searches are ongoing.\n"
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

    def clear(self, is_button=False):
        if not self.orig_image: return
        _, photo = self.orig_image
        self.image_label.configure(image=photo)
        self.curr_image = self.orig_image
        if self.searching: self.cancel_search()
        self.searcher.clear(is_button)
        self.history.undo_all(is_button)
        self._config_button()
        print("Cleared annotations")

    def cancel_search(self):
        with self.lock:
            self.searching = 0
            self.searcher.canceled = True
            self._config_button()

        # Find the last line entry and restore to that state
        # while self.search_stack:
        #     last = self.search_stack.peek()
        #     if not last or last.is_line: break
        #
        #     # if it is not a line, undo
        #     self._undo()

    def prev_image(self):
        self._draw(self.image_list.prev().value)

    def next_image(self):
        self._draw(self.image_list.next().value)

    def first_image(self):
        self.image_list.init()
        self.next_image()

    def last_image(self):
        self._draw(self.image_list.last().value)

    def on_click(self, event, is_temp=0):
        try:
            x, y, image = self._get_coor(event)
        except ArgumentError:
            return

        data = np.array(image)
        print(f"Click detected at x={x}, y={y} with intensity "
              f"{data[y, x]}")

        with self.lock:
            self.searcher.push(self.searcher.clicks, PointNode(Point(x, y)))
            action = self.history.push(src.history.Action([(x, y)], data))
            self.searching += 1 if not self.searcher.clicks.curr_at_first() else 0

        # now do UI updates and start thread outside the lock
        cv2.circle(data, (x, y), CIR_SIZE, (0, 0, 0), -1)
        self._draw(data)
        self._config_button()

        if self.searching:
            threading.Thread(
                target=self._search,
                args=(np.array(self.orig_image[0]), action),
                daemon=True).start()

        self.after_idle(self._plot_brightness, np.array(self.orig_image[0]))

    def _config_button(self):
        if self.history.curr_has_prev() and not self.searching:
            self.undo_button.configure(state='normal')
        else:
            self.undo_button.configure(state='disabled')

        if self.history.curr_has_next() and not self.searching:
            self.redo_button.configure(state='normal')
        else:
            self.redo_button.configure(state='disabled')

        if self.history.is_init_state():
            self.save_button.configure(state='disabled')
            self.clear_button.configure(state='disabled')
        else:
            self.save_button.configure(state='normal')
            self.clear_button.configure(state='normal')

        if self.searching:
            self.cancel_search_button.configure(state='normal')
        else:
            self.cancel_search_button.configure(state='disabled')

    def _draw(self, data, invis=0):
        if not isinstance(data, (np.ndarray, ImageFile.ImageFile)):
            raise TypeError()

        image = Image.fromarray(data) if isinstance(data, np.ndarray) else data
        photo = ImageTk.PhotoImage(image)  # Convert to PhotoImage
        self.image_label.configure(image=photo)
        self.curr_image = image, photo  # Keep a reference

    def _get_coor(self, event):
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

        if x < 0 or y < 0 or x >= orig_width or y >= orig_height:
            raise ArgumentError(None, "")

        return x, y, image

    def _search(self, orig, action, thread_count=1):
        while thread_count < self.searching:
            if self.searcher.canceled: return

        try:
            visited = np.zeros(orig.shape[:2], dtype=bool)
            line = self.searcher.search(visited, orig)
            with self.lock:
                if line and not self.searcher.canceled:
                    data = self.history.peek().value.data
                    points = np.array(line)
                    cv2.polylines(data, [points], False, (0, 0, 0), LINE_WIDTH)

                    # Store result in stack
                    self.after_idle(
                        lambda: setattr(action, 'child', src.history.ActionNode(
                            src.history.Action(line, data))))
                    self.after_idle(self._draw, data)
        finally:
            with self.lock:
                self._config_button()
                self.searching -= 1
                self._config_button()

    def _plot_brightness(self, data):
        # Clear the frame if needed (optional)
        for widget in self.brightness_graph_frame.winfo_children():
            print("Graph: Destroying widget:", widget)
            widget.destroy()

        # Embed the plot into the tkinter frame
        canvas = FigureCanvasTkAgg(
            self.searcher.plot_brightness(data,
            Point(self.graph_frame.winfo_width(),
                  self.graph_frame.winfo_height())),
            master=self.brightness_graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
