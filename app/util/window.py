from enum import Enum, auto


class Window(Enum):
    """Logical windows managed by the stacked widget router."""

    MENU = auto()
    TRAIN = auto()
    TEST = auto()

    @property
    def index(self) -> int:
        return self.value - 1
