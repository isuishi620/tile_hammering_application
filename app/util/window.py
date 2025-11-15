from enum import Enum, auto


class Window(Enum):
    """スタックウィジェットのルーターで扱う論理的な画面列挙。"""

    MENU = auto()
    TRAIN = auto()
    TEST = auto()

    @property
    def index(self) -> int:
        return self.value - 1
