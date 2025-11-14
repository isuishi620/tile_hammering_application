# random_block_timer.py
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
import numpy as np

class RandomGenerator(QObject):
    signal = pyqtSignal(object)  # ndarray をそのまま流すので object でOK

    def __init__(self, fps: float, block_size: int, parent=None):
        super().__init__(parent)
        self.block_size = int(block_size)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._timeout)
        self.timer.start(int(round(1000 / float(fps))))

    def _timeout(self):
        block = np.random.randn(self.block_size)*0.1
        self.signal.emit(block)
