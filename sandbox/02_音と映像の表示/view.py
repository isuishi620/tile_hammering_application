# view.py
import pyqtgraph as pg

from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox, QPushButton

class View(QWidget):
    """ビュークラス"""
    signal = pyqtSignal(str, object)

    def __init__(self, ui_path: str) -> None:
        super().__init__()
        uic.loadUi(ui_path, self)
        pg.setConfigOptions(imageAxisOrder="row-major", antialias=True)

        self._connect_buttons()
        self._init_graphics_views()

    def _init_graphics_views(self) -> None:
        self.audio_plot = self.graphicsView.addPlot()
        self.audio_plot.hideAxis('left')
        self.audio_plot.hideAxis('bottom')
        self.audio_plot.getViewBox().setDefaultPadding(0.0)
        self.audio_plot.layout.setContentsMargins(0, 0, 0, 0)
        self.audio_curve = self.audio_plot.plot([], [], pen='w', clipToView=True)

        # self.audio_plot.setYRange(0, 20)
        self.audio_plot.setLabel('left', 'Amp.[Pa]')

        self.camera_viewbox = self.graphicsView_2.addViewBox(lockAspect=True, enableMenu=False)
        self.camera_viewbox.invertY(True)            
        self.camera_viewbox.setDefaultPadding(0.0) 

        self.camera_image = pg.ImageItem()
        self.camera_viewbox.addItem(self.camera_image)

    def plot(self, target, data):
        target.setData(y=data)

    def image(self, target, data):
        target.setImage(data)

    def error(self, error: str) -> None:
        """エラーメッセージを表示する"""
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle("Error")
        dialog.setInformativeText(error)
        dialog.exec_()

    def _connect_buttons(self) -> None:
        """
        画面上の全ての QPushButton にクリックハンドラを動的接続。
        ボタン名（objectName）をシグナルでControllerへ渡す。
        """
        for btn in self.findChildren(QPushButton):
            name = btn.objectName()
            btn.clicked.connect(lambda _=False, n=name, b=btn: self.signal.emit(n, b))
