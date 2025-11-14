# アプリケーションのエントリーポイント

import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    return os.path.join(base_path, relative_path)

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
import qdarkstyle

from app.main.main import MainWindow, Window
from app.model.model import Model
# ===[ menu, train, test ]===
from app.menu.view import MenuView
from app.menu.controller import MenuController
from app.train.view import TrainView
from app.train.controller import TrainController
from app.test.view import TestView
from app.test.controller import TestController

app = QApplication(sys.argv)
app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
# app.setFont(QtGui.QFont('Meiryo'))
app.setFont(QtGui.QFont('Arial'))

main_window = MainWindow()
model = Model()
# ===[ menu ]===
menu_view = MenuView(resource_path('app/ui/menu.ui'))
menu_controller = MenuController(model, menu_view)
menu_controller.signal.connect(main_window.handle_window)
# ===[ train ]===
train_view = TrainView(resource_path('app/ui/train.ui'))
train_controller = TrainController(model, train_view)
train_controller.signal.connect(main_window.handle_window)
# ===[ test ]===
test_view = TestView(resource_path('app/ui/test.ui'))
test_controller = TestController(model, test_view)
test_controller.signal.connect(main_window.handle_window)

# ===[ util\window.py でwindow:MENU,TRAIN,TESTを指定 ]===
# ===[ 各windowのタイトル指定:app\main\main.pyにて ]===
main_window.register(Window.MENU,  menu_controller,  menu_view)
main_window.register(Window.TRAIN, train_controller, train_view)
main_window.register(Window.TEST,  test_controller,  test_view)

# ===[ MENUを表示 ]===
main_window.set(Window.MENU)
main_window.show()


sys.exit(app.exec_())
