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
from app.pipeline.pipeline import melspec_zscore

class Model(ModelBase):
    trigger_signal = pyqtSignal()


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

        # ===[ tap 訓練　最大回数 ]===
        self.tap_train_sample_all_number: int = 30
        # ===[ tap 閾値　最大回数 ]===
        self.tap_th_sample_all_number: int = 30
        # ===[ rub 訓練　最大時間 s ]===
        self.rub_train_sample_all_number: int = 30
        # ===[ rub 閾値　最大時間 s ]===
        self.rub_th_sample_all_number: int = 30

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
        # ===[ PL_MEL ]===
        self.PL_MEL_n_mels: int = 40
        self.PL_MEL_f_min: int = 1000
        self.PL_MEL_f_max: int = 16000

        # ===[ trigger の初期化 ]===
        self.trigger = Trigger(self)
        self.trigger_is_active: bool = False
        self._trigger_data = np.array([])
        self.pipeline = melspec_zscore(self)


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
        return 3
    
    @property
    def rub_th_sample_number(self) -> int:
        return 4
    
    @property
    def block_data(self) -> np.ndarray:
        return self._block_data
    
    @block_data.setter
    def block_data(self, value: np.ndarray):
        self._block_data = np.array(value)
        self.buffer_data = self._block_data

    @property
    def buffer_data(self) -> np.ndarray:
        if len(self._buffer_data) == 0:
            return np.array([])
        return np.concatenate(list(self._buffer_data))
    
    @buffer_data.setter
    def buffer_data(self, value: np.ndarray):
        self._buffer_data.append(value)



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
