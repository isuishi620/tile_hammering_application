import sys
from pathlib import Path

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication

import qdarkstyle

from controller import Controller
from model import Model
from view import View


UI_PATH = "sandbox/01_QtDesignerで作成したUIの読み込み/layout.ui"

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
