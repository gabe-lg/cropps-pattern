import numpy as np
from dataclasses import dataclass, field
from lib.doubly_linked_list import DoublyLinkedList, DoublyLinkedNode
from lib.point import Point
from typing import Any, List, Tuple


@dataclass
class Action:
    """
    :ivar points: a list of ``Points`` representing a line.
    :ivar data: a NumPy array representing an image.
    """
    point: Point
    line: List[Point] = field(default_factory=list)
    area: List[Point] = field(default_factory=list)

    __str__ = lambda self: f"Action: {self.points}\n"


class ActionNode(DoublyLinkedNode[Action]): pass


class PointsList(DoublyLinkedList[ActionNode]):
    def __init__(self):
        super().__init__()
        self._clear = ActionNode()

    @property
    def cleared(self):
        """
        :return: ``True`` iff the last action was "Clear".
        """
        return self._curr == self._clear

    def get_circles(self) -> List[Point]:
        """
        :return: a list of circles from the current frame up to the first one.
        """
        if not self._curr.value: return []
        return [node.value.point for node in self.iter_prev()]

    def get_lines(self) -> List[np.ndarray[Tuple[int, ...], Any]]:
        """
        :return: a list of lines from the current frame up to the first one.
         Lines are converted to NumPy arrays for use in ``cv2.polylines``.
        """
        if not self._curr.value: return []
        return [np.array(node.value.line) for node in self.iter_prev()]

    def push(self, value: ActionNode):
        if self.cleared: self.first()
        super().push(value)

    def undo_all(self):
        """ Clears frame while preserving history. """
        self._clear.prev = self._curr
        self._curr = self._clear
