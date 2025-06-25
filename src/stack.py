from dataclasses import dataclass
from typing import Deque, List, Optional, Tuple, TypeVar
import numpy as np

T = TypeVar('T')


class Stack(Deque[T]):
    """https://docs.python.org/3.13/library/collections.html#collections.deque"""

    def __init__(self):
        super().__init__()
        self.push = self.append

    def peek(self) -> Optional[T]: return self[-1] if self else None

    @property
    def size(self) -> int: return len(self)


@dataclass
class SearchResult:
    points: List[Tuple[int, int]]
    is_line: bool
    data: np.ndarray


class SearchStack(Stack[SearchResult]): pass
