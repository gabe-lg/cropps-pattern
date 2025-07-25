from lib.doubly_linked_list import DoublyLinkedNode
from typing import List


class Point(tuple):
    """
    Examples::

      >>> p = Point(1, 2)
      Point(1, 2)

      >>> p + Point(3, 4)
      Point(4, 6)

      >>> p.t
      tuple(2, 1)
    """

    def __new__(cls, x, y): return super().__new__(cls, (x, y))

    @property
    def x(self) -> int: return self[0]

    @property
    def y(self) -> int: return self[1]

    @property
    def t(self) -> "Point": return Point(self.y, self.x)

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point") -> "Point":
        return Point(self.x - other.x, self.y - other.y)

    def __abs__(self) -> "Point": return Point(abs(self.x), abs(self.y))

    def out_of_bounds(self, corner: "Point") -> bool:
        """
        :param corner: the point with the largest ``x`` and ``y`` coordinates
         while being in bounds.
        :return: ``True`` iff point is out of bounds.
        """
        return not (0 <= self.y < corner.y and 0 <= self.x < corner.x)


class PointNode(DoublyLinkedNode[Point]): pass


class LineNode(DoublyLinkedNode[List[Point]]): pass
