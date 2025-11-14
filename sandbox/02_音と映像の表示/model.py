# model.py
from PyQt5.QtCore import QObject
import numpy as np

class Model(QObject):
    """モデルクラス"""

    def __init__(self) -> None:
        super().__init__()

        self.fps: int = 30
        
        self.audio: np.adarray = None
        self.audio_is_stream: bool = False

        self.camera: any = None
        self.camera_is_stream: bool = False

        