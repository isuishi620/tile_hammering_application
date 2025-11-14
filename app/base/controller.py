from PyQt5.QtCore import pyqtSignal, QObject
from .model import ModelBase
from .view import ViewBase
import inspect
import cv2

class ControllerBase(QObject):
    signal = pyqtSignal(object)

    def __init__(self, model:ModelBase, view:ViewBase):
        super().__init__()
        self.model = model

        self.model.trigger_signal.connect(self.handle_trigger_signal)
        self.trigger_methods = []
        
        self.view = view
        self.view.signal.connect(self.handle_view_signal)
        self.timeout_methods = []



    def handle_view_signal(self, name: str, widget: object, event: str, payload=None) -> None:
        """
        Viewから (name, widget, event, payload) を受け取り、
        on_{name}_{event} → on_{event} → on_{name} → on_any の順
        """
        try:
            candidates = [
                f'on_{name}_{event}',  
                f'on_{event}',      
                f'on_{name}',       
                'on_any',           
            ]
            for cname in candidates:
                if hasattr(self, cname):
                    handler = getattr(self, cname)
                    self._invoke(handler, name, widget, event, payload)
                    return
            raise NotImplementedError(f'{name}({event}) に対応するハンドラーが存在しません')
        except Exception as e:
            self.view.error(str(e))

    def _invoke(self, handler, name, widget, event, payload):
        """ハンドラーの引数数に合わせてスマートに呼ぶ（後方互換あり）"""
        args = (name, widget, event, payload)
        n = len(inspect.signature(handler).parameters)
        if n >= 4:
            handler(*args)
        elif n == 3:
            handler(*args[:3])
        elif n == 2:
            handler(*args[:2])
        elif n == 1:
            handler(args[0])
        else:
            handler()


    def handle_trigger_signal(self):
        try:
            for method in self.trigger_methods:
                method()
        except Exception as e:
            self.view.error(str(e))

    def add_trigger_method(self, method):
        if method not in self.trigger_methods:
            self.trigger_methods.append(method)

    def remove_trigger_method(self, method):
        if method in self.trigger_methods:
            self.trigger_methods.remove(method)

    def reset_trigger_method(self):
        self.trigger_methods = []


    def handle_timer_signal(self):
        if self.view.isVisible():
            try:
                for method in self.timeout_methods:
                    method()
            except Exception as e:
                self.view.error(str(e))

    def add_timeout_method(self, method):
        if method not in self.timeout_methods:
            self.timeout_methods.append(method)

    def remove_timeout_method(self, method):
        if method in self.timeout_methods:
            self.timeout_methods.remove(method)

    def reset_timeout_method(self):
        self.timeout_methods = []

    def start_process(self):
        self.model.audio.start()
        self.model.audio_is_stream = True
        self.model.camera_is_stream = True

    # ===[ audio stream ずっと使うので　停止だけで良い ]===
    def end_process(self):
        self.model.audio.stop()# まず停止
        # self.model.audio.close() # 次にリソースを解放
        self.model.audio_is_stream = False
        self.model.camera_is_stream = False
    