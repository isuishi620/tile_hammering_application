from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple

import numpy as np


class RubPhase(Enum):
    PRETRAIN = auto()
    TRAIN = auto()


@dataclass
class RubSession:
    """単一の擦りトレーニングセッションを管理する状態コンテナー。"""

    train_time: float
    data: List[np.ndarray] = field(default_factory=list)
    counting_time: float = 0.0
    collecting: bool = False
    start_ts: Optional[float] = None
    end_ts: Optional[float] = None
    phase: Optional[RubPhase] = None

    def start(self, now: float, phase: RubPhase) -> None:
        """指定フェーズの擦りフレーム収集を開始する。"""
        self.data.clear()
        self.counting_time = 0.0
        self.collecting = True
        self.start_ts = now
        self.end_ts = now + float(self.train_time)
        self.phase = phase

    def stop(self) -> None:
        """フレーム収集を停止する。"""
        self.collecting = False
        self.start_ts = None
        self.end_ts = None

    def append_frame(self, frame: np.ndarray, frames: int, sample_rate: int) -> float:
        """マイクから取得したフレームを保存する。"""
        self.data.append(frame.copy())
        self.counting_time += frames / float(sample_rate)
        return self.counting_time

    def is_active(self) -> bool:
        return self.collecting

    def elapsed(self, now: float) -> float:
        if self.start_ts is None:
            return 0.0
        return max(0.0, now - self.start_ts)

    def completed(self, now: float) -> bool:
        return self.end_ts is not None and now >= self.end_ts

    @property
    def buffer(self) -> np.ndarray:
        if not self.data:
            return np.empty(0, dtype=np.float32)
        return np.concatenate(tuple(self.data))

    @property
    def frames(self) -> Tuple[np.ndarray, ...]:
        return tuple(self.data)
