from __future__ import annotations

from typing import Dict, Optional, Tuple

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from app.util.window import Window

Route = Tuple[QObject, QWidget]


class MainWindow(QWidget):
    """Window列挙値に合わせてスタックウィジェットを切り替えるシンプルなルーター。"""

    def __init__(self):
        super().__init__()
        self.stack = QStackedWidget()
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.stack)
        self.setLayout(self.layout)
        self.resize(1150, 750)

        self._routes: Dict[Window, Route] = {}
        self._current: Optional[Window] = None

    def register(self, window: Window, controller: QObject, view: QWidget) -> None:
        """Window列挙値とコントローラー/ビューを対応付ける。"""
        self._routes[window] = (controller, view)
        if self.stack.indexOf(view) == -1:
            self.stack.addWidget(view)

    def add(self, widget: QObject) -> None:
        self.stack.addWidget(widget)

    def set(self, window: Window) -> None:
        self.go_to(window)

    def handle_window(self, arg) -> None:
        """コントローラーからの画面切り替え要求シグナルを処理する。"""
        if isinstance(arg, tuple) and len(arg) == 2:
            window, payload = arg
            self.go_to(window, payload)
        else:
            self.go_to(arg, {})

    def go_to(self, window: Window, payload: Optional[dict] = None) -> None:
        if window not in self._routes:
            if hasattr(window, "index"):
                self.stack.setCurrentIndex(window.index)
                self._current = window
                self._update_title(window)
            return

        next_ctrl, next_view = self._routes[window]

        if self._current is not None and self._current in self._routes:
            cur_ctrl, _ = self._routes[self._current]
            if hasattr(cur_ctrl, "on_leave"):
                try:
                    cur_ctrl.on_leave(next_route=window)
                except Exception:
                    return

        self.stack.setCurrentWidget(next_view)
        self._current = window
        self._update_title(window)

        if hasattr(next_ctrl, "on_enter"):
            try:
                next_ctrl.on_enter(payload or {})
            except Exception:
                pass

    def _update_title(self, window: Window) -> None:
        titles = {
            Window.MENU: "Menu",
            Window.TRAIN: "Train",
            Window.TEST: "Test",
        }
        self.setWindowTitle(titles.get(window, ""))
