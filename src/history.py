import numpy as np
from dataclasses import dataclass
from lib.doubly_linked_list import DoublyLinkedList, DoublyLinkedNode
from typing import List, Tuple


@dataclass
class Action:
    """
    :ivar points: a list of ``Points`` representing a line.
    :ivar data: a NumPy array representing an image.
    """
    points: List[Tuple[int, int]]
    data: np.ndarray

    __str__ = lambda self: f"Action:{self.points}\n"


class ActionNode(DoublyLinkedNode[Action]): pass


class PointsList(DoublyLinkedList[ActionNode]): pass


class History:
    """
    A tree of ``ActionNode`` objects with a cursor for tree traversal.
    """

    def __init__(self):
        # Structure:
        # `[_init] -> [_root] -> [_list]`
        #
        # Notes:
        # `curr` initially points to `_init`. When first action is pushed,
        # it points to `_root`. Then it points to the same object as
        # `_list.curr`.

        self._list: PointsList = PointsList()
        self._init: ActionNode = ActionNode()
        self._root: ActionNode = ActionNode(prev=self._init)
        self._curr: ActionNode = self._init

        # points to `_init` except immediately after `clear` is called,
        # in which case it points to the node that `curr` pointed to
        # immediately before `clear` was called.
        self._last_curr: ActionNode = self._init

    def init(self, data: np.ndarray):
        """
        Called after initialization to save a copy of `data` before it is
        manipulated, then calls ``clear``.

        :param data: A NumPy array representing an image.
        """
        self._init.value = Action([], data.copy())
        self.clear()

    def is_init_state(self) -> bool:
        """
        :return: ``True`` iff the cursor is at the start of the tree (
         before the first node).
        """
        return self._curr == self._init

    def clear(self):
        self._list.clear()
        self._root.value = None
        self._init.next = None
        self._root.next = None
        self._curr = self._init

    def peek(self) -> ActionNode:
        return self._curr.child if self.curr_has_child() else self._curr

    def push(self, value: Action) -> ActionNode:
        if self._curr == self._init:
            self._root.value = value
            self._root.next = None
            self._list.clear()
            self._curr = self._init.next = self._root
        else:
            self._root.next = self._list.head
            self._list.push(ActionNode(value))
            self._curr = self._list.peek()
        self._last_curr = self._init
        return self._curr

    def undo(self) -> ActionNode:
        """
        Moves cursor to the previous node, and returns it.

        If ``undo_all`` was called immediately before this function is called,
        cursor is moved to the node immediately before ``undo_all`` was called
        instead.

        :raises IndexError: iff cursor is at the start of the tree (before the
         first node), and ``undo_all`` was not called immediately before this
         function is called.
        """
        if self._last_curr != self._init:
            self._curr = self._last_curr
            self._last_curr = self._init
        elif self._curr == self._init:
            raise IndexError()
        else:
            if self._curr == self._root or self._curr == self._root.next.next:
                self._curr = self._init
            else:
                self._curr = self._list.prev()
        return self._curr.child if self.curr_has_child() else self._curr

    def undo_all(self, is_button=False) -> ActionNode:
        """
        Moves the cursor to the start of the tree, and returns it.

        Keeps track of the cursor's position immediately before this function
        was called.
        """
        if is_button: self._last_curr = self._curr
        self._curr = self._init
        return self._curr

    def redo(self) -> ActionNode:
        """
        Moves the cursor to the next node, and returns it.

        :raises IndexError: iff the current node has no next node.
        """
        if not self.curr_has_next(): raise IndexError()
        try:
            self._curr = self._list.next()
        except IndexError:
            self._curr = self._root
        return self._curr.child if self.curr_has_child() else self._curr

    def redo_all(self) -> ActionNode:
        """
        Moves the cursor to the last node, and returns it.

        :raises IndexError: iff the current node has no next node.
        """
        if not self.curr_has_next(): raise IndexError()
        if self._list.is_empty():
            self._curr = self._root
        else:
            self._curr = self._list.last()
        return self._curr.child if self.curr_has_child() else self._curr

    def curr_has_prev(self) -> bool:
        return self._curr.prev is not None

    def curr_has_next(self) -> bool:
        return self._curr.next is not None

    def curr_has_child(self) -> bool:
        return self._curr.child is not None
