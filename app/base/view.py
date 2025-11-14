from PyQt5.QtWidgets import QWidget, QPushButton, QMessageBox, QCheckBox, QButtonGroup, QFileDialog
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QTimer


class ViewBase(QWidget):
    # signal = pyqtSignal(str, object)
    signal = pyqtSignal(str, object, str, object)

    def __init__(self, ui_path):
        super().__init__()
        self.ui = uic.loadUi(ui_path, self)
        self._popup_dialog = None
        self._connect_buttons()

    def error(self, error: str) -> None:
        """
        エラーメッセージを表示する
        """
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle("Error")
        dialog.setInformativeText(error)
        dialog.exec_()

    def _connect_buttons(self) -> None:
        """
        画面上の全ての QPushButton にクリックハンドラを動的接続
        ボタン名（objectName）をシグナルでControllerへ渡す
        """
        for btn in self.findChildren(QPushButton):
            name = btn.objectName()
            btn.clicked.connect(lambda _=False, n=name, b=btn: 
                                self.signal.emit(n, b, "clicked", None))
            
    def trigger_button_click(self, button, delay_ms=0):
        QTimer.singleShot(delay_ms, button.click)

 
    def set_lcd(self,lcd,number):
        lcd.display(number)
   
    def confirm(self, message: str):
        dialog = QMessageBox()
        dialog.setText(message)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.setWindowTitle("CONFIRM")
        self._center_dialog(dialog)
        response = dialog.exec_()
        return response == QMessageBox.Yes

    def show_popup(self, message: str, title: str = "Processing"):
        if self._popup_dialog is None:
            dialog = QMessageBox(self)
            dialog.setIcon(QMessageBox.Information)
            dialog.setWindowTitle(title)
            dialog.setStandardButtons(QMessageBox.NoButton)
            self._popup_dialog = dialog
        self._popup_dialog.setText(message)
        self._popup_dialog.show()

    def close_popup(self):
        if self._popup_dialog is not None:
            self._popup_dialog.close()
            self._popup_dialog.deleteLater()
            self._popup_dialog = None
    
    def _center_dialog(self, dialog):
        parent_center = self.mapToGlobal(self.rect().center())
        dialog.adjustSize()
        dialog.move(parent_center.x() - dialog.width() // 2,
                    parent_center.y() - dialog.height() // 2)
    
    def save_file_dialog(self,file_name):
        dialog = QFileDialog()
        self._center_dialog(dialog)

        options = dialog.Options()
        options |= QFileDialog.ShowDirsOnly
        file_path, _ = QFileDialog.getSaveFileName(None, "SAVE", file_name, "Pickle Files (*.pickle)")
        if file_path:
            return file_path
        else:
            return None
    
    def read_file_dialog(self):
        dialog = QFileDialog()
        self._center_dialog(dialog)

        options = dialog.Options()
        options |= QFileDialog.ShowDirsOnly
        file_path, _ = QFileDialog.getOpenFileName(None, "REad",filter="Pickle Files (*.pickle)")
        if file_path:
            return file_path
        else:
            return None



