import sys
import os
import numpy as np
import pyqtgraph as pg
import qdarkstyle as qds

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.base.view import ViewBase
from PyQt5.QtWidgets import QSlider

class TrainView(ViewBase):
    def __init__(self, ui_path):
        super().__init__(ui_path)

        # self._set_slider()
        self._set_lcdNumber()

        self._connect_sliders()

        # self._set_label()
        # self._set_buttons()
       
        # self.checkBox.setText('USBAudio')
        # self.checkBox.setEnabled(False)
        self._init_graphics_view_mic()
        self._init_graphics_view_monitor()

        self.th_pen = pg.mkPen(color=qds.DarkPalette.COLOR_ACCENT_5, width=2)
        self.th_pen = pg.mkPen((255, 80, 80), width=1)
        self.threshold_line = None


    # ===[ 閾値(物理値)だけを描画する ]===
    def set_threshold(self, y:float):
        if self.threshold_line is None:
            self.threshold_line = self.audio_plot.addLine(
                y=y, pen=self.th_pen
            )
        else:
            self.threshold_line.setValue(y)


    # ===[ スライダーの値が変更された時　int値を取得する ]===
    def _connect_sliders(self) -> None:
        """
        画面上の全ての Qsilder にスライダーが動かされた後のハンドラを動的接続。
        スライダー名（objectName）をシグナルでControllerへ渡す。
        """
        for slider in self.findChildren(QSlider):
            name = slider.objectName()
            slider.valueChanged.connect(
                lambda v, n=name, s=slider: 
                    self.signal.emit(n, s, "valueChanged", v)
            )
      
    # verticalSlider_TrigLevel
    # ===[ 初期設定　トリガレベルのint値 0-100% ]===
    def set_slider(self, min, max, value):
        # 引数(入力) : min   : (1,1) モデルで定義したトリガレベルのint値下限   0
        # 引数(入力) : max   : (1,1) モデルで定義したトリガレベルのint値上限 100
        # 引数(入力) : value : (1,1) モデルで定義したトリガレベルのint値

        # ===[ Qtではintしか設定できない ]===
        # ===[ 0-100% min-max ]===
        self.verticalSlider_TrigLevel.setRange(min, max)
        self.verticalSlider_TrigLevel.setValue(value)


    # lcdNumber All
    def set_lcdNumberAll(self, 
                         tap_train_target_count, 
                         tap_threshold_target_count, 
                         rub_train_duration_sec, 
                         rub_threshold_duration_sec):
        # tap 回数
        # lcdNumber_TapTrainSampleAllNumber 
        self.lcdNumber_TapTrainSampleAllNumber.display(tap_train_target_count)
        # lcdNumber_TapTHSampleAllNumber
        self.lcdNumber_TapTHSampleAllNumber.display(tap_threshold_target_count)
        # rub 時間s
        # lcdNumber_RubTrainSampleAllTime
        self.lcdNumber_RubTrainSampleAllTime.display(rub_train_duration_sec)
        # lcdNumber_RubTHSampleAllTimes
        self.lcdNumber_RubTHSampleAllTimes.display(rub_threshold_duration_sec)

    def _set_lcdNumber(self):
        # tap 回数
        # lcdNumber_TapTrainSampleNumber 学習
        self.lcdNumber_TapTrainSampleNumber.display(0)
        # lcdNumber_TapTHSampleNumber　学習後
        self.lcdNumber_TapTHSampleNumber.display(0)
        

        # rub 時間s
        # lcdNumber_RubTrainSampleTime 学習
        self.lcdNumber_RubTrainSampleTime.display(0)
        # lcdNumber_RubTHSampleTimes 学習後
        self.lcdNumber_RubTHSampleTimes.display(0)
        
    def _init_graphics_view_mic(self) -> None:
        self.audio_plot = self.graphicsView_Mic.addPlot()
        self.audio_plot.hideAxis('left')
        self.audio_plot.hideAxis('bottom')
        self.audio_plot.getViewBox().setDefaultPadding(0.0)
        self.audio_plot.layout.setContentsMargins(0, 0, 0, 0)
        self.audio_curve = self.audio_plot.plot([], [], pen='w', clipToView=True)

        self.audio_plot.setYRange(-20, 20, padding=0)
        # self.audio_plot.setLabel('left', 'Amp.[Pa]')

    
    def _init_graphics_view_monitor(self) -> None:
        self.camera_viewbox = self.graphicsView_Monitor.addViewBox(lockAspect=True, enableMenu=False)
        self.camera_viewbox.invertY(True)            
        self.camera_viewbox.setDefaultPadding(0.0) 

        self.camera_image = pg.ImageItem()
        self.camera_viewbox.addItem(self.camera_image)
 
    def image(self, target, data):
        target.setImage(data)
           

    def plot(self, target, data):
        target.setData(y=data)

    pass
