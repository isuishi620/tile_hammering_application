from __future__ import annotations

from typing import Optional

import sounddevice as sd
from PyQt5.QtCore import QObject


class Read(QObject):
    """入力音声ストリームを管理し、取得サンプルをモデルへ渡す。"""

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.stream: Optional[sd.InputStream] = None
        self.time = 0.0
        self.model.audio_is_stream = False
        self.model.camera_is_stream = False
        self._configure_defaults()

    def _configure_defaults(self) -> None:
        """sounddeviceをリセットして基本的な設定を行う。"""
        self.reset()
        sd.default.samplerate = self.model.sample_rate
        sd.default.dtype = self.model.dtype
        sd.default.blocksize = self.model.block_size

    def start(self) -> None:
        if self.model.audio_is_stream:
            return
        self.stream = sd.InputStream(
            samplerate=self.model.sample_rate,
            blocksize=self.model.block_size,
            dtype=self.model.dtype,
            channels=self.model.input,
            callback=self.callback,
        )
        self.stream.start()
        self.model.audio_is_stream = True

    def stop(self) -> None:
        if not self.model.audio_is_stream or self.stream is None:
            return
        self.stream.close()
        self.stream = None
        self.model.audio_is_stream = False

    def callback(self, indata, frames, _time, _status) -> None:
        data = indata[:, self.model.ch] * self.model.eu
        self.time += frames / self.model.sample_rate
        self.model.read_time = self.time
        self.model.block_data = data.copy()

    def reset(self) -> None:
        sd._terminate()
        sd._initialize()

    def time_reset(self) -> None:
        self.time = 0.0
        self.model.read_time = 0.0
