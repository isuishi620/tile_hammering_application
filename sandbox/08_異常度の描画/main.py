import sys
import inspect
import numpy as np

from PyQt5 import QtGui, uic
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QPushButton
import pyqtgraph as pg
import qdarkstyle


UI_PATH = "sandbox/08_異常度の描画/untitled.ui"

class Model(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.anomaly_list: list= []
        self.threshold: tuple= (1, 2)
        self.display_count: int = 20
        
    @property
    def anomaly_data(self):
        """標準正規分布 N(0,1) の乱数の絶対値を返す。"""
        return np.abs(np.random.randn())

class View(QWidget):
    signal = pyqtSignal(str, object, str, object)

    def __init__(self, ui_path: str) -> None:
        super().__init__()
        uic.loadUi(ui_path, self)
        pg.setConfigOptions(imageAxisOrder="row-major", antialias=True)

        self._connect_buttons()
        self._init_graphics_views()

    def _init_graphics_views(self) -> None:
        self.anomaly_plot = self.graphicsView.addPlot()
        self.anomaly_plot.hideAxis('bottom')
        self.anomaly_plot.setLabel('left', 'Anomaly Score')
        self.scatter = pg.ScatterPlotItem(
            size=20,
            pen=pg.mkPen('w', width=2),
            pxMode=True,  
        )
        self.anomaly_plot.addItem(self.scatter)
        self.anomaly_plot.enableAutoRange('y', True)

    def plot_anomaly_scatter(self, data: list, threshold: tuple, n_points: int) -> None:
        if not data:
            self.scatter.clear()
            return

        last = data[-n_points:] 
        start_idx = len(data) - len(last)
        xs = np.arange(start_idx, start_idx + len(last), dtype=float)

        t1, t2 = threshold
        brushes = []
        for y in last:
            if y < t1:
                brushes.append(pg.mkBrush('b')) 
            elif y < t2:
                brushes.append(pg.mkBrush('y')) 
            else:
                brushes.append(pg.mkBrush('r')) 
        self.scatter.setData(x=xs, y=last, brush=brushes)

        if len(xs) == 1:
            self.anomaly_plot.setXRange(xs[0] - 1, xs[0] + 1, padding=0)
        else:
            self.anomaly_plot.setXRange(xs.min() - 0.5, xs.max() + 0.5, padding=0)



    def error(self, error: str) -> None:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle("Error")
        dialog.setInformativeText(error)
        dialog.exec_()

    def _connect_buttons(self) -> None:
        for btn in self.findChildren(QPushButton):
            name = btn.objectName()
            btn.clicked.connect(
            lambda v, n=name, s=btn: self.signal.emit(n, s, "clicked", v)
        )

class Controller(QObject):

    def __init__(self, model, view) -> None:
        super().__init__()
        self.model = model
        self.view = view
        self.view.signal.connect(self.handle_view_signal)

    def on_pushButton_clicked(self):
        anomaly_data = self.model.anomaly_data
        self.model.anomaly_list.append(anomaly_data)
        self.view.plot_anomaly_scatter(
            self.model.anomaly_list,
            self.model.threshold,
            self.model.display_count
            )
        
    def on_pushButton_2_clicked(self):
        print(f'{len(self.model.anomaly_list)=}')
        
    def handle_view_signal(self, name: str, widget: object, event: str, payload=None) -> None:
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
            raise NotImplementedError(f'{name}({event}) に対応するハンドラーが存在しません')
        except Exception as e:
            self.view.error(str(e))

    def _invoke(self, handler, name, widget, event, payload):
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
