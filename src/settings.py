import tkinter as tk


class Settings:
    def __init__(self):
        # Class attributes
        self.line_thickness = 1
        self.circle_radius = 3
        self.circle_color = (255, 0, 0)
        self.line_color = (255, 0, 0)
        self.area_color = (255, 0, 0)
        self.weight_factor = 2
        self.closed = True

    def show_window(self, root):
        self.closed = False

        self.window = tk.Toplevel(root)
        self.window.title("Settings")
        self.window.resizable(False, False)

        tk.Label(self.window, text="Line thickness").pack()
        self.line_slider = tk.Scale(self.window, from_=1, to=10,
                                    orient='horizontal',
                                    command=lambda val:
                                    setattr(self, "line_thickness", int(val)))
        self.line_slider.set(self.line_thickness)
        self.line_slider.pack()

        tk.Label(self.window, text="Circle radius").pack()
        self.circle_slider = tk.Scale(self.window, from_=1, to=10,
                                      orient='horizontal',
                                      command=lambda val:
                                      setattr(self, "circle_radius", int(val)))
        self.circle_slider.set(self.circle_radius)
        self.circle_slider.pack()

        tk.Label(self.window, text="Circle color").pack()

        tk.Label(self.window, text="R").pack()
        self.circle_r_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "circle_color",
                                                (int(val), self.circle_color[1],
                                                 self.circle_color[2])))
        self.circle_r_slider.set(self.circle_color[0])
        self.circle_r_slider.pack()

        tk.Label(self.window, text="G").pack()
        self.circle_g_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "circle_color",
                                                (self.circle_color[0], int(val),
                                                 self.circle_color[2])))
        self.circle_g_slider.set(self.circle_color[1])
        self.circle_g_slider.pack()

        tk.Label(self.window, text="B").pack()
        self.circle_b_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "circle_color",
                                                (self.circle_color[0],
                                                 self.circle_color[1],
                                                 int(val))))
        self.circle_b_slider.set(self.circle_color[2])
        self.circle_b_slider.pack()

        tk.Label(self.window, text="Line color").pack()

        tk.Label(self.window, text="R").pack()
        self.circle_r_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "line_color",
                                                (int(val), self.line_color[1],
                                                 self.line_color[2])))
        self.circle_r_slider.set(self.line_color[0])
        self.circle_r_slider.pack()

        tk.Label(self.window, text="G").pack()
        self.circle_g_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "line_color",
                                                (self.line_color[0], int(val),
                                                 self.line_color[2])))
        self.circle_g_slider.set(self.line_color[1])
        self.circle_g_slider.pack()

        tk.Label(self.window, text="B").pack()
        self.circle_b_slider = tk.Scale(self.window, from_=0, to=255,
                                        orient='horizontal',
                                        command=lambda val:
                                        setattr(self, "line_color",
                                                (self.line_color[0],
                                                 self.line_color[1], int(val))))
        self.circle_b_slider.set(self.line_color[2])
        self.circle_b_slider.pack()

        tk.Label(self.window, text="Weight factor (wavefront)").pack()
        self.weight_factor_slider = tk.Scale(self.window, from_=1., to=3.,
                                             resolution=0.1,
                                             orient='horizontal',
                                             command=lambda val:
                                             setattr(self, "weight_factor",
                                                     float(val)))
        self.weight_factor_slider.set(self.weight_factor)
        self.weight_factor_slider.pack()

        tk.Button(self.window, text="Close",
                  command=lambda: [self.window.destroy(),
                                   setattr(self, "closed", True)]).pack()

        return self.window
