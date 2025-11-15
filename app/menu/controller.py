from __future__ import annotations

import pickle
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from app.base.controller import ControllerBase
from app.base.model import ModelBase
from app.base.view import ViewBase
from app.util.window import Window


class MenuController(ControllerBase):
    """起動画面での遷移と保存データ読込を担当するコントローラー。"""

    def __init__(self, model: ModelBase, view: ViewBase):
        super().__init__(model, view)

    def on_pushButton_new_training_clicked(self):
        self.model.current_window = Window.TRAIN
        self.signal.emit(Window.TRAIN)

    def on_pushButton_load_condition_clicked(self):
        if self._load_condition():
            self.model.current_window = Window.TEST
            self.signal.emit(Window.TEST)

    def on_pushButton_end_clicked(self):
        QApplication.quit()

    def _load_condition(self) -> bool:
        if not self.view.confirm("Load saved training/threshold data?"):
            return False

        filepath = self.view.read_file_dialog()
        if not filepath:
            self.view.error("No file selected.")
            return False

        try:
            with Path(filepath).open("rb") as file:
                data = pickle.load(file)
        except (OSError, pickle.UnpicklingError) as exc:
            self.view.error(f"Failed to load file: {exc}")
            return False

        self._delete_threshold_data()
        self._delete_train_data()

        self.model.train_data = data.get("train_data", [])
        self.model.threshold_data = data.get("threshold_data", [])
        self.model.trigger_threshold = data.get(
            "trigger_threshold", self.model.trigger_threshold
        )
        self.model.anomaly_threshold = data.get(
            "anomaly_threshold", self.model.anomaly_threshold or (0.0, 0.0)
        )
        self.model.trig_level_val = self.model.trig_th2level()

        if self.model.tap_train_sample_number == self.model.tap_train_target_count:
            self.model.pipeline.fit(self.model.train_data)
            self.model.trained = True

        if self.model.tap_th_sample_number == self.model.tap_threshold_target_count:
            self.model.thresholded = True
            anomaly = self.model.pipeline.transform(self.model.threshold_data)
            self.model.anomaly_threshold = anomaly

        return True

    def _delete_threshold_data(self):
        self.model.thresholded = False
        del self.model.threshold_data

    def _delete_train_data(self):
        self.model.trained = False
        del self.model.train_data
