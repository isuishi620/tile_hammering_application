from __future__ import annotations

from collections import deque

import cv2
import numpy as np
from PyQt5.QtCore import pyqtSignal

from app.base.model import ModelBase
from app.model.read import Read
from app.model.rub import RubPhase, RubSession
from app.model.timer import Timer
from app.model.trigger import Trigger
from app.pipeline.pipeline import gmm, melspec_zscore
from app.util.window import Window


class Model(ModelBase):
    """全コントローラーで共有するアプリケーション状態。"""

    trigger_signal = pyqtSignal()
    rub_progress = pyqtSignal(float)

    def __init__(self):
        super().__init__()

        # トリガースライダー（パーセンテージ基準）
        self.trig_level_min: int = 0
        self.trig_level_max: int = 100
        self.trig_level_val: int = 50
        self.threshold_min: float = 0.0
        self.threshold_max: float = 20.0
        self._trigger_threshold: float = 0.0

        # データ収集の目標値
        self.tap_train_target_count: int = 30
        self.tap_threshold_target_count: int = 30
        self.rub_train_duration_sec: float = 10
        self.rub_threshold_duration_sec: float = 10
        self.rub_session = RubSession(train_time=float(self.rub_train_duration_sec))
        self._rub_train_elapsed: float = 0.0
        self._rub_th_elapsed: float = 0.0

        # 音声/映像ストリーミングの初期値
        self.fps: int = 30
        self.timer = Timer(self.fps)
        self.audio_is_stream: bool = False
        self.camera_is_stream: bool = False
        self.sample_rate: int = 48000
        self.input: int = 2
        self.dtype: str = "int16"
        self.block_size: int = 2048
        self.ch: int = 0
        self.eu: float = 0.1
        self._block_data = np.array([])
        self.buffer_time: float = 1.0
        self._buffer_data = self._make_buffer()

        self.read_time: float = 0.0
        self.audio = Read(self)
        self.camera = self._init_camera()
        self.beep_duration_sec: float = 0.1
        self.beep_frequency_hz: float = 1200.0
        self.beep_volume: float = 0.2
        self.beep_envelope_ratio: float = 0.2
        self.beep_waveform = self._generate_beep_waveform()

        # パイプライン設定
        self.bandpass_min_hz: int = 300
        self.bandpass_max_hz: int = 16000
        self.bandpass_pass_ripple_db: int = 3
        self.bandpass_stop_ripple_db: int = 40
        self.fft_size: int = 4096
        self.fft_power: int = 2
        self.fft_window: str = "hann"
        self.stft_overlap: int = int(self.fft_size * 0.75)
        self.mel_bins: int = 40
        self.mel_min_hz: int = 1000
        self.mel_max_hz: int = 16000

        # トリガーと推論パイプライン
        self.trigger = Trigger(self)
        self.trigger_is_active: bool = False
        self._trigger_data = np.array([])
        self.pipeline = melspec_zscore(self)
        self.n_components: int = 2
        self.covariance_type: str = "full"
        self.random_state: int = 42
        self.gmm_pipeline = gmm(self)
        self.gmm_is_infering: bool = False
        self.gmm_pretrained: bool = False
        self.gmm_trained: bool = False
        self.pretrain_score_mean: float = 0.0
        self.pretrain_score_std: float = 1.0
        self.train_score_mean: float = 0.0
        self.train_score_std: float = 1.0
        self.rub_anomaly_threshold_sigma: float = 3.0
        self._rub_threshold_bands = (0.0, 0.0, 0.0)
        self.rub_anomaly_scores: list = []
        self.rub_anomaly_history_size: int = 50

        # データバッファ
        self.trained: bool = False
        self._train_data = np.empty((0, 0))
        self._threshold_data = np.empty((0, 0))
        self.thresholded: bool = False
        self._anomaly_threshold = None

        # 擦り専用の状態
        self.rub_pretrained: bool = False
        self.rub_trained: bool = False

        self.current_window: Window = Window.MENU
        self.test_anomalies: list[float] = []
        self.display_count: int = 20

    def record_test_anomaly(self, value: float) -> None:
        self.test_anomalies.append(float(value))

    def reset_test_anomalies(self) -> None:
        self.test_anomalies.clear()

    @property
    def trigger_threshold(self):
        return self._trigger_threshold

    @trigger_threshold.setter
    def trigger_threshold(self, value) -> float:
        self._trigger_threshold = value

    def trig_level2th(self):
        range_trig = self.trig_level_max - self.trig_level_min
        percent = (self.trig_level_val - self.trig_level_min) / range_trig
        range_th = self.threshold_max - self.threshold_min
        value = range_th * percent + self.threshold_min
        return value

    def trig_th2level(self):
        range_trig = self.trig_level_max - self.trig_level_min
        range_th = self.threshold_max - self.threshold_min
        percent = (self.trigger_threshold - self.threshold_min) / range_th
        value = percent * range_trig + self.trig_level_min
        return int(value)

    @property
    def tap_train_sample_number(self) -> int:
        return len(self.train_data)

    @property
    def tap_th_sample_number(self) -> int:
        return len(self.threshold_data)

    @property
    def rub_train_sample_number(self) -> int:
        return int(self._rub_train_elapsed)

    @property
    def rub_th_sample_number(self) -> int:
        return int(self._rub_th_elapsed)

    @property
    def block_data(self) -> np.ndarray:
        return self._block_data

    @block_data.setter
    def block_data(self, value: np.ndarray):
        self._block_data = np.array(value)
        self.buffer_data = self._block_data
        if self.rub_session.is_active():
            progress = self.rub_session.append_frame(
                self._block_data, len(self._block_data), self.sample_rate
            )
            self.rub_progress.emit(progress)

    @property
    def buffer_data(self) -> np.ndarray:
        if len(self._buffer_data) == 0:
            return np.array([])
        return np.concatenate(list(self._buffer_data))

    @buffer_data.setter
    def buffer_data(self, value: np.ndarray):
        self._buffer_data.append(value)

    def set_rub_train_elapsed(self, seconds: float):
        self._rub_train_elapsed = max(0.0, float(seconds))

    def set_rub_threshold_elapsed(self, seconds: float):
        self._rub_th_elapsed = max(0.0, float(seconds))

    def compute_rub_anomaly(self, signal: np.ndarray) -> float:
        if self.gmm_pipeline is None:
            raise RuntimeError("GMM pipeline is not initialized.")
        scores = self.gmm_pipeline.transform(signal)
        return float(np.mean(scores))

    def record_rub_anomaly_score(self, score: float) -> None:
        self.rub_anomaly_scores.append(score)
        if len(self.rub_anomaly_scores) > self.rub_anomaly_history_size:
            self.rub_anomaly_scores = self.rub_anomaly_scores[
                -self.rub_anomaly_history_size :
            ]

    def latest_rub_anomaly_scores(self, count=None):
        if count is None:
            count = self.rub_anomaly_history_size
        if count <= 0 or not self.rub_anomaly_scores:
            return []
        return list(self.rub_anomaly_scores[-count:])

    def latest_rub_anomaly_series(self, count=None):
        scores = self.latest_rub_anomaly_scores(count)
        total = len(self.rub_anomaly_scores)
        start = max(0, total - len(scores))
        indices = list(range(start, start + len(scores)))
        colors = self._colorize_rub_scores(scores)
        return indices, scores, colors

    def _colorize_rub_scores(self, scores):
        if not scores:
            return []
        low, medium, _ = self.rub_threshold_offsets()
        colors = []
        for score in scores:
            if score < low:
                colors.append("#2196F3")
            elif score < medium:
                colors.append("#FFEB3B")
            else:
                colors.append("#F44336")
        return colors

    def standardize_pretrain(self, score: float) -> float:
        return (score - self.pretrain_score_mean) / self._safe_std(
            self.pretrain_score_std
        )

    def standardize_training(self, score: float) -> float:
        return (score - self.train_score_mean) / self._safe_std(self.train_score_std)

    def denormalize_training(self, z_value: float) -> float:
        return (z_value * self.train_score_std) + self.train_score_mean

    @staticmethod
    def _safe_std(std: float) -> float:
        return std if abs(std) > 1e-8 else 1e-8

    def set_rub_threshold_bands(self, sigma1: float, sigma2: float, sigma3: float):
        self._rub_threshold_bands = (sigma1, sigma2, sigma3)

    @property
    def rub_threshold_bands(self):
        return self._rub_threshold_bands

    def rub_threshold_offsets(self):
        zero_point = self.train_score_mean
        _, sigma2, sigma3 = self._rub_threshold_bands
        low = max(sigma2 - zero_point, 0.0)
        medium = max(sigma3 - zero_point, 0.0)
        return (low, medium, medium)

    def _init_camera(self):
        return cv2.VideoCapture(0, cv2.CAP_DSHOW)

    def time_reset(self):
        if hasattr(self, "audio") and hasattr(self.audio, "time_reset"):
            self.audio.time_reset()
        else:
            self.read_time = 0

    def _make_buffer(self) -> deque:
        buffer_time = self.buffer_time
        sample_rate = self.sample_rate
        block_size = self.block_size
        buffer_length = int(buffer_time * (sample_rate / block_size))
        buffer = deque([np.full(block_size, 0)] * buffer_length, maxlen=buffer_length)
        return buffer

    def start_rub_collection(self, now: float, phase: RubPhase, duration: float):
        self.rub_session.train_time = float(duration)
        self.rub_session.start(now, phase)

    def stop_rub_collection(self):
        self.rub_session.stop()

    def rub_elapsed(self, now: float) -> float:
        return self.rub_session.elapsed(now)

    def rub_collection_completed(self, now: float) -> bool:
        return self.rub_session.completed(now)

    def rub_phase(self):
        return self.rub_session.phase

    def rub_frames(self):
        return self.rub_session.frames

    @property
    def rub_buffer(self) -> np.ndarray:
        return self.rub_session.buffer

    def reset_gmm_pipeline(self):
        self.gmm_pipeline = gmm(self)
        self.gmm_is_infering = False
        self.gmm_pretrained = False
        self.gmm_trained = False

    def reset_rub_session(self):
        self.rub_session = RubSession(train_time=float(self.rub_train_duration_sec))

    @property
    def camera_data(self):
        _, frame = self.camera.read()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_transposed = frame_rgb.transpose((1, 0, 2))
        return frame_transposed

    @property
    def trigger_data(self):
        return self._trigger_data

    @trigger_data.setter
    def trigger_data(self, value):
        self._trigger_data = value
        self.trigger_signal.emit()

    @property
    def train_data(self):
        return self._train_data

    @train_data.setter
    def train_data(self, value):
        value = np.atleast_2d(value)
        if self._train_data.size == 0:
            self._train_data = value
        else:
            self._train_data = np.vstack((self._train_data, value))

    @train_data.deleter
    def train_data(self):
        self._train_data = np.empty((0, 0))

    def _generate_beep_waveform(self) -> np.ndarray:
        samples = max(1, int(self.sample_rate * self.beep_duration_sec))
        t = np.linspace(0.0, self.beep_duration_sec, samples, endpoint=False)
        waveform = self.beep_volume * np.sin(2.0 * np.pi * self.beep_frequency_hz * t)
        envelope_samples = max(1, int(samples * self.beep_envelope_ratio))
        envelope = np.ones(samples, dtype=np.float32)
        fade = np.linspace(0.0, 1.0, envelope_samples, endpoint=True, dtype=np.float32)
        envelope[:envelope_samples] = fade
        envelope[-envelope_samples:] = fade[::-1]
        waveform *= envelope
        return waveform.astype(np.float32)

    @property
    def threshold_data(self):
        return self._threshold_data

    @threshold_data.setter
    def threshold_data(self, value):
        value = np.atleast_2d(value)
        if self._threshold_data.size == 0:
            self._threshold_data = value
        else:
            self._threshold_data = np.vstack((self._threshold_data, value))

    @threshold_data.deleter
    def threshold_data(self):
        self._threshold_data = np.empty((0, 0))

    @property
    def anomaly_threshold(self):
        return self._anomaly_threshold

    @anomaly_threshold.setter
    def anomaly_threshold(self, anomaly):
        mean = np.mean(anomaly)
        std_dev = np.std(anomaly)
        self._anomaly_threshold = (mean + 2 * std_dev, mean + 3 * std_dev)
