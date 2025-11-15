from __future__ import annotations

import pyqtgraph as pg
import qdarkstyle as qds
from PyQt5.QtWidgets import QSlider

from app.base.view import ViewBase


class TrainView(ViewBase):
    def __init__(self, ui_path: str):
        super().__init__(ui_path)
        self._set_lcdNumber()
        self._connect_sliders()
        self._init_graphics_view_mic()
        self._init_graphics_view_monitor()

        self.th_pen = pg.mkPen(color=qds.DarkPalette.COLOR_ACCENT_5, width=2)
        self.th_pen = pg.mkPen((255, 80, 80), width=1)
        self.threshold_line = None

    def set_threshold(self, y: float):
        if self.threshold_line is None:
            self.threshold_line = self.audio_plot.addLine(y=y, pen=self.th_pen)
        else:
            self.threshold_line.setValue(y)

    def _connect_sliders(self) -> None:
        """Emit the slider name/value whenever it changes."""
        for slider in self.findChildren(QSlider):
            name = slider.objectName()
            slider.valueChanged.connect(lambda v, n=name, s=slider: self.signal.emit(n, s, "valueChanged", v))

    def set_slider(self, min_value, max_value, value):
        self.verticalSlider_TrigLevel.setRange(min_value, max_value)
        self.verticalSlider_TrigLevel.setValue(value)

    def show_tapping_mode(self, trained: bool, thresholded: bool):
        """Highlight tapping controls and dim rub controls."""
        self._set_active_button(self.pushButton_SetTap, active=True)
        self._set_active_button(self.pushButton_SetRub, active=False)
        self._set_button_enabled(self.pushButton_TrigLevel, enabled=True, active=True)
        self._set_button_enabled(self.verticalSlider_TrigLevel, enabled=True, active=True)
        self._set_button_enabled(self.pushButton_TapTrainSampleStart, enabled=True, active=True)
        self._set_button_enabled(self.pushButton_TapTHSampleStart, enabled=trained, active=trained)

        if thresholded:
            self.set_lcd(self.lcdNumber_TapTHSampleNumber, self.lcdNumber_TapTHSampleNumber.intValue())
            self.label_TapFinish.setText("-finish-")
            self.label_TapFinish.setStyleSheet("background-color: rgb(0, 85, 255); color: red;")
        else:
            self.label_TapFinish.setText("-begin-")
            self.label_TapFinish.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")

        self._set_button_enabled(self.pushButton_RubTrainSampleStart, enabled=False, active=False)
        self.set_rub_threshold_button_enabled(False)
        self.set_rub_status(self.label_RubFinish.text(), background="grey")

    def show_rub_mode(self, rub_pretrained: bool):
        """Highlight rub controls and disable tapping controls."""
        self._set_active_button(self.pushButton_SetTap, active=False)
        self._set_button_enabled(self.pushButton_TrigLevel, enabled=False, active=False)
        self._set_button_enabled(self.verticalSlider_TrigLevel, enabled=False, active=False)
        self._set_button_enabled(self.pushButton_TapTrainSampleStart, enabled=False, active=False)
        self._set_button_enabled(self.pushButton_TapTHSampleStart, enabled=False, active=False)
        self.label_TapFinish.setStyleSheet("background-color: grey;")

        self._set_active_button(self.pushButton_SetRub, active=True)
        self._set_button_enabled(self.pushButton_RubTrainSampleStart, enabled=True, active=True)
        self.set_rub_threshold_button_enabled(rub_pretrained)

    def set_start_test_enabled(self, enabled: bool):
        self.pushButton_StartTest.setEnabled(enabled)
        style = "background-color: rgb(0, 85, 255);" if enabled else "background-color: grey;"
        self.pushButton_StartTest.setStyleSheet(style)

    def set_rub_threshold_button_enabled(self, enabled: bool):
        self._set_button_enabled(self.pushButton_RubTHSampleStart, enabled=enabled, active=enabled)

    def set_rub_status(self, text: str, text_color: str = "white", background: str = "rgb(0, 85, 255)"):
        self.label_RubFinish.setText(text)
        self.label_RubFinish.setStyleSheet(f"background-color: {background}; color: {text_color};")

    def set_lcdNumberAll(
        self,
        tap_train_target_count,
        tap_threshold_target_count,
        rub_train_duration_sec,
        rub_threshold_duration_sec,
    ):
        self.lcdNumber_TapTrainSampleAllNumber.display(tap_train_target_count)
        self.lcdNumber_TapTHSampleAllNumber.display(tap_threshold_target_count)
        self.lcdNumber_RubTrainSampleAllTime.display(rub_train_duration_sec)
        self.lcdNumber_RubTHSampleAllTimes.display(rub_threshold_duration_sec)

    def _set_lcdNumber(self):
        self.lcdNumber_TapTrainSampleNumber.display(0)
        self.lcdNumber_TapTHSampleNumber.display(0)
        self.lcdNumber_RubTrainSampleTime.display(0)
        self.lcdNumber_RubTHSampleTimes.display(0)

    def _init_graphics_view_mic(self) -> None:
        self.audio_plot = self.graphicsView_Mic.addPlot()
        self.audio_plot.hideAxis("left")
        self.audio_plot.hideAxis("bottom")
        self.audio_plot.getViewBox().setDefaultPadding(0.0)
        self.audio_plot.layout.setContentsMargins(0, 0, 0, 0)
        self.audio_curve = self.audio_plot.plot([], [], pen="w", clipToView=True)
        self.audio_plot.setYRange(-20, 20, padding=0)

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

    def _set_active_button(self, button, active: bool):
        style = "background-color: rgb(0, 85, 255); color: white;" if active else "background-color: grey; color: white;"
        button.setStyleSheet(style)

    def _set_button_enabled(self, widget, enabled: bool, active: bool | None = None):
        widget.setEnabled(enabled)
        if active is not None:
            style = "background-color: rgb(0, 85, 255);" if active else "background-color: grey; color: white;"
            widget.setStyleSheet(style)
