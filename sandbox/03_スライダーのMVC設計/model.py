# model.py
from PyQt5.QtCore import QObject
import numpy as np

class Model(QObject):
    """モデルクラス"""

    def __init__(self) -> None:
        super().__init__()
        self.threshold_min: float = 0
        self.threshold_max: float = 20
        self.slider_value: int = 0
        
    @property
    def threshold(self) -> str:
        percent = self.slider_value/100
        return self.threshold_max*percent