import numpy as np


class GraphAnalyzer:
    def __init__(self):
        self.window_size = 20
        self.last = None

    def moving_average(self, data):
        """
        Compute the moving average of a 1D array using a specified window size.
        """
        data = np.array(data)
        if self.window_size < 1:
            raise ValueError("window_size should be at least 1")
        if self.window_size > len(data):
            raise ValueError(
                "window_size should not be larger than the length of the data")
        return list(
            np.convolve(data, np.ones(self.window_size) / self.window_size,
                        mode='valid'))

    @staticmethod
    def first_derivative_at_x(x, y, target_x):
        x = np.array(x)
        y = np.array(y)
        idx = np.abs(x - target_x).argmin()
        if idx < 1 or idx > len(x) - 2:
            raise ValueError(f"{target_x} is too close to the boundaries")
        dy_dx = (y[idx + 1] - y[idx - 1]) / (x[idx + 1] - x[idx - 1])
        return dy_dx

    def max_sum(self, l):
        """
        Runs ``_max_sum`` twice, once in an inverted order to allow a strictly
        decreasing selection.
        """
        increasing = self._max_sum(l)
        tmp = self._max_sum(l[::-1])
        decreasing = tmp[0][::-1], tmp[1]
        res = max(increasing, decreasing, key=lambda x: x[1])[0]
        self.last = res
        return res

    @staticmethod
    def _max_sum(l):
        """
        Given ``l``, find the indices of chosen values in each image such
        that the sum of the chosen values is maximized, under the constraint
        that exactly one value is chosen in each image, and that the indices
        have to be strictly increasing.

        Let ``OPT(i, j)`` be the maximum sum of the values in the submatrix of
        data. Then

        ``OPT(i, j) = max(OPT(i + 1, k) + l[i][j] for k in range(j + 1, c))``

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
                    tmp = m[i + 1][k] + l[i][j]
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
        indices = [(i, j)]
        while j != -1:
            j = path[i][j]
            i += 1
            indices.append((i, j))

        return indices, max_value
