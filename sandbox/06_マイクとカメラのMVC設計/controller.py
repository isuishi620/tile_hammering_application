# controller.py
import cv2
import inspect
from PyQt5.QtCore import QObject, pyqtSignal, QEvent
from PyQt5.QtWidgets import QApplication

class ControllerBase(QObject):
    """コントローラークラス"""
    navigate = pyqtSignal(str)

    def __init__(self, model, view) -> None:
        super().__init__()
        self.model = model
        self.view = view
        self.view.signal.connect(self.handle_view_signal)
        
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

class Window1Controller(ControllerBase):
    def __init__(self, model, view):
        super().__init__(model, view)
        self.model.timer.signal.connect(self.handle_label)

    def on_pushButton_clicked(self):
        QApplication.quit()

    def on_pushButton_2_clicked(self):
        self.navigate.emit("window2")
        self.model.mic.start()
        self.model.mic_is_stream = True

        self.model.camera_is_stream = True

    def handle_label(self):
        self.view.set_label(self.view.label_2, f'{self.model.mic_is_stream=}')
        self.view.set_label(self.view.label_3, f'{self.model.camera_is_stream=}')

class Window2Controller(ControllerBase):
    def __init__(self, model, view):
        super().__init__(model, view)
        self.model.timer.signal.connect(self.handle_audio)
        self.model.timer.signal.connect(self.handle_camera)

        # ×ボタンでwindowが閉じられた時の処理
        self.view.window().installEventFilter(self)

    def eventFilter(self, _, event):
        if event.type() == QEvent.Close:
            self.end_process()
        return False

    def on_pushButton_clicked(self):
        self.end_process()
        self.view.close()

    def end_process(self):
        self.model.mic.stop()
        self.model.mic_is_stream = False
        self.model.camera_is_stream = False

    def handle_audio(self):
        if self.model.mic_is_stream:
            self.view.plot(self.view.audio_curve, self.model.buffer)

    def handle_camera(self):
        if self.model.camera_is_stream:
            self.view.image(self.view.camera_image, self.model.camera_data)
