from enum import Enum, auto

class Window(Enum):
    # ===[ 順番でwindow指定 ]===
    MENU = auto()
    TRAIN = auto()
    TEST = auto()

    @property
    def index(self):
        return self.value-1
