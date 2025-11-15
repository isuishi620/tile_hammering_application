from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class Timer(QObject):
    """指定したFPSでQtシグナルを発火させる薄いラッパー。"""

    signal = pyqtSignal()

    def __init__(self, fps: float):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timeout)
        interval_ms = max(1, int(round(1000 / fps)))
        self.timer.start(interval_ms)

    def timeout(self):
        self.signal.emit()
