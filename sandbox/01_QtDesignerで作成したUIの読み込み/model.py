from datetime import datetime
from PyQt5.QtCore import QObject
import numpy as np


class Model(QObject):
    """モデルクラス"""

    def __init__(self) -> None:
        super().__init__()

    @property
    def time(self) -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @property
    def data(self) -> np.ndarray:
        return np.random.rand(100)