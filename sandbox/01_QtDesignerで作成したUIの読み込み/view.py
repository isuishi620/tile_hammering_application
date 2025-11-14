from typing import Any
import numpy as np
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

        self.plot_item = self.graphicsView.addPlot()
        self.plot_item.hideAxis('left')
        self.plot_item.hideAxis('bottom')

        self._connect_buttons()

    def error(self, error: str) -> None:
        """エラーメッセージを表示する"""
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle("Error")
        dialog.setInformativeText(error)
        dialog.exec_()

    def text(self, obj: Any, text: str) -> None:
        """ラベル等 setText を持つオブジェクトに文字列を設定"""
        if hasattr(obj, "setText"):
            obj.setText(text)

    def plot(self, plot_item: pg.PlotItem, data: np.ndarray, **kwargs) -> None:
        """プロット領域をクリアして描画"""
        plot_item.clear()
        plot_item.plot(data, **kwargs)

    def _connect_buttons(self) -> None:
        """
        画面上の全ての QPushButton にクリックハンドラを動的接続。
        ボタン名（objectName）をシグナルでControllerへ渡す。
        """
        for btn in self.findChildren(QPushButton):
            name = btn.objectName()
            # ループ変数の束縛に注意しつつデフォルト引数で閉包
            btn.clicked.connect(lambda _=False, n=name, b=btn: self.signal.emit(n, b))
