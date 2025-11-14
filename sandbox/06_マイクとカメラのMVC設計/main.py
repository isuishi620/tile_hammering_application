# main.py
import sys

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication,  QStackedWidget

import qdarkstyle

from model import Model
import view as v
import controller as c

WINDOW_1 = "sandbox/06_マイクとカメラのMVC設計/window1.ui"
WINDOW_2 = "sandbox/06_マイクとカメラのMVC設計/window2.ui"

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setFont(QtGui.QFont("Meiryo"))

    model = Model()

    v1 = v.Window1View(WINDOW_1)
    v2 = v.Window2View(WINDOW_2)

    c1 = c.Window1Controller(model, v1)
    c2 = c.Window2Controller(model, v2)
    
    c1.navigate.connect(lambda: v2.show())

    v1.show()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
