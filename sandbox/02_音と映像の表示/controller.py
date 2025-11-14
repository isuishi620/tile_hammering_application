# controller.py
import inspect
import cv2

from PyQt5.QtCore import QObject
import sounddevice as sd

from model import Model
from view import View
from timer import Timer


class Controller(QObject):
    """コントローラークラス"""

    def __init__(self, model: Model, view: View) -> None:
        super().__init__()
        self.model = model
        self.timer = Timer(fps=self.model.fps)
        self.view = view
        self.view.signal.connect(self.handle_view_signal)

        print(sd.default.samplerate)
        print(sd.default.channels)
        print(sd.default.dtype)
        print(sd.default.blocksize)                 
        SAMPLING_RATE = 48000
        NUM_CHANNELS = 2 # チャンネル数(1にしたら基本的にLchのみになる)
        # CH = 1 # Rchを指定
        DTYPE = 'int16'
        BLOCK_SIZE = 2048
        # EU = 0.0006103515625

        # sd.default.device = [INPUT, None]
        sd.default.samplerate = SAMPLING_RATE
        sd.default.channels = NUM_CHANNELS
        sd.default.dtype = DTYPE
        sd.default.blocksize = BLOCK_SIZE
        
        print(sd.default.samplerate)
        print(sd.default.channels)
        print(sd.default.dtype)
        print(sd.default.blocksize)  

        self.audio = sd.InputStream(callback=self.audio_callback)
        self.audio.start()
        self.timer.signal.connect(self.handle_audio)
        
        self.camera = cv2.VideoCapture(0,cv2.CAP_DSHOW)
        self.timer.signal.connect(self.handle_camera)

    def on_pushButton_clicked(self):
        if not self.model.audio_is_stream:
            self.model.audio_is_stream = True
        else:
            self.model.audio_is_stream = False

    def on_pushButton_2_clicked(self):
        if not self.model.camera_is_stream:
            self.model.camera_is_stream = True
        else:
            self.model.camera_is_stream = False

    def handle_audio(self):
        if self.model.audio_is_stream:
            self.view.plot(self.view.audio_curve, self.model.audio)

    def handle_camera(self):
        if self.model.camera_is_stream:
            _, frame = self.camera.read()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.model.camera = frame_rgb
            self.view.image(self.view.camera_image, self.model.camera)

    def audio_callback(self, indata, frames, time, status):
        # ===[ 0.00061035 -> 134 dB 0.00305900411149 ]===
        data = indata[:, 0] * 0.003059004
        self.model.audio = data.copy()

    def handle_view_signal(self, name: str, ins: object) -> None:
        """
        Viewから (ウィジェット名, インスタンス) を受け取り、
        on_{name}_clicked を動的に呼び出す。
        """
        try:
            handler_name = f'on_{name}_clicked'
            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                sig = inspect.signature(handler)
                num_params = len(sig.parameters)
                if num_params == 2:
                    handler(name, ins)  # on_xxx(self, name, ins)
                elif num_params == 1:
                    handler(name)       # on_xxx(self, name)
                else:
                    handler()           # on_xxx(self)
            else:
                raise NotImplementedError(f'{name} に対応するハンドラーが存在しません')
        except Exception as e:
            self.view.error(str(e))
