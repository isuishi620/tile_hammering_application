# main.py
import sys

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication

import qdarkstyle

from controller import Controller
from model import Model
from view import View


UI_PATH = "sandbox/02_音と映像の表示/layout.ui"

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setFont(QtGui.QFont("Meiryo"))

    model = Model()
    view = View(UI_PATH)
    controller = Controller(model, view)

    view.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
