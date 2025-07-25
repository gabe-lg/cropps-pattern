import heapq
import numpy as np
from lib.point import Point
from src.line_tracer import LineTracer
from typing import List, Optional, Tuple


class Searcher(LineTracer):
    """
    Stores points using a stack, then searches for the brightest and shortest
    path between the last two points.

    :ivar canceled: ``True`` iff user terminates search
    :ivar clicks: A ``DoublyLinkedList`` of points representing the position
     clicked by user
    :ivar all_lines: A ``DoublyLinkedList`` of lines returned by searcher
    """

    def __init__(self):
        super().__init__()
        self.canceled = False

    def trace(self, orig: Point, dest: Point, data: np.ndarray, *args) \
            -> Optional[List[Tuple[int, int]]]:
        """
        Returns the shortest path between ``orig = self.clicks[-2]`` and
        ``dest = self.clicks[-1]``, where edge weights are determined by
        ``_calc_weight``.

        Implemented with Dijkstra's algorithm using a binary heap. Overall time
        complexity is `O(n log n)`, where `n` is the number of pixels (i.e.
        height x width) of the image. However, its average time complexity is
        `Θ(d^2 log d)`, where ``d`` is the distance between ``orig`` and
        ``dest``.
        """
        self.canceled = False

        print(f"Searcher: starting search with origin at {orig} and "
              f"destination at {dest}...")

        # Convert to grayscale if the image is in color
        if len(data.shape) == 3: data = np.mean(data, axis=2)

        height, width = data.shape
        steps = [Point(1, 0), Point(0, 1), Point(-1, 0), Point(0, -1)]

        # init
        visited = np.full((height, width), False)
        distances = np.full((height, width), float('inf'))
        distances[*orig.t] = 0
        predecessors = np.full((height, width, 2), -1, dtype=int)
        pq = [(0, orig)]  # binary heap: (dist, node)

        while pq:
            if self.canceled:
                print("Searcher: canceled")
                return None

            curr_dist, curr = heapq.heappop(pq)
            if visited[*curr.t]: continue
            visited[*curr.t] = True
            if curr == dest: break

            for step in steps:
                neighbor = curr + step
                if neighbor.out_of_bounds(Point(width, height)): continue

                # use inverse brightness as weight
                new_weight = curr_dist + self._calc_weight(float(
                    data[*neighbor.t]))

                if distances[*neighbor.t] > new_weight:
                    distances[*neighbor.t] = new_weight
                    predecessors[*neighbor.t] = curr.x, curr.y
                    heapq.heappush(pq, (new_weight, neighbor))

        # reconstruct path
        path = []
        curr = dest
        while curr != orig:
            path.append(curr)
            curr = Point(*predecessors[*curr.t])
            if curr == Point(-1, -1):
                print("Searcher: Path broken, no predecessor found")
                return None
        if not path: return None

        print("Searcher: path found!")
        return path

    @staticmethod
    def _calc_weight(x: float) -> int | float:
        """
        Calculates the edge weight based on pixel intensity.

        Modifying this formula changes how much a pixel's intensity affects the
        relative cost of traversal.
        """
        # I propose an exponential decay function with:
        n0 = 2 ** 16
        t_half = 16
        # https://www.desmos.com/calculator/8zad7rj8md
        return n0 * 2 ** (-x / t_half)
