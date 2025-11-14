from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication
import qdarkstyle

from app.main.main import MainWindow, Window
from app.menu.controller import MenuController
from app.menu.view import MenuView
from app.model.model import Model
from app.test.controller import TestController
from app.test.view import TestView
from app.train.controller import TrainController
from app.train.view import TrainView


def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", Path(sys.argv[0]).resolve().parent)
    return str(Path(base_path) / relative_path)


def build_controllers(model: Model, main_window: MainWindow):
    menu_view = MenuView(resource_path('app/ui/menu.ui'))
    menu_controller = MenuController(model, menu_view)
    menu_controller.signal.connect(main_window.handle_window)

    train_view = TrainView(resource_path('app/ui/train.ui'))
    train_controller = TrainController(model, train_view)
    train_controller.signal.connect(main_window.handle_window)

    test_view = TestView(resource_path('app/ui/test.ui'))
    test_controller = TestController(model, test_view)
    test_controller.signal.connect(main_window.handle_window)

    main_window.register(Window.MENU, menu_controller, menu_view)
    main_window.register(Window.TRAIN, train_controller, train_view)
    main_window.register(Window.TEST, test_controller, test_view)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setFont(QtGui.QFont('Arial'))

    model = Model()
    main_window = MainWindow()
    build_controllers(model, main_window)

    main_window.set(Window.MENU)
    main_window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
