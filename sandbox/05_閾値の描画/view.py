# view.py
import pyqtgraph as pg

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox, QSlider

class View(QWidget):
    """ビュークラス"""
    signal = pyqtSignal(str, object, str, object)

    def __init__(self, ui_path: str) -> None:
        super().__init__()
        uic.loadUi(ui_path, self)
        pg.setConfigOptions(imageAxisOrder="row-major", antialias=True)
        self._connect_sliders()
        self._init_graphics_views()

    def _init_graphics_views(self) -> None:
        self.audio_plot = self.graphicsView.addPlot()
        self.audio_plot.hideAxis('left')
        self.audio_plot.hideAxis('bottom')
        self.audio_plot.getViewBox().setDefaultPadding(0.0)
        self.audio_plot.layout.setContentsMargins(0, 0, 0, 0)
        self.audio_plot.setYRange(-1, 1)
        self.audio_curve = self.audio_plot.plot([], [], pen='w', clipToView=True)

        self.threshold_line = None

    def plot(self, target, data):
        target.setData(y=data)

    def set_threshold(self, y:float):
        if self.threshold_line is None:
            self.threshold_line = self.audio_plot.addLine(
                y=y, pen=pg.mkPen((255, 80, 80), width=1)
            )
        else:
            self.threshold_line.setValue(y)
            
    def error(self, error: str) -> None:
        """エラーメッセージを表示する"""
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle("Error")
        dialog.setInformativeText(error)
        dialog.exec_()

    def _connect_sliders(self) -> None:
        """
        画面上の全ての Qsilder にスライダーが動かされた後のハンドラを動的接続。
        スライダー名（objectName）をシグナルでControllerへ渡す。
        """
        for slider in self.findChildren(QSlider):
            name = slider.objectName()
            slider.valueChanged.connect(
            lambda v, n=name, s=slider: self.signal.emit(n, s, "valueChanged", v)
        )