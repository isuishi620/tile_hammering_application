import sys
import os
import pyqtgraph as pg

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from app.base.view import ViewBase
import qdarkstyle as qds


class TestView(ViewBase):
    def __init__(self, ui_path):
        super().__init__(ui_path)

        # self._set_label()
        # self._set_buttons()
       
        # self.checkBox.setText('USBAudio')
        # self.checkBox.setEnabled(False)
        self._init_graphics_view_monitor()
        self._set_graphicsView_Data()
        self.anomaly_plot_item = None

    
    def _init_graphics_view_monitor(self) -> None:
        self.camera_viewbox = self.graphicsView_Monitor.addViewBox(lockAspect=True, enableMenu=False)
        self.camera_viewbox.invertY(True)            
        self.camera_viewbox.setDefaultPadding(0.0) 

        self.camera_image = pg.ImageItem()
        self.camera_viewbox.addItem(self.camera_image)

    # graphicsView_Data
    def _set_graphicsView_Data(self):
        self.anomaly_plot = self.graphicsView_Data.addPlot(row=0, col=0)
        self.graphicsView_Data_2 = self.graphicsView_Data.addPlot(row=0, col=1)
        self.graphicsView_Data_2.setYLink(self.anomaly_plot)

        self.graphicsView_Data.ci.layout.setColumnStretchFactor(0, 10)
        self.graphicsView_Data.ci.layout.setColumnStretchFactor(1, 1)

        self.anomaly_plot.setLabel('left', 'Anomaly Score')
        self.anomaly_plot.setLabel('bottom', 'Data')
        self.anomaly_plot.showGrid(x=True, y=True)
        self.scatter = pg.ScatterPlotItem(
            size=20,
            pen=pg.mkPen('w', width=2),
            pxMode=True,  
        )
        self.anomaly_plot.addItem(self.scatter)
        self.anomaly_plot.enableAutoRange('y', True)
        self.anomaly_plot.setMouseEnabled(x=False, y=True)

        self.graphicsView_Data_2.setLabel('bottom', ' ')
        self.graphicsView_Data_2.hideAxis('left')

        self.blue_bar_2_2 = pg.BarGraphItem(x=[1], height=[0], width=1, pen=None, brush=qds.DarkPalette.COLOR_ACCENT_5)
        self.yellow_bar_2_2 = pg.BarGraphItem(x=[1], height=[0], width=1, pen=None, brush='y')
        self.red_bar_2_2 = pg.BarGraphItem(x=[1], height=[0], width=1, pen=None, brush='r')
                                           
        self.graphicsView_Data_2.addItem(self.blue_bar_2_2)
        self.graphicsView_Data_2.addItem(self.yellow_bar_2_2)
        self.graphicsView_Data_2.addItem(self.red_bar_2_2)
        
        self.graphicsView_Data_2.setMouseEnabled(x=False, y=False)
    

    # ===[ Test画面　異常値描画 list ]===
    def plot_anomaly_scatter(self, data: list, threshold: tuple, n_points: int) -> None:
        if not data:
            self.scatter.clear()
            return

        last = data[-n_points:] 
        start_idx = len(data) - len(last)
        xs = np.arange(start_idx, start_idx + len(last), dtype=float)

        t1, t2 = threshold
        print(f'{data=}')
        print(f'{threshold=}')
        print(f'{threshold=}')
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

    def plot_rub_anomaly_scatter(self, indices, scores, colors):
        if not indices or not scores:
            self.scatter.clear()
            return
        brushes = [pg.mkBrush(c) for c in colors] if colors else pg.mkBrush('w')
        self.scatter.setData(x=indices, y=scores, brush=brushes)
        if len(indices) == 1:
            self.anomaly_plot.setXRange(indices[0] - 1, indices[0] + 1, padding=0)
        else:
            self.anomaly_plot.setXRange(min(indices) - 0.5, max(indices) + 0.5, padding=0)


    def threshold(self, low, medium):
        max = medium * 10
        self.blue_bar_2_2.setOpts(height=[low], y0=[0])        
        
        yellow_height = medium - low if medium > low else 0
        self.yellow_bar_2_2.setOpts(height=[yellow_height], y0=[low])
        
        red_height = max - medium if medium < max else 0  
        self.red_bar_2_2.setOpts(height=[red_height], y0=[medium])

    def image(self, target, data):
        target.setImage(data)

    pass
