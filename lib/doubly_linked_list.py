from dataclasses import dataclass
from typing import Generic, Iterable, Optional, TypeVar, List, Generator

T = TypeVar('T')


@dataclass
class DoublyLinkedNode(Generic[T]):
    """
    Graph::

        prev ↔ self ↔ next
                ↓
              child

    :ivar value:
    :ivar prev:
    :ivar next:
    :ivar child:
    """
    value: Optional[T] = None
    prev: Optional["DoublyLinkedNode[T]"] = None
    next: Optional["DoublyLinkedNode[T]"] = None
    child: Optional["DoublyLinkedNode[T]"] = None

    def __str__(self):
        return (f"{type(self)}:\n-----\n"
                f"Value:{self.value}\n"
                f"Prev is {'not ' if self.prev else ''}None\n"
                f"Next is {'not ' if self.next else ''}None\n"
                f"Child:{self.child}\n\n")


DoublyLinkedNode_T = TypeVar('DoublyLinkedNode_T', bound=DoublyLinkedNode)


class DoublyLinkedList(Iterable[DoublyLinkedNode_T]):
    """
    A list of ``DoublyLinkedNode`` objects with a cursor for list traversal.
    """

    def __init__(self):
        # When freshly initialized, the cursor points to `_init`.

        # Must always be the first node of the list. It can never have
        # a value, a previous node, or a child node
        self._init: DoublyLinkedNode_T = DoublyLinkedNode()

        # The cursor. Can point to any node, including `_init`.
        self._curr: DoublyLinkedNode_T = self._init

        self._tail: DoublyLinkedNode_T = self._init

    def __str__(self):
        res = ""
        for elem in self:
            res += str(elem)
        return f"{type(self)}:\n" + res

    def __iter__(self):
        curr = self._init.next
        while curr:
            yield curr
            curr = curr.next

    def iter_prev(self):
        curr = self._curr
        while curr != self._init:
            yield curr
            curr = curr.prev

    def iter_list(self, indices: List[int]) -> Generator[DoublyLinkedNode_T, None, None]:
        """
        A generator yielding nodes corresponding to the specified indices
        in the linked list.

        :param indices: The indices of nodes to be returned.
        """
        curr = self._init
        curr_id = -1
        indices.sort()
        for index in indices:
            for i in range(index - curr_id):
                curr = curr.next
            curr_id += index
            yield curr

    def is_empty(self) -> bool:
        return not self._init.next

    def push(self, value: DoublyLinkedNode_T):
        self._curr.next = value
        value.prev = self._curr
        self._tail = self._curr = value

    def push_all(self, values: Iterable[T]) -> int:
        """
        Push all elements from ``values`` into the list. Preserves the order of
        elements in ``values``.

        :param values: An iterable of elements to be pushed.
        :return: The number of elements pushed.
        """
        count = 0
        for value in values:
            self.push(value)
            count += 1
        return count

    def clear(self):
        self._tail = self._curr = self._init
        self._init.next = None

    def peek(self) -> DoublyLinkedNode_T:
        self._check_empty()
        return self._curr

    def init(self):
        """
        Moves cursor to the start of the list, such that it will point to the
        first node next time ``next`` is called.
        """
        self._curr = self._init

    def curr_at_init(self) -> bool:
        """
        :return: ``True`` iff the cursor before the first element.
        """
        return self._curr == self._init

    def curr_at_first(self) -> bool:
        """
        :return: ``True`` iff the cursor is pointing at the first element.
        """
        return self._curr.prev == self._init

    def curr_at_tail(self) -> bool:
        """
        :return: ``True`` iff the cursor is pointing at the last element.
        """
        return self._curr == self._tail

    def first(self):
        """
        Moves cursor before the first node.

        :raises IndexError: iff list is empty
        """
        self._check_empty()
        self._curr = self._init

    def prev(self) -> DoublyLinkedNode_T:
        """
        Moves cursor to the previous node, and returns it. Does nothing if
        the node is already before the first node.

        :raises IndexError: iff list is empty
        """
        self._check_empty()
        if self._curr != self._init: self._curr = self._curr.prev
        return self._curr

    def next(self) -> DoublyLinkedNode_T:
        """
        Moves cursor to the next node, and returns it. Does nothing if the
        node is already the last.

        :raises IndexError: iff list is empty
        """
        self._check_empty()
        if self._curr != self._tail: self._curr = self._curr.next
        return self._curr

    def has_next(self) -> bool:
        """
        :return: ``True`` iff the current node has a next node.
        """
        return self._curr.next is not None

    def last(self) -> DoublyLinkedNode_T:
        """
        Moves cursor to the last node, and returns it.

        :raises IndexError: iff list is empty
        """
        self._check_empty()
        self._curr = self._tail
        return self._curr

    def goto(self, index: int):
        """
        Moves cursor to the node at index ``index``.
        :param index: The index of the node to move to.
         Must be non-negative and less than the length of the list.
        :raises IndexError: iff list is empty or index out of bounds.
        :raises ValueError: iff index is negative.
        """
        self._check_empty()
        curr = self._init.next
        for _ in range(index):
            if curr == self._tail: raise IndexError()
            curr = curr.next
        self._curr = curr
        return self._curr

    def _check_empty(self):
        if self.is_empty(): raise IndexError()
