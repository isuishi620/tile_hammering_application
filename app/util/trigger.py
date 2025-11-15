from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
from PyQt5.QtCore import QObject


class Trigger(QObject):
    """設定した閾値を超えたときの音声フレームを切り出すユーティリティ。"""

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.buffer_index: int = -5
        self.hold: float = 0.05
        self.offset: int = -1024
        self.length: int = 4096

    def trigger(self) -> None:
        if not self._should_trigger():
            return

        self.model.time_reset()
        buffer_segments = self._buffer_segments()
        if not buffer_segments:
            return

        trigger_data = self._extract_trigger_data(np.concatenate(buffer_segments))
        self.model.trigger_data = trigger_data

    def start(self) -> None:
        self.model.trigger_is_active = True

    def stop(self) -> None:
        self.model.trigger_is_active = False

    # ------------------------------------------------------------------ #
    # 内部処理
    # ------------------------------------------------------------------ #
    def _buffer_segments(self) -> Sequence[np.ndarray]:
        buffer_data = getattr(self.model, "_buffer_data", None)
        if buffer_data is None:
            return []
        segments = list(buffer_data)
        if not segments:
            return []
        start = max(0, len(segments) + self.buffer_index - 1)
        return segments[start:]

    def _should_trigger(self) -> bool:
        return (
            self.is_active
            and self.height is not None
            and self._is_threshold_exceeded()
            and self.model.read_time >= self.hold
        )

    def _is_threshold_exceeded(self) -> bool:
        buffer_data = getattr(self.model, "_buffer_data", None)
        if buffer_data is None:
            return False
        segments = list(buffer_data)
        if not segments:
            return False
        index = self.buffer_index
        try:
            return np.any(segments[index] >= self.height)
        except IndexError:
            return False

    def _extract_trigger_data(self, data: np.ndarray) -> np.ndarray:
        threshold_indices = np.where(data >= self.height)[0]
        if threshold_indices.size == 0:
            return np.empty(0, dtype=data.dtype)
        index = int(threshold_indices[0])
        start = max(0, index + self.offset)
        end = start + self.length
        return data[start:end]

    # ------------------------------------------------------------------ #
    # 便利プロパティ
    # ------------------------------------------------------------------ #
    @property
    def is_active(self) -> bool:
        return getattr(self.model, "trigger_is_active", False)

    @property
    def height(self) -> float | None:
        return getattr(self.model, "trigger_threshold", None)
