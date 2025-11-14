from PyQt5.QtCore import pyqtSignal, QObject, QTimer

class Timer(QObject):
    signal = pyqtSignal()

    def __init__(self, fps):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timeout)
        # self.timer.start(int(interval))
        self.timer.start(int(round(1000 / fps)))
        
    def timeout(self):
        self.signal.emit()
