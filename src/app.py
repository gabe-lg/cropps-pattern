import cv2
import numpy as np
import os
import threading
import tkinter as tk
import src.history
import src.searcher
from argparse import ArgumentError
from lib.doubly_linked_list import DoublyLinkedList, DoublyLinkedNode
from lib.point import Point, PointNode
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog, messagebox
from typing import Tuple
from PIL import Image, ImageFile, ImageTk

SIZE_RATIO = 0.75
CIR_SIZE = 3
LINE_WIDTH = 2


class ImageNode(DoublyLinkedNode[Tuple[ImageFile.ImageFile, int]]): pass


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
        self.main_pane = tk.PanedWindow(self, orient="horizontal")
        self.main_pane.pack(fill="both", expand=True)

        # image + arrows frame
        self.content_frame = tk.Frame(self.main_pane, bg="lightgray")
        self.main_pane.add(self.content_frame)

        # graph frame
        self.graph_frame = tk.Frame(self.main_pane, bg="white")
        self.main_pane.add(self.graph_frame)

        self.brightness_graph_frame = tk.Frame(self.graph_frame)
        self.brightness_graph_frame.pack(fill='both',
                                         expand=True, padx=20, pady=20)

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

        self.pause_button = (
            tk.Button(self.button_frame, text="Pause",
                      command=lambda:
                      setattr(self, "playing", not self.playing)))
        self.pause_button.pack(side='right', padx=5)

        self.play_button = (
            tk.Button(self.button_frame, text="Play",
                      command=lambda:
                      threading.Thread(target=self._play).start()))
        self.play_button.pack(side='right', padx=5)

        self.image_list = ImageList()
        self.curr_image = None
        self.orig_image = None
        self.lock = threading.Lock()

        self.playing = False
        self.searching = 0
        self.searcher = src.searcher.Searcher(self.lock)
        self.history = src.history.History()

        self.brightness_canvas = None
        self.graph = None

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
        self.image_list.goto(res.value.image_id)
        self._config_button()

    def redo(self):
        self.searcher.redo()
        self._draw(self.history.redo().value.data)
        self._config_button()

    def open(self, is_folder: bool):
        """ :param is_folder: ``True`` iff the open folder button is clicked. """
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
        if self.history.peek().value:
            self.clear()  # do not clear if no original image
        self.history.clear()
        self.image_list.clear()

        # push images to list
        if is_folder:
            self.image_list.push_all(
                [f[2] for f in sorted(
                    [(os.path.getmtime(os.path.join(file_path, f)), i,
                      ImageNode((Image.open(os.path.join(file_path, f)), i)))
                     for i, f in enumerate(os.listdir(file_path))
                     if f.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif",
                         ".tiff"))])])
        else:
            self.image_list.push(ImageNode((Image.open(file_path), 0)))

        # Open and display the image
        self.image_list.init()  # navigate to the start of the list
        try:
            image = self.image_list.next().value[0]
        except IndexError:
            self.image_label.configure(image=tk.PhotoImage())
            messagebox.showerror("Open folder",
                                 "This folder does not contain any image files.")
            return

        # Update the label with new image
        self._change_image(image)
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
        self.cancel_search()
        self.searcher.clear(is_button)
        self.history.undo_all(is_button)
        self._draw(self.history.peek().value.data)
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
        if not self.image_list.curr_at_first():
            self._change_image(self.image_list.prev().value[0])

    def next_image(self):
        self._change_image(self.image_list.next().value[0])

    def first_image(self):
        self.image_list.init()
        self.next_image()

    def last_image(self):
        self._change_image(self.image_list.last().value[0])

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
            action = self.history.push(src.history.Action(
                [(x, y)], data, self.image_list.peek().value[1]))
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

    def _change_image(self, image: ImageFile.ImageFile):
        # Resize image if it's too large (maintaining aspect ratio)
        display_size = (800, 600)  # Maximum display size
        image.thumbnail(display_size, Image.Resampling.LANCZOS)

        data = np.array(image)
        self.orig_image = image.copy(), ImageTk.PhotoImage(image)
        for p in self.searcher.clicks:
            cv2.circle(data, p.value, CIR_SIZE, (0, 0, 0), -1)
        cv2.polylines(data, [np.array(self.searcher.reconstruct_line())], False,
                      (0, 0, 0), LINE_WIDTH)
        self._draw(data)
        self._config_button()

    def _config_button(self):
        if (self.image_list.curr_at_first() or self.image_list.is_empty()
                or self.playing):
            self.prev_button.configure(state='disabled')
            self.first_button.configure(state='disabled')
        else:
            self.prev_button.configure(state='normal')
            self.first_button.configure(state='normal')

        if self.image_list.curr_at_tail() or self.playing:
            self.next_button.configure(state='disabled')
            self.last_button.configure(state='disabled')
        else:
            self.next_button.configure(state='normal')
            self.last_button.configure(state='normal')

        if (self.history.curr_has_prev() and not self.searching
                and not self.playing):
            self.undo_button.configure(state='normal')
        else:
            self.undo_button.configure(state='disabled')

        if (self.history.curr_has_next() and not self.searching
                and not self.playing):
            self.redo_button.configure(state='normal')
        else:
            self.redo_button.configure(state='disabled')

        if self.history.is_init_state() or self.playing:
            self.save_button.configure(state='disabled')
            self.clear_button.configure(state='disabled')
        else:
            self.save_button.configure(state='normal')
            self.clear_button.configure(state='normal')

        if self.searching and not self.playing:
            self.cancel_search_button.configure(state='normal')
        else:
            self.cancel_search_button.configure(state='disabled')

        if self.playing:
            self.play_button.configure(state='disabled')
            self.pause_button.configure(state='normal')
        else:
            self.play_button.configure(state='normal')
            self.pause_button.configure(state='disabled')

        if self.image_list.is_empty() or self.searching or self.image_list.curr_at_tail():
            self.play_button.configure(state='disabled')
            self.pause_button.configure(state='disabled')

    def _draw(self, data, invis=0):
        image = Image.fromarray(data)
        photo = ImageTk.PhotoImage(image)  # Convert to PhotoImage
        self.image_label.configure(image=photo)
        self.curr_image = image, photo  # Keep a reference
        self.after_idle(self._plot_brightness, np.array(self.orig_image[0]))

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
                            src.history.Action(line, data,
                                               self.image_list.peek().value[
                                                   1]))))
                    self.after_idle(self._draw, data)
        finally:
            with self.lock:
                self._config_button()
                self.searching -= 1
                self._config_button()

    def _play(self):
        self.playing = True
        self._config_button()
        while self.playing and not self.image_list.curr_at_tail():
            self.next_image()
        self.playing = False
        self._config_button()

    def _plot_brightness(self, data):
        # Process data for brightness plot
        data = np.clip(255 * (data / np.max(data)), 0, 255)
        data = np.mean(data, axis=2) if len(data.shape) == 3 else data

        brightness_values = [
            v if 0 <= v <= 255
            else (_ for _ in ()).throw(ValueError(f"Invalid brightness {v}"))
            for p in self.searcher.reconstruct_line()
            for v in [data[*p._]]
        ]

        if self.brightness_canvas is None:
            # First time: create figure and canvas
            self.graph = fig, _ = plt.subplots()
            self.brightness_canvas = FigureCanvasTkAgg(
                fig, master=self.brightness_graph_frame)
            self.brightness_canvas.get_tk_widget().pack(
                fill="both", expand=True)

        fig, ax = self.graph
        ax.clear()
        fig.tight_layout()
        ax.set_xlabel('Number of pixels from origin')
        ax.set_ylabel('Brightness')
        ax.set_title('Brightness Along Selected Line')
        ax.set_ylim(0, 255)
        ax.plot(
            range(len(brightness_values)), brightness_values)
        self.brightness_canvas.draw()
