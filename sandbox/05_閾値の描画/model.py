# model.py
from PyQt5.QtCore import QObject
import numpy as np
from collections import deque

from timer import Timer
from random_generator import RandomGenerator


class Model(QObject):
    """モデルクラス"""

    def __init__(self) -> None:
        super().__init__()
        self.fps: int = 30
        self.timer = Timer(self.fps)

        self.threshold_min: float = 0.0
        self.threshold_max: float = 1.0
        self.slider_value: int = 0

        self._data: np.ndarray | None = None
        self.sample_rate = 48000
        self.buffer_time = 3.0
        self.block_size = 2048

        self._buffer_blocks = self._make_buffer(time=self.buffer_time,
                                                block_size=self.block_size,
                                                fs=self.sample_rate
                                                )

        self.generator = RandomGenerator(fps=60, block_size=self.block_size)
        self.generator.signal.connect(self._handle_generator)

    @property
    def threshold(self) -> float:
        percent = self.slider_value / 100.0
        return self.threshold_min + (self.threshold_max - self.threshold_min) * percent

    @property
    def data(self) -> np.ndarray | None:
        return self._data

    @data.setter
    def data(self, value) -> None:
        arr = np.asarray(value, dtype=np.float32)
        self._data = arr
        self._buffer_blocks.append(arr.copy())

    @property
    def buffer_blocks(self) -> deque:
        return self._buffer_blocks

    @property
    def buffer(self) -> np.ndarray:
        if not self._buffer_blocks:
            return np.empty(0, dtype=np.float32)
        return np.concatenate(tuple(self._buffer_blocks))

    def _make_buffer(self, time: float, block_size: int, fs: int) -> deque:
        buffer_length = max(1, int(np.ceil(time * (fs / block_size))))
        return deque(
            (np.zeros(block_size, dtype=np.float32) for _ in range(buffer_length)),
            maxlen=buffer_length,
        )

    def _handle_generator(self, value):
        self.data = value
