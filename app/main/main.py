import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QVBoxLayout, QWidget, QStackedWidget
from PyQt5.QtCore import QObject
from app.util.window import Window

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.stack = QStackedWidget()
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.stack)
        self.setLayout(self.layout)
        self.resize(1150, 750)

        self._routes: dict = {}         # Window -> (controller, view)
        self._current: 'Window|None' = None

    def register(self, window, controller, view):
        self._routes[window] = (controller, view)
        if self.stack.indexOf(view) == -1:
            self.stack.addWidget(view)

    def add(self, widget: QObject):
        self.stack.addWidget(widget)

    def set(self, window):
        self.go_to(window)

    def handle_window(self, arg):
        """
        arg が Window ならそのまま遷移。
        (Window, payload) タプルなら payload を渡して遷移。
        """
        if isinstance(arg, tuple) and len(arg) == 2:
            window, payload = arg
            self.go_to(window, payload)
        else:
            self.go_to(arg, {})

    def go_to(self, window, payload=None):
        if window not in self._routes:
            if hasattr(window, "index"):
                self.stack.setCurrentIndex(window.index)
                self.update_title(window)
                self._current = window
                return
            return

        next_ctrl, next_view = self._routes[window]

        if self._current is not None and self._current in self._routes:
            cur_ctrl, _ = self._routes[self._current]
            try:
                # on_leave(next_route) を呼べるようにしておく
                if hasattr(cur_ctrl, "on_leave"):
                    cur_ctrl.on_leave(next_route=window)
            except Exception as e:
                return

        self.stack.setCurrentWidget(next_view)
        self._current = window
        self.update_title(window)

        try:
            if hasattr(next_ctrl, "on_enter"):
                next_ctrl.on_enter(payload or {})
        except Exception:
            pass

    def update_title(self, window):
        if window == Window.MENU:
            self.setWindowTitle("Menu")
        elif window == Window.TRAIN:
            self.setWindowTitle("Train")
        elif window == Window.TEST:
            self.setWindowTitle("Test")