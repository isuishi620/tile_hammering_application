import inspect
import pyqtgraph as pg
from PyQt5 import uic
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox, QPushButton


class ViewBase(QWidget):
    """Common QWidget utilities shared by all views."""

    signal = pyqtSignal(str, object, str, object)

    def __init__(self, ui_path: str) -> None:
        super().__init__()
        uic.loadUi(ui_path, self)
        pg.setConfigOptions(imageAxisOrder="row-major", antialias=True)
        self._connect_buttons()

    def error(self, error: str) -> None:
        """Display a critical error dialog."""
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle("Error")
        dialog.setInformativeText(error)
        dialog.exec_()

    def set_label(self, obj, text):
        obj.setText(text)

    def plot(self, target, data):
        target.setData(y=data)

    def image(self, target, data):
        target.setImage(data)

    def confirm(self, message: str):
        dialog = QMessageBox()
        dialog.setText(message)
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.setDefaultButton(QMessageBox.No)
        dialog.setWindowTitle("CONFIRM")
        self._center_dialog(dialog)
        response = dialog.exec_()
        return response == QMessageBox.Yes

    def _connect_buttons(self) -> None:
        for btn in self.findChildren(QPushButton):
            name = btn.objectName()
            btn.clicked.connect(
                lambda v, n=name, s=btn: self.signal.emit(n, s, "clicked", v)
            )

    def _center_dialog(self, dialog):
        parent_center = self.mapToGlobal(self.rect().center())
        dialog.adjustSize()
        dialog.move(
            parent_center.x() - dialog.width() // 2,
            parent_center.y() - dialog.height() // 2,
        )


class ControllerBase(QObject):
    """Base controller that dispatches view signals to handlers."""

    navigate = pyqtSignal(str)

    def __init__(self, model, view) -> None:
        super().__init__()
        self.model = model
        self.view = view
        self.view.signal.connect(self.handle_view_signal)

    def handle_view_signal(self, name: str, widget: object, event: str, payload=None) -> None:
        """
        Receive (name, widget, event, payload) from the view and dispatch
        to on_{name}_{event} -> on_{event} -> on_{name} -> on_any, in order.
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
            raise NotImplementedError(f"No handler registered for {name} ({event})")
        except Exception as e:
            self.view.error(str(e))

    def _invoke(self, handler, name, widget, event, payload):
        """Call handlers with flexible arity for backward compatibility."""
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

