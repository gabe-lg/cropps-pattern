import numpy as np
from abc import ABC, abstractmethod
from lib.point import Point
from queue import Queue
from typing import List


class LineTracer(ABC):
    @abstractmethod
    def trace(self, *args) -> List[Point]: pass


class NotALineTracer(LineTracer):
    def trace(self, *args): raise NotImplementedError()


class StraightLineTracer(LineTracer):
    def trace(self, orig, dest, *args):
        """
        Implemented with Bresenham's line algorithm.
        """
        dx, dy = abs(dest - orig)
        sx = 1 if orig.x < dest.x else -1
        sy = 1 if orig.y < dest.y else -1
        err = dx - dy

        points = [orig]
        while orig != dest:
            e2 = 2 * err
            if e2 >= -dy:
                err -= dy
                orig += Point(sx, 0)
            if e2 <= dx:
                err += dx
                orig += Point(0, sy)
            points.append(orig)
        return points[::-1]


class FreehandLineTracer(LineTracer):
    def trace(self, _, __, ___, mouse_coor, *args):
        assert isinstance(mouse_coor, Queue)

        points = []
        while not mouse_coor.empty():
            mouse_pos = mouse_coor.get()
            if mouse_pos != Point(np.inf, np.inf):
                points.append(mouse_pos)
            if mouse_pos == Point(np.inf, np.inf) and points: break
        return points
