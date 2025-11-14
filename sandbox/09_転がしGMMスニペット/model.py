# model.py
import cv2
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
from collections import deque
from typing import Optional, List, Sequence, Tuple
from timer import Timer
import sounddevice as sd
from pipeline.pipeline import gmm
from rub import RubSession, RubPhase

class Model(QObject):
    """Core state container for microphone, camera, and GMM inference."""
    rub_progress = pyqtSignal(float)
    
    def __init__(self) -> None:
        super().__init__()
        self.fps: int = 30
        self.timer = Timer(self.fps)

        self.sample_rate = 48000
        self.num_channels = 1
        self.dtype = 'float32'
        self.block_size = 2048
        self.buffer_time = 1
        self.eu = 0.003059004
        
        self.mic_data = None
        self.buffer_blocks = self._make_buffer(time=self.buffer_time,
                                                block_size=self.block_size,
                                                fs=self.sample_rate
                                                )     
        
        self.mic = self._init_microphone()
        self.camera = self._init_camera()

        self.mic_is_stream = False
        self.camera_is_stream = False

        #========== 転がしのパラメータ ===========
        self.rub_duration = 10
        self.rub_session = RubSession(train_time=self.rub_duration)

        self.f_min: int = 1000
        self.f_max: int = 16000
        self.g_pass: int = 3
        self.g_stop: int = 40
        self.n_fft: int = 4096
        self.power: int = 2
        self.n_mels: int = 40
        self.window: str = 'hann'
        self.noverlap: int = int(self.n_fft*0.75)

        self.n_components = 1
        self.covariance_type = 'full'
        self.random_state = 42
        
        self.gmm_pipeline = gmm(self)
        self.gmm_is_infering = False
        self.anomaly_scores: List[float] = []
        self.anomaly_history_size: int = 50

        self.gmm_pretrained: bool = False
        self.gmm_calibrated: bool = False

        # statistic placeholders for multi-phase normalization
        self.pretrain_score_mean: float = 0.0
        self.pretrain_score_std: float = 1.0
        self.train_score_mean: float = 0.0
        self.train_score_std: float = 1.0
        self.anomaly_threshold: float = 3.0

    def _init_camera(self):
        return cv2.VideoCapture(0,cv2.CAP_DSHOW)

    def _init_microphone(self):
        return sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.num_channels,
            dtype=self.dtype,
            blocksize=self.block_size,
            callback=self._audio_callback,
        )
    
    def _audio_callback(self, indata, frames, time, status):
        x = indata[:, 0].copy() * self.eu
        self.mic_data = x            
        self.buffer_blocks.append(x)

        if self.rub_session.is_active():
            progress = self.rub_session.append_frame(x, frames, self.sample_rate)
            self.rub_progress.emit(progress)

    @property
    def buffer(self) -> np.ndarray:
        if not self.buffer_blocks:
            return np.empty(0, dtype=np.float32)
        return np.concatenate(tuple(self.buffer_blocks))

    @property
    def rub_buffer(self) -> np.ndarray:
        return self.rub_session.buffer
    
    @property
    def camera_data(self):
        _, frame = self.camera.read()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame_rgb

    def _make_buffer(self, time: float, block_size: int, fs: int) -> deque:
        n = max(1, int(np.ceil(time * (fs / block_size))))
        return deque(
            (np.zeros(block_size, dtype=np.float32) for _ in range(n)),
            maxlen=n,
        )

    # ====== Rub training helpers ==================================================
    def start_rub_collection(self, now: float, phase: RubPhase) -> None:
        self.rub_session.start(now, phase)

    def stop_rub_collection(self) -> None:
        self.rub_session.stop()

    def rub_elapsed(self, now: float) -> float:
        return self.rub_session.elapsed(now)

    def rub_collection_completed(self, now: float) -> bool:
        return self.rub_session.completed(now)

    def rub_phase(self) -> Optional[RubPhase]:
        return self.rub_session.phase

    def rub_frames(self):
        return self.rub_session.frames

    def update_rub_duration(self, seconds: float) -> None:
        """Change the amount of audio (seconds) captured for each rub session."""
        if seconds <= 0:
            raise ValueError("Rub duration must be a positive value.")
        if self.rub_session.is_active():
            raise RuntimeError("Cannot change rub duration while capture is running.")
        self.rub_duration = float(seconds)
        self.rub_session.train_time = self.rub_duration

    def compute_anomaly(self, signal: np.ndarray) -> float:
        if self.gmm_pipeline is None:
            raise RuntimeError("GMM pipeline is not initialized.")
        scores = self.gmm_pipeline.transform(signal)
        return float(np.mean(scores))

    def record_anomaly_score(self, score: float) -> None:
        """Keep every anomaly score so that recent history can be visualized."""
        self.anomaly_scores.append(score)

    def latest_anomaly_scores(self, count: Optional[int] = None) -> List[float]:
        if count is None:
            count = self.anomaly_history_size
        if count <= 0 or not self.anomaly_scores:
            return []
        return list(self.anomaly_scores[-count:])

    def latest_anomaly_series(self, count: Optional[int] = None) -> Tuple[List[int], List[float], List[str]]:
        scores = self.latest_anomaly_scores(count)
        total = len(self.anomaly_scores)
        start = max(0, total - len(scores))
        indices = list(range(start, start + len(scores)))
        colors = self._colorize_scores(scores)
        return indices, scores, colors

    def _colorize_scores(self, scores: Sequence[float]) -> List[str]:
        if not scores:
            return []
        if not self.gmm_calibrated:
            return ['#2196F3'] * len(scores)
        mu = self.train_score_mean
        sigma = self._safe_std(self.train_score_std)
        first = mu + sigma
        second = mu + 2 * sigma
        third = mu + 3 * sigma
        colors: List[str] = []
        for score in scores:
            absolute = (score * sigma) + mu
            if absolute < first:
                colors.append('#2196F3')  # blue
            elif absolute < second:
                colors.append('#FFEB3B')  # yellow
            elif absolute >= third:
                colors.append('#F44336')  # red
            else:
                colors.append('#FF9800')  # between 2sigma and 3sigma
        return colors

    def standardize_pretrain(self, score: float) -> float:
        if not self.gmm_pretrained:
            return score
        return (score - self.pretrain_score_mean) / self._safe_std(self.pretrain_score_std)

    def standardize_training(self, score: float) -> float:
        if not self.gmm_calibrated:
            return score
        return (score - self.train_score_mean) / self._safe_std(self.train_score_std)

    @staticmethod
    def _safe_std(std: float) -> float:
        return std if abs(std) > 1e-8 else 1e-8

