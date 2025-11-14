# controller.py
import inspect
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QSlider

from model import Model
from view import View

class Controller(QObject):
    """コントローラークラス"""

    def __init__(self, model: Model, view: View) -> None:
        super().__init__()
        self.model = model
        self.view = view
        self.view.signal.connect(self.handle_view_signal)
        self.model.timer.signal.connect(self.handle_timer_signal)

    def handle_timer_signal(self):
        self.view.plot(self.view.audio_curve, self.model.buffer)

    def on_verticalSlider_valueChanged(self, _name, _widget, _event, value):
        """スライダーが変更された後に実行されるメソッド"""
        # self.model.slider_value = self.view.verticalSlider.value()
        self.model.slider_value = value
        self.view.set_threshold(self.model.threshold)


# ============================================================================================
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