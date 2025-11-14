import sys
import os
import cv2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtCore import pyqtSignal
from app.base.model import ModelBase
import numpy as np
from app.util.timer import Timer
from collections import deque
from app.util.read import Read
from app.util.trigger import Trigger
from app.pipeline.pipeline import melspec_zscore, gmm
from app.model.rub import RubSession, RubPhase

class Model(ModelBase):
    trigger_signal = pyqtSignal()
    rub_progress = pyqtSignal(float)


    def __init__(self):
        super().__init__()

        # ===[ 0-100% min-max ]===
        # ===[ トリガレベル int　最小値　最大値　現在値 ]===
        self.trig_level_min: int =   0
        # ===[ int指定 0-100 or 0-255 ]===
        self.trig_level_max: int = 100
        self.trig_level_val: int =  50
        # ===[ トリガレベル物理値 float　最小値　最大値　現在値 ]===
        self.threshold_min: float =  0.0
        self.threshold_max: float = 20.0
        self._trigger_threshold: float = 0.0

        # ===[ tap 訓練データ目標数 ]===
        self.tap_train_target_count: int = 30
        # ===[ tap 閾値データ目標数 ]===
        self.tap_threshold_target_count: int = 30
        # ===[ rub 訓練収集時間 (s) ]===
        self.rub_train_duration_sec: float = 2
        # ===[ rub 閾値収集時間 (s) ]===
        self.rub_threshold_duration_sec: float = 2
        self.rub_session = RubSession(train_time=float(self.rub_train_duration_sec))
        self._rub_train_elapsed: float = 0.0
        self._rub_th_elapsed: float = 0.0

        # ===[ MICデータ ]===
        self.fps: int = 30
        self.timer = Timer(self.fps)
        
        self.audio_is_stream: bool = False
        self.camera_is_stream: bool = False
        self.sample_rate: int = 48000
        self.input: int = 2
        self.dtype: str = 'int16'
        self.block_size: int = 2048
        self.ch: int = 0
        # ===[ 134dB range ]===
        # ===[ L_pa_max = 20*10**(-6)*10**(134/20) ]===
        # ===[ R_pa_max = 20*10**(-6)*10**(104/20) ]===
        # ===[ L_EU = (L_pa_max*2)/2**(16) ]===
        # ===[ R_EU = (R_pa_max*2)/2**(16) ]===
        # self.eu: float = 0.003059004
        self.eu: float = 0.1
        self.api: str = 'WASAPI'
        self.device: str = 'ライン'
        # self.block_data: np.adarray = None
        self._block_data = np.array([])
        self.buffer_time: float = 1.0
        # self._buffer_data =  deque()
        self._buffer_data = self._make_buffer()

        # ===[ micとcameraを分離 ]===
        # ===[ audio read time ]===
        self.read_time: float = 0.0
        self.audio = Read(self)
        self.camera = self._init_camera()
        # self.camera_data: any = None    

        # ===[ PL_BPF ]===
        self.PL_BPF_f_min: int = 300
        self.PL_BPF_f_max: int = 16000
        self.PL_BPF_g_pass: int = 3
        self.PL_BPF_g_stop: int = 40
        # ===[ PL_FFT ]===
        self.PL_FFT_n_fft: int = 4096
        self.PL_FFT_power: int = 2
        self.window: str = 'hann'
        self.noverlap: int = int(self.PL_FFT_n_fft * 0.75)
        # ===[ PL_MEL ]===
        self.PL_MEL_n_mels: int = 40
        self.PL_MEL_f_min: int = 1000
        self.PL_MEL_f_max: int = 16000

        # ===[ trigger の初期化 ]===
        self.trigger = Trigger(self)
        self.trigger_is_active: bool = False
        self._trigger_data = np.array([])
        self.pipeline = melspec_zscore(self)
        self.n_components: int = 1
        self.covariance_type: str = 'full'
        self.random_state: int = 42
        self.gmm_pipeline = gmm(self)
        self.gmm_is_infering: bool = False
        self.gmm_pretrained: bool = False
        self.gmm_calibrated: bool = False
        self.pretrain_score_mean: float = 0.0
        self.pretrain_score_std: float = 1.0
        self.train_score_mean: float = 0.0
        self.train_score_std: float = 1.0
        self.rub_anomaly_threshold_sigma: float = 3.0
        self._rub_threshold_bands = (0.0, 0.0, 0.0)
        self.rub_anomaly_scores: list = []
        self.rub_anomaly_history_size: int = 50


        self.trained: bool = False
        self._train_data = np.empty((0, 0))

        # ===[ 閾値 ]===
        self._threshold_data = np.empty((0, 0))
        self.thresholded: bool = False
        # ===[ 異常値 ]===
        self._anomaly_threshold = None

        # ===[ rub 閾値 ]===
        self.rub_thresholded: bool = False
        self.rub_trained: bool = False
        self.rub_train_data = np.empty((0, 0))


        # ===[ Test画面　未使用 ]===
        self.test_tap_on: bool = False
        self.test_rub_on: bool = False


        # ===[ 0:menu / 1:train / 2:test ]===
        self.curl_window: int = 0

        self._test_data = np.empty((0, 0))
        self._test_anomaly = []
        # ===[ 異常値描画個数 ]===
        self.display_count: int = 20
        
    
    # ===[ test data ]===
    @property
    def test_data(self):
        return self._test_data
    
    @test_data.setter
    def test_data(self, value):
        value = np.atleast_2d(value)
        if self._test_data.size == 0:
            self._test_data = value
        else:
            self._test_data = np.vstack((self._test_data, value))

    @test_data.deleter
    def test_data(self):
        self._test_data = np.empty((0, 0))

    @property
    def test_anomaly(self):
        return self._test_anomaly
        #return np.array(self._test_anomaly)
    
    @test_anomaly.setter
    def test_anomaly(self,value):
        self._test_anomaly.append(value)

    # ===[ トリガーレベル物理値 ]===
    @property
    def trigger_threshold(self):
        return self._trigger_threshold
    
    @trigger_threshold.setter    
    def trigger_threshold(self, value) -> float:
        self._trigger_threshold = value

    # ===[ トリガーレベルから物理値への変換 ]===
    def trig_level2th(self):
        range_trig = self.trig_level_max - self.trig_level_min
        percent = (self.trig_level_val - self.trig_level_min) / range_trig
        range_th = self.threshold_max - self.threshold_min
        value = range_th * percent + self.threshold_min
        return value

    # ===[ 物理値からトリガーレベルへの変換 ]===
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
            progress = self.rub_session.append_frame(self._block_data, len(self._block_data), self.sample_rate)
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

    # ===[ Rub anomaly utilities ]===
    def compute_rub_anomaly(self, signal: np.ndarray) -> float:
        if self.gmm_pipeline is None:
            raise RuntimeError("GMM pipeline is not initialized.")
        scores = self.gmm_pipeline.transform(signal)
        return float(np.mean(scores))

    def record_rub_anomaly_score(self, score: float) -> None:
        self.rub_anomaly_scores.append(score)
        if len(self.rub_anomaly_scores) > self.rub_anomaly_history_size:
            self.rub_anomaly_scores = self.rub_anomaly_scores[-self.rub_anomaly_history_size:]

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
        low, medium, high = self._rub_threshold_bands
        colors = []
        for score in scores:
            if score < low:
                colors.append('#2196F3')
            elif score < medium:
                colors.append('#FFEB3B')
            elif score >= high:
                colors.append('#F44336')
            else:
                colors.append('#FF9800')
        return colors

    def standardize_pretrain(self, score: float) -> float:
        return (score - self.pretrain_score_mean) / self._safe_std(self.pretrain_score_std)

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


    def _init_camera(self):
        return cv2.VideoCapture(0,cv2.CAP_DSHOW)

    def time_reset(self):
        if hasattr(self, 'audio') and hasattr(self.audio, 'time_reset'):
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

    # ===[ Rub session helpers ]===
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

    @property
    def camera_data(self):
        _, frame = self.camera.read()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 軸を入れ替える: (height, width, ch) -> (width, height, ch)
        # (Y, X, 色) から (X, Y, 色) へ変換
        frame_transposed = frame_rgb.transpose((1, 0, 2))
        return frame_transposed


    # ===[ トリガーデータ ]===
    @property
    def trigger_data(self):
        return self._trigger_data
    
    @trigger_data.setter
    def trigger_data(self,value):
        self._trigger_data = value
        self.trigger_signal.emit()

    # ===[ 訓練データ ]===
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

    # ===[ 閾値値データ ]===
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
    def anomaly_threshold(self,anomaly):
        mean = np.mean(anomaly)
        std_dev = np.std(anomaly)
        self._anomaly_threshold = (mean + 2 * std_dev, mean + 3 * std_dev)
