from __future__ import annotations

from typing import Optional

from PyQt5 import uic
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QPushButton, QWidget


class ViewBase(QWidget):
    """Common utilities shared across every view."""

    signal = pyqtSignal(str, object, str, object)

    def __init__(self, ui_path: str):
        super().__init__()
        self.ui = uic.loadUi(ui_path, self)
        self._popup_dialog: Optional[QMessageBox] = None
        self._connect_buttons()

    # ------------------------------------------------------------------ #
    # Dialog helpers
    # ------------------------------------------------------------------ #
    def error(self, error: str) -> None:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle("Error")
        dialog.setInformativeText(error)
        dialog.exec_()

    def confirm(self, message: str) -> bool:
        dialog = QMessageBox(self)
        dialog.setText(message)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.setWindowTitle("Confirm")
        self._center_dialog(dialog)
        return dialog.exec_() == QMessageBox.Yes

    def show_popup(self, message: str, title: str = "Processing") -> None:
        if self._popup_dialog is None:
            dialog = QMessageBox(self)
            dialog.setIcon(QMessageBox.Information)
            dialog.setWindowTitle(title)
            dialog.setStandardButtons(QMessageBox.NoButton)
            self._popup_dialog = dialog
        self._popup_dialog.setText(message)
        self._popup_dialog.show()

    def close_popup(self) -> None:
        if self._popup_dialog is None:
            return
        self._popup_dialog.close()
        self._popup_dialog.deleteLater()
        self._popup_dialog = None

    def _center_dialog(self, dialog: QMessageBox) -> None:
        parent_center = self.mapToGlobal(self.rect().center())
        dialog.adjustSize()
        dialog.move(parent_center.x() - dialog.width() // 2, parent_center.y() - dialog.height() // 2)

    def save_file_dialog(self, file_name: str) -> Optional[str]:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save",
            file_name,
            "Pickle Files (*.pickle)",
        )
        return file_path or None

    def read_file_dialog(self) -> Optional[str]:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Read",
            "",
            "Pickle Files (*.pickle)",
        )
        return file_path or None

    # ------------------------------------------------------------------ #
    # UI helpers
    # ------------------------------------------------------------------ #
    def _connect_buttons(self) -> None:
        """Emit a signal whenever any button on the view is clicked."""
        for btn in self.findChildren(QPushButton):
            name = btn.objectName()
            btn.clicked.connect(lambda _=False, n=name, b=btn: self.signal.emit(n, b, "clicked", None))

    def trigger_button_click(self, button, delay_ms: int = 0) -> None:
        QTimer.singleShot(delay_ms, button.click)

    def set_lcd(self, lcd, number) -> None:
        lcd.display(number)
