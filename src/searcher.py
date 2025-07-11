import cv2
import heapq
import numpy as np
from lib.doubly_linked_list import DoublyLinkedList, T
from lib.point import LineNode, Point, PointNode
from typing import List, Optional, Tuple


class PointList(DoublyLinkedList[PointNode]): pass


class LineList(DoublyLinkedList[LineNode]): pass


class Searcher:
    """
    Stores points using a stack, then searches for the brightest and shortest
    path between the last two points.

    :ivar canceled: ``True`` iff user terminates search
    :ivar clicks: A ``DoublyLinkedList`` of points representing the position
     clicked by user
    :ivar all_lines: A ``DoublyLinkedList`` of lines returned by searcher
    """

    def __init__(self, lock):
        self.canceled = False
        self.clicks = PointList()
        self.all_lines = LineList()
        self._lock = lock
        self._cleared_count = 0

    def push(self, l: DoublyLinkedList[T], elem: T):
        """
        Pushes ``elem`` into ``l``.
        :param l: A ``DoublyLinkedList``
        :param elem: The element to be pushed
        """
        l.push(elem)
        self._cleared_count = 0

    def clear(self, is_button=False):
        cleared_count = 0
        while not self.clicks.curr_at_init():
            if is_button: cleared_count += 1
            if self.clicks.peek().prev: self.undo()
        self._cleared_count = cleared_count

    def undo(self):
        if self._cleared_count:
            for _ in range(self._cleared_count): self.redo()
            self._cleared_count = 0
        else:
            if not self.all_lines.is_empty(): self.all_lines.prev()
            self.clicks.prev()
        return self.clicks.peek()

    def redo(self):
        if self.clicks.peek().prev: self.all_lines.next()
        self.clicks.next()

    def search(self, visited: np.ndarray, data: np.ndarray) \
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
        if not self.clicks: return None

        with self._lock:
            dest = self.clicks.peek().value
            orig = self.clicks.peek().prev.value
        print(f"Searcher: starting search with origin at {orig} and "
              f"destination at {dest}...")

        # Get rid of nonsensical values then normalize
        cv2.normalize(np.clip(data, 0, 255), data, 0., 255., cv2.NORM_MINMAX)
        # Convert to grayscale if the image is in color
        if len(data.shape) == 3: data = np.mean(data, axis=2)

        height, width = data.shape
        steps = [Point(1, 0), Point(0, 1), Point(-1, 0), Point(0, -1)]

        # init
        assert not visited.any()
        distances = np.full((height, width), float('inf'))
        distances[*orig._] = 0
        predecessors = np.full((height, width, 2), -1, dtype=int)
        pq = [(0, orig)]  # binary heap: (dist, node)

        while pq:
            if self.canceled:
                print("Searcher: canceled")
                return None

            curr_dist, curr = heapq.heappop(pq)
            if visited[*curr._]: continue
            visited[*curr._] = True
            if curr == dest: break

            for step in steps:
                neighbor = curr + step
                if neighbor.out_of_bounds(Point(width, height)): continue

                # use inverse brightness as weight
                new_weight = curr_dist + self._calc_weight(float(
                    data[*neighbor._]))

                if distances[*neighbor._] > new_weight:
                    distances[*neighbor._] = new_weight
                    predecessors[*neighbor._] = curr.x, curr.y
                    heapq.heappush(pq, (new_weight, neighbor))

        # reconstruct path
        path = []
        curr = dest
        while curr != orig:
            path.append(curr)
            curr = Point(*predecessors[*curr._])
            if curr == Point(-1, -1):
                print("Searcher: Path broken, no predecessor found")
                return None
        if not path: return None

        print("Searcher: path found!")
        self.all_lines.push(LineNode(path))
        visited.fill(False)
        return path

    def reconstruct_line(self):
        return [p for l in self.all_lines for p in l.value][::-1]

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
