from collections import deque
from typing import Optional, TypeVar

T = TypeVar('T')


class Stack(deque[T]):
    """
    A stack is a `deque
    <https://docs.python.org/3.13/library/collections.html#collections.deque>`_.
    """

    def __init__(self): super().__init__(); self.push = self.append

    def peek(self) -> Optional[T]: return self[-1]
