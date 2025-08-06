import csv
from tkinter import filedialog, messagebox

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import convolve2d


class GraphAnalyzer:
    def __init__(self):
        self.window_size = 20
        self.sigma = 5
        self.last = None
        self.line = None
        self.mode = 0

    def moving_average(self, data):
        """
        Compute the moving average of a 1D array using a specified window size.
        """
        if self.mode == 3:
            return gaussian_filter1d(data, self.sigma)

        data = np.array(data)
        if self.window_size < 1:
            raise ValueError("window_size should be at least 1")
        if self.window_size > len(data):
            raise ValueError(
                "window_size should not be larger than the length of the data")
        res = list(
            np.convolve(data, np.ones(self.window_size) / self.window_size,
                        mode='valid'))

        if self.mode == 0: return -np.gradient(res)
        if self.mode == 1: return res
        if self.mode == 2: return res * -np.gradient(res)

        # garbage
        return data

    @staticmethod
    def first_derivative_at_x(x, y, target_x):
        x = np.array(x)
        y = np.array(y)
        idx = np.abs(x - target_x).argmin()
        if idx < 1 or idx > len(x) - 2:
            raise ValueError(f"{target_x} is too close to the boundaries")
        dy_dx = (y[idx + 1] - y[idx - 1]) / (x[idx + 1] - x[idx - 1])
        return dy_dx

    @staticmethod
    def take_avg(image, radius) -> np.ndarray:
        size = radius * 2 + 1
        center = radius
        y, x = np.ogrid[:size, :size]
        mask = (x - center) ** 2 + (y - center) ** 2 <= radius ** 2

        kernel = np.zeros((size, size))
        kernel[mask] = 1
        kernel /= kernel.sum()  # normalize so it's an average

        # Convolve image with circular (disk-like) kernel
        avg_image = convolve2d(image, kernel, mode='same', boundary='symm')
        return avg_image

    def max_sum(self, l, weight_factor):
        """
        Runs ``_max_sum`` twice, once in an inverted order to allow a strictly
        decreasing selection.
        """
        is_increasing = (self._max_sum(l, 0.)[1] >
                         self._max_sum([line[::-1] for line in l], 0.)[1])
        increasing = self._max_sum(l, weight_factor)
        tmp = self._max_sum([line[::-1] for line in l], weight_factor)
        decreasing = [(entry[0], len(l[0]) - entry[1]) for entry in tmp[0]], tmp[1]
        res = increasing if is_increasing else decreasing
        res = np.array(res[0])
        error = self.window_size // 2 if self.mode != 3 else 0
        res = [(k[0] + 1, k[1] + error) for k in res]
        self.last = res

        if messagebox.askyesno("Save File", "Save output as a CSV file?"):
            try:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")])

                if file_path:
                    with open(file_path, mode='w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(("Image number",
                                         "Number of pixels from origin"))
                        writer.writerows(res)

                    messagebox.showinfo("Success", "Image saved at"
                                                   f"\n{file_path}\n"
                                                   "successfully.")

            except OSError as e:
                messagebox.showerror(
                    "Error", f"An error occurred while saving graphs:\n{str(e)}")

        return res

    @staticmethod
    def _max_sum(l, a):
        """
        Given ``l``, find the indices of chosen values in each image such
        that the sum of the chosen values is maximized, under the constraint
        that exactly one value is chosen in each image, and that the indices
        have to be strictly increasing.

        Let ``OPT(i, j)`` be the maximum sum of the values in the submatrix of
        data. Then

        ``OPT(i, j) = max(OPT(i + 1, k) + l[i][j] + aj for k in range(j + 1, c))``

        :param l: a 2D array with images as rows and number of pixels from the
         origin as columns
        """
        r, c = len(l), len(l[0])
        print(f"Finding the maximum values in {r} images, "
              f"each with a line of {c} pixels")

        m = np.full((r, c), -1)
        path = np.full((r, c), -1)

        for j in range(c):
            m[r - 1][j] = l[r - 1][j]

        for i in range(r - 2, -1, -1):
            for j in range(c):
                for k in range(j + 1, c):
                    tmp = m[i + 1][k] + l[i][j] + a * j
                    if tmp > m[i][j]:
                        m[i][j] = tmp
                        path[i][j] = k

        max_value = -1
        max_pos = -1
        for j in range(c):
            if m[0][j] > max_value:
                max_value = m[0][j]
                max_pos = j

        i, j = 0, max_pos
        indices = []
        while j != -1:
            indices.append((i, j))
            j = path[i][j]
            i += 1

        return indices, max_value
