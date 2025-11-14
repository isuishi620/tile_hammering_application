# model.py
from PyQt5.QtCore import QObject
import numpy as np
from collections import deque
from timer import Timer
import sounddevice as sd
import cv2

class Model(QObject):
    """モデルクラス"""

    def __init__(self) -> None:
        super().__init__()
        self.fps: int = 30
        self.timer = Timer(self.fps)

        self.sample_rate = 48000
        self.num_channels = 1
        self.dtype = 'float32'
        self.block_size = 2048
        self.buffer_time = 3.0
        
        self.mic_data = None
        self.buffer_blocks = self._make_buffer(time=self.buffer_time,
                                                block_size=self.block_size,
                                                fs=self.sample_rate
                                                )     
        
        self.mic = self._init_microphone()
        self.camera = self._init_camera()

        self.mic_is_stream = False
        self.camera_is_stream = False

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
        x = indata[:, 0].copy()      
        self.mic_data = x            
        self.buffer_blocks.append(x)     

    @property
    def buffer(self) -> np.ndarray:
        if not self.buffer_blocks:
            return np.empty(0, dtype=np.float32)
        return np.concatenate(tuple(self.buffer_blocks))
    
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