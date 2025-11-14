# main.py
import sys
from pathlib import Path

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QStackedWidget

import qdarkstyle

from model import Model
from view import View
from controller import Controller


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setFont(QtGui.QFont("Meiryo"))

    model = Model()
    ui_path = Path(__file__).with_name("untitled.ui")
    view = View(str(ui_path))
    controller = Controller(model, view)
    view.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
