import sys

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui, uic
import qdarkstyle
import pyqtgraph as pg

class Model:
    def __init__(self):

        pass

class View:
    def __init__(self, ui):
        self.ui = uic.loadUi(ui)
        self.graphics_view = self.ui.graphicsView.addPlot()

        self.blue_region = pg.LinearRegionItem([0, 1], brush='b', orientation='horizontal')
        self.yellow_region = pg.LinearRegionItem([1, 2], brush='y', orientation='horizontal')
        self.red_region = pg.LinearRegionItem([2, 3], brush='r', orientation='horizontal')

        self.graphics_view.addItem(self.blue_region)
        self.graphics_view.addItem(self.yellow_region)
        self.graphics_view.addItem(self.red_region)

        self.blue_region.sigRegionChanged.connect(lambda: self._handle_region('blue'))
        self.yellow_region.sigRegionChanged.connect(lambda: self._handle_region('yellow'))
        self.red_region.sigRegionChanged.connect(lambda: self._handle_region('red'))

    def _handle_region(self, region_name):
        blue_min, blue_max = self.blue_region.getRegion()
        yellow_min, yellow_max = self.yellow_region.getRegion()
        red_min, red_max = self.red_region.getRegion()

        if region_name == 'blue':
            if blue_max > yellow_min:
                self.blue_region.setRegion([blue_min, yellow_min])
        
        elif region_name == 'yellow':
            if yellow_min < blue_max:
                self.yellow_region.setRegion([blue_max, yellow_max])
            if yellow_max > red_min:
                self.yellow_region.setRegion([yellow_min, red_min])
        
        elif region_name == 'red':
            if red_min < yellow_max:
                self.red_region.setRegion([yellow_max, red_max])

        # Print the current min and max of each region
        print(f"Blue Region: {self.blue_region.getRegion()}")
        print(f"Yellow Region: {self.yellow_region.getRegion()}")
        print(f"Red Region: {self.red_region.getRegion()}")

    def show(self):
        self.ui.show()

        
class Controller:
    def __init__(self,model,view):
        self.model = model
        self.view = view
        self.view.show()
        pass

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    app.setFont(QtGui.QFont('Meyryo'))

    model = Model()
    view = View(r'D:\sakai\projects\tile_hammering_application\sandbox\調整可能な棒グラフ\layout.ui')
    controller = Controller(model, view)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()