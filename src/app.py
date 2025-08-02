import cv2
import numpy as np
import os
import threading
import tkinter as tk
import queue
import src.history
import src.line_tracers
from argparse import ArgumentError
from lib.doubly_linked_list import DoublyLinkedList, DoublyLinkedNode
from lib.point import Point
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.line_tracers import LineTracerTypes as ltt
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

        self.mouse_coor = queue.LifoQueue()
        self.bind('<Motion>', lambda e: self.on_motion(e))

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

        self.brightness_graph_frame.bind('<MouseWheel>', self.on_scroll_graph)

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
        self.button_down = False
        self.image_label.bind('<Button-1>', lambda e:
        [self.on_click(e), setattr(self, "button_down", True)])
        self.image_label.bind('<ButtonRelease-1>',
                              lambda _: setattr(self, "button_down", False))

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
            tk.Button(self.button_frame, text="Clear", command=self.clear))
        self.clear_button.pack(side='left', padx=5)

        self.cancel_search_button = (
            tk.Button(self.button_frame, text="Cancel Search",
                      command=self.cancel_search))
        self.cancel_search_button.pack(side='left', padx=5)

        ###
        self.brightness_slider = tk.Scale(self.button_frame, from_=0, to=1000,
                                          orient='horizontal',
                                          label="Brightness",
                                          command=lambda _: self._draw())
        self.brightness_slider.set(100)
        self.brightness_slider.pack(side='left', padx=5)

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

        self.line_tracer_button = tk.Menubutton(self.button_frame,
                                                text="Change Tool...")
        self.line_tracer_menu = tk.Menu(self.line_tracer_button, tearoff=0)
        self.line_tracer_button.config(menu=self.line_tracer_menu)
        self.line_tracer_menu.add_command(
            label="Straight line tool",
            command=lambda: self.line_tracers.set_curr_type(ltt.LINE))
        self.line_tracer_menu.add_command(
            label="Freehand tool",
            command=lambda: self.line_tracers.set_curr_type(ltt.FREE))
        self.line_tracer_menu.add_command(
            label="Brightest path searcher",
            command=lambda: self.line_tracers.set_curr_type(ltt.BRIGHTEST))
        self.line_tracer_button.pack(side='right', padx=5)

        self.y_slider = tk.Scale(self.button_frame, from_=1,
                                 to=np.iinfo(np.uint16).max,
                                 orient='horizontal',
                                 label="y-axis upper limit",
                                 length=200,
                                 command=lambda _: self._set_ylim_graph())
        self.y_slider.set(1023)
        self.y_slider.pack(side='right', padx=5)

        self.image_list = ImageList()
        self.curr_image = None
        self.orig_image = None
        self.lock = threading.Lock()

        self.playing = False
        self.searching = 0
        self.line_tracers = src.line_tracers.LineTracers(ltt.LINE)
        self.history = src.history.PointsList()

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
        self.update()
        self.main_pane.sash_place(0, int(self.winfo_width() * 0.7), 0)

    def undo(self):
        self.history.prev()
        self._draw()
        self._config_button()

    def redo(self):
        self.history.next()
        self._draw()
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
        self.history.clear()
        self.image_list.clear()

        # push images to list
        if is_folder:
            self.image_list.push_all(
                [ImageNode(Image.open(os.path.join(file_path, f)))
                 for i, f in enumerate(sorted(
                    [f for f in os.listdir(file_path)
                     if f.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif",
                         ".tiff"))],
                    key=lambda x: os.path.getmtime(os.path.join(file_path, x))))
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

        # Update the label with new image
        self._change_image(image)
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
                image.save(file_path, "I;16")
                messagebox.showinfo("Success", "Image saved at"
                                               f"\n{file_path}\n"
                                               "successfully.")
            except OSError as e:
                messagebox.showerror("Error", "An error occurred while saving:"
                                              f"\n{str(e)}")

    # def to_csv(self):
    #     for image in self.image_list:
    #         filename = f'intensity_values{image.value[1]}.csv'
    #         with open(filename, mode='w', newline='') as file:
    #             writer = csv.writer(file)
    #             writer.writerows(np.array(image.value[0]))
    #         print(f"Saved intensity values to {filename}")

    def clear(self):
        self.cancel_search()
        self.history.undo_all()
        self._draw()
        self._config_button()
        print("Cleared annotations")

    def cancel_search(self):
        with self.lock:
            self.searching = 0
            # self.searcher.canceled = True
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
            self._change_image(self.image_list.prev().value)

    def next_image(self):
        self._change_image(self.image_list.next().value)

    def first_image(self):
        self.image_list.init()
        self.next_image()

    def last_image(self):
        self._change_image(self.image_list.last().value)

    def on_click(self, event):
        try:
            x, y, image = self._get_coor(event)
        except ArgumentError:
            return

        with self.lock:
            action_node = src.history.ActionNode(
                src.history.Action(Point(x, y)))
            self.history.push(action_node)
            self.searching += 1

        # now do UI updates and start thread outside the lock
        self._draw()
        self._config_button()

        if self.searching:
            threading.Thread(
                target=self._search,
                args=(np.array(self.orig_image[0]), action_node),
                daemon=True).start()

    def on_motion(self, event):
        if self.line_tracers.curr_type != ltt.FREE: return

        if not self.button_down:
            self.mouse_coor.put(Point(np.inf, np.inf))
            return

        try:
            self.mouse_coor.put(Point(*self._get_coor(event)[:2]))
        except ArgumentError:
            pass

    def on_scroll_graph(self, event):
        if event.delta > 0:
            self.y_slider.set(self.y_slider.get() + 10)
        else:
            self.y_slider.set(self.y_slider.get() - 10)
        self._plot_brightness()

    def _change_image(self, image: ImageFile.ImageFile):
        # Resize image if it's too large (maintaining aspect ratio)
        display_size = (800, 600)  # Maximum display size
        image.thumbnail(display_size, Image.Resampling.LANCZOS)

        self.orig_image = image.copy(), ImageTk.PhotoImage(image)
        self._draw()
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

        if not (self.history.curr_at_init() or self.searching
                or self.playing):
            self.undo_button.configure(state='normal')
        else:
            self.undo_button.configure(state='disabled')

        if self.history.has_next() and not (self.searching
                                            or self.playing):
            self.redo_button.configure(state='normal')
        else:
            self.redo_button.configure(state='disabled')

        if self.history.curr_at_init() or self.history.cleared or self.playing:
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

            self.brightness_slider.configure(state='disabled')
            self.y_slider.configure(state='disabled')
            self.line_tracer_button.configure(state='disabled')
        else:
            self.play_button.configure(state='normal')
            self.pause_button.configure(state='disabled')

            self.brightness_slider.configure(state='normal')
            self.y_slider.configure(state='normal')
            self.line_tracer_button.configure(state='normal')

        if self.image_list.is_empty() or self.searching or self.image_list.curr_at_tail():
            if self.image_list.curr_at_tail():
                self.play_button.configure(state='normal')
            else:
                self.play_button.configure(state='disabled')
            self.pause_button.configure(state='disabled')

    def _draw(self):
        if self.image_list.is_empty(): return

        brightness = self.brightness_slider.get() / 100
        data = np.array(self.image_list.peek().value)
        max_data = data.max() if data.max() else 1
        data = np.clip(data / max_data * 255 * brightness, 0, 255)

        for circle in self.history.get_circles():
            cv2.circle(data, circle, CIR_SIZE, (0, 0, 0), -1)
        cv2.polylines(data, self.history.get_lines(), False, (0, 0, 0),
                      LINE_WIDTH)

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

    def _search(self, orig_image, action_node):
        print("")
        if self.line_tracers.curr_type == ltt.FREE:
            while self.button_down: print("")

        try:
            if (not action_node.prev.value and
                    self.line_tracers.curr_type != ltt.FREE): return
            line = self.line_tracers.get_line_tracer.trace(
                action_node.prev.value.point if action_node.prev.value else None,
                action_node.value.point, np.array(orig_image), self.mouse_coor)

            with self.lock:
                if line:  # and not self.searcher.canceled:
                    data = np.array(self.image_list.peek().value.copy())
                    cv2.polylines(data, [np.array(line)], False, (0, 0, 0),
                                  LINE_WIDTH)

                    # Store result in stack
                    action_node.value.line = line
                    self.after_idle(self._draw)
        finally:
            with self.lock:
                self._config_button()
                self.searching -= 1
                self._config_button()

    def _set_ylim_graph(self):
        if not self.image_list.is_empty():
            data = np.array(self.image_list.peek().value)
            self.after_idle(self._plot_brightness, data)

    def _play(self):
        self.playing = True
        self._config_button()

        if self.image_list.curr_at_tail():
            # play from beginning
            self.image_list.init()

        while self.playing and not self.image_list.curr_at_tail():
            self.next_image()
        self.playing = False
        self._config_button()

    def _plot_brightness(self, data):
        data = np.mean(data, axis=2) if len(data.shape) == 3 else data

        brightness_values = [data[p[1], p[0]] for l in self.history.get_lines()
                             for p in l][::-1]

        if self.brightness_canvas is None:
            # First time: create figure and canvas
            self.graph = fig, _ = plt.subplots()
            self.brightness_canvas = FigureCanvasTkAgg(
                fig, master=self.brightness_graph_frame)
            self.brightness_canvas.get_tk_widget().pack(
                fill="both", expand=True)
            fig.tight_layout(pad=2)

        fig, ax = self.graph
        ax.clear()
        ax.set_xlabel('Number of pixels from origin')
        ax.set_ylabel('Brightness')
        ax.set_title('Brightness Along Selected Line')

        ylim = self.y_slider.get()
        if ylim is not None:
            ax.set_ylim(0, ylim)
        else:
            ax.set_ylim(0, 500)

        ax.plot(
            range(len(brightness_values)), brightness_values)
        self.brightness_canvas.draw()
