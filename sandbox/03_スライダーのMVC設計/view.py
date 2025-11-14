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
            slider.sliderReleased.connect(lambda n=name, s=slider:
                                          self.signal.emit(n, s, "sliderReleased", None))