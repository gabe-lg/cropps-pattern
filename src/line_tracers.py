from enum import auto, Enum
from src.line_tracer import *
from src.searcher import Searcher


class LineTracerTypes(Enum):
    NONE = auto()
    LINE = auto()
    FREE = auto()
    BRIGHTEST = auto()


ltt = LineTracerTypes


class LineTracers:
    def __init__(self, initial: ltt = ltt.BRIGHTEST):
        self._curr_type = initial
        self._types = {
            ltt.NONE: NotALineTracer(),
            ltt.LINE: StraightLineTracer(),
            ltt.FREE: FreehandLineTracer(),
            ltt.BRIGHTEST: Searcher(),
        }

    @property
    def curr_type(self): return self._curr_type

    @property
    def get_line_tracer(self) -> LineTracer:
        return self._types.get(self._curr_type)

    def set_curr_type(self, value: LineTracerTypes):
        if not isinstance(value, LineTracerTypes): raise ValueError()
        print(f"Switching from {self._curr_type.name} to {value.name}")
        self._curr_type = value
