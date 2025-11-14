import pyqtgraph as pg

from base import ViewBase
            
class View(ViewBase):
    def __init__(self, ui_path):
        super().__init__(ui_path)
        self._init_graphics_views()

    def set_lcd(self, lcd, number):
        lcd.display(number)

    def _init_graphics_views(self) -> None:
        self.audio_plot = self.graphicsView.addPlot()
        self.audio_plot.hideAxis('left')
        self.audio_plot.hideAxis('bottom')
        self.audio_plot.getViewBox().setDefaultPadding(0.0)
        self.audio_plot.layout.setContentsMargins(0, 0, 0, 0)
        self.audio_curve = self.audio_plot.plot([], [], pen='w', clipToView=True)

        self.camera_viewbox = self.graphicsView_2.addViewBox(lockAspect=True, enableMenu=False)
        self.camera_viewbox.invertY(True)            
        self.camera_viewbox.setDefaultPadding(0.0) 

        self.camera_image = pg.ImageItem()
        self.camera_viewbox.addItem(self.camera_image)

        self.anomaly_plot = self.graphicsView_3.addPlot()
        self.anomaly_plot.hideAxis('left')
        self.anomaly_plot.hideAxis('bottom')
        self.anomaly_plot.getViewBox().setDefaultPadding(0.0)
        self.anomaly_plot.layout.setContentsMargins(0, 0, 0, 0)
        self.anomaly_plot.setMouseEnabled(x=False, y=False)
        self.anomaly_scatter = pg.ScatterPlotItem(
            x=[], y=[], pen=None, brush=pg.mkBrush(255, 170, 0, 200), size=10
        )
        self.anomaly_plot.addItem(self.anomaly_scatter)

    def update_anomaly_scatter(self, x_points, y_points, colors):
        if not x_points or not y_points:
            self.anomaly_scatter.setData([], [])
            return
        if not colors or len(colors) != len(y_points):
            brushes = pg.mkBrush(255, 170, 0, 200)
        else:
            brushes = [pg.mkBrush(c) for c in colors]
        self.anomaly_scatter.setData(x=x_points, y=y_points, pen=None, brush=brushes, size=6)

