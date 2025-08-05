import tkinter as tk


class Settings:
    def __init__(self):
        # Class attributes
        self.line_thickness = 1
        self.circle_radius = 3
        self.circle_color = (255, 0, 0)
        self.line_color = (255, 0, 0)
        self.area_color = (255, 0, 0)
        self.closed = True

    def show_window(self, root):
        self.closed = False

        self.window = tk.Toplevel(root)
        self.window.title("Settings")
        self.window.geometry("300x1000")
        self.window.resizable(False, False)

        tk.Label(self.window, text="Line thickness").pack()
        self.line_slider = tk.Scale(self.window, from_=1, to=10,
                                    orient='horizontal',
                                    command=lambda val:
                                    setattr(self, "line_thickness", int(val)))
        self.line_slider.set(1)
        self.line_slider.pack()

        tk.Label(self.window, text="Circle radius").pack()
        self.circle_slider = tk.Scale(self.window, from_=1, to=10,
                                      orient='horizontal',
                                      command=lambda val:
                                      setattr(self, "circle_radius", int(val)))
        self.circle_slider.set(3)
        self.circle_slider.pack()

        tk.Label(self.window, text="Circle color").pack()
        self.circle_r_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "circle_color",
                                                (int(val), self.circle_color[1],
                                                 self.circle_color[2])))
        self.circle_r_slider.set(255)
        self.circle_r_slider.pack()

        self.circle_g_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "circle_color",
                                                (self.circle_color[0], int(val), self.circle_color[2])))
        self.circle_g_slider.set(0)
        self.circle_g_slider.pack()

        self.circle_b_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "circle_color",
                                                (self.circle_color[0], self.circle_color[1], int(val))))
        self.circle_b_slider.set(0)
        self.circle_b_slider.pack()

        tk.Label(self.window, text="Line color").pack()
        self.circle_r_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "line_color",
                                                (int(val), self.line_color[1],self.line_color[2])))
        self.circle_r_slider.set(255)
        self.circle_r_slider.pack()

        self.circle_g_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "line_color",
                                                (self.line_color[0], int(val), self.line_color[2])))
        self.circle_g_slider.set(0)
        self.circle_g_slider.pack()

        self.circle_b_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "line_color",
                                                (self.line_color[0], self.line_color[1], int(val))))
        self.circle_b_slider.set(0)
        self.circle_b_slider.pack()

        tk.Button(self.window, text="Close",
                  command=lambda: [self.window.destroy(),
                                   setattr(self, "closed", True)]).pack()

        return self.window
