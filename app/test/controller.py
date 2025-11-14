import os
from datetime import datetime

from pathlib import Path

from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QFileDialog

from app.base.model import ModelBase
from app.base.view import ViewBase
from app.base.controller import ControllerBase
from app.util.window import Window


class TestController(ControllerBase):

    def __init__(self, model: ModelBase, view: ViewBase):
        super().__init__(model, view)
        self.is_tapping_mode: bool = True
        self.is_playing: bool = False
        self.selected_path: str = os.getcwd()
        self.monitor_view_enabled: bool = True


        self.model = model
        self.view = view

        self.add_timeout_method(self.model.trigger.trigger)
        self.model.timer.signal.connect(self.handle_camera)
                
        self.model.timer.signal.connect(self.handle_timer_signal)
        self.model.timer.signal.connect(self.handle_rub_inference)


    def on_enter(self, payload=None):
        if self.model.thresholded:
            self.is_tapping_mode = True
            self._set_tapping()
        elif self.model.rub_trained:
            self.is_tapping_mode = False
            self._set_tapping()
        else:
            self.view.error('Train tapping or rub test cannot start without training.')
        self.start_process()
    
   

    def on_pushButton_ReturnTraining_clicked(self):
        self.end_process()
        self.model.current_window = Window.TRAIN
        self.signal.emit(Window.TRAIN)
    

    def on_pushButton_Tapping_clicked(self):
        self._stop_playback()
        self.is_tapping_mode = True
        self._set_tapping()

    def on_pushButton_Rubbing_clicked(self):
        self._stop_playback()
        self.is_tapping_mode = False
        self._set_tapping()

    def on_pushButton_NgFolder_clicked(self):
        self.selected_path = self.get_folder_path()           

    def on_pushButton_MonitorViewOn_clicked(self):
        self.monitor_view_enabled = not self.monitor_view_enabled
        
        if self.monitor_view_enabled:
            self.view.pushButton_MonitorViewOn.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")
        else:
            self.view.pushButton_MonitorViewOn.setStyleSheet("background-color: grey; color: white;")
            '''
            try:
                self.model.timer.signal.disconnect(self.handle_camera)
            except TypeError:
                pass
            '''
        

    
    def on_pushButton_play_clicked(self):
        self._update_stop_button(enabled=True, style="background-color: rgb(0, 85, 255);")
        if self.is_tapping_mode:
            self.is_playing = not self.is_playing
            if self.is_playing:
                self.view.pushButton_play.setText('STOP')
                self.model.trigger.start()
                self.add_trigger_method(self.handle_test_data)
            else:
                self.view.pushButton_play.setText('START')
                self.model.trigger.stop()
                self.remove_trigger_method(self.handle_test_data)
        else:
            if not self.model.rub_trained:
                self.view.error('rub test cannot start without training.')
                self._update_stop_button(enabled=False, style="background-color: grey;")
                return
            self.is_playing = not self.is_playing
            if self.is_playing:
                self.view.pushButton_play.setText('STOP')
                self._set_rub_inference(True)
            else:
                self.view.pushButton_play.setText('START')
                self._set_rub_inference(False)


    def on_pushButton_stop_clicked(self):
        self.view.pushButton_play.setEnabled(True)
        self.view.pushButton_play.setStyleSheet("background-color: rgb(0, 85, 255);")
        self._update_stop_button(style="background-color: grey;")
        self._stop_playback()
        

    def handle_camera(self):
        if self.model.camera_is_stream and self.model.current_window == Window.TEST:
            _data = self.model.camera_data
            if self.monitor_view_enabled: 
                self.view.image(self.view.camera_image, _data)

    def handle_test_data(self):
        if not self.is_tapping_mode:
            return
        if self.model.audio_is_stream and self.model.current_window == Window.TEST:
            _trigger_data = self.model.trigger_data
            self.model.test_data = _trigger_data
            anomaly = self.model.pipeline.transform(_trigger_data)[0]
            self.model.test_anomaly = anomaly

            self.view.plot_anomaly_scatter(
                                self.model.test_anomaly,
                                self.model.anomaly_threshold,
                                self.model.display_count
            )

            
            medium = self.model.anomaly_threshold[-1]
            flg_test = True
            if anomaly > medium and flg_test:
                self.save_jpg(anomaly)



    def _set_tapping(self):
        if self.is_tapping_mode:
            self.view.pushButton_Rubbing.setStyleSheet("background-color: grey;")
            if self.model.thresholded:
                self.view.pushButton_Tapping.setStyleSheet("background-color: rgb(0, 85, 255);")
                self.view.pushButton_play.setEnabled(True)
                self.view.pushButton_play.setStyleSheet("background-color: rgb(0, 85, 255);")
                self.view.threshold(low=self.model.anomaly_threshold[0],
                            medium=self.model.anomaly_threshold[-1])
            else:
                self.view.error('Complete tapping training first.')
                self.view.pushButton_play.setEnabled(False)
                self._update_stop_button(enabled=False, style="background-color: grey;")
                self.view.pushButton_play.setStyleSheet("background-color: grey;")
                self.view.pushButton_play.setText('START')
                
        else:
            self.view.pushButton_Tapping.setStyleSheet("background-color: grey;")
            if self.model.rub_trained:
                self.view.pushButton_Rubbing.setStyleSheet("background-color: rgb(0, 85, 255);")
                self.view.pushButton_play.setEnabled(True)
                self.view.pushButton_play.setStyleSheet("background-color: rgb(0, 85, 255);")
                low, medium, high = self.model.rub_threshold_offsets()
                self.view.threshold(low, medium, high)
            else:
                self.view.error('rub test cannot start without training.')
                self.view.pushButton_play.setEnabled(False)
                self._update_stop_button(enabled=False, style="background-color: grey;")
                self.view.pushButton_play.setStyleSheet("background-color: grey;")
                self.view.pushButton_play.setText('START')
                
            


    def _stop_playback(self):
        if self.is_tapping_mode:
            self.model.trigger.stop()
            self.remove_trigger_method(self.handle_test_data)
        else:
            self._set_rub_inference(False)
        self.is_playing = False
        self.view.pushButton_play.setText('START')
        self._update_stop_button(enabled=False, style="background-color: grey;")

    def _update_stop_button(self, enabled=None, style=None):
        button = getattr(self.view, 'pushButton_stop', None)
        if button is None:
            return
        if enabled is not None:
            button.setEnabled(enabled)
        if style is not None:
            button.setStyleSheet(style)

    def _set_rub_inference(self, enabled: bool):
        self.model.gmm_is_infering = enabled
        if not enabled:
            return

    def handle_rub_inference(self):
        if not (self.model.audio_is_stream and self.model.current_window == Window.TEST):
            return
        if self.is_tapping_mode or not self.model.gmm_is_infering or not self.model.rub_trained:
            return
        block = getattr(self.model, "block_data", None)
        if block is None or getattr(block, "size", 0) == 0:
            return
        try:
            raw_anomaly = self.model.compute_rub_anomaly(block)
        except Exception as exc:
            self.view.error(str(exc))
            return
        standardized = self.model.standardize_pretrain(raw_anomaly)
        normalized = self.model.standardize_training(standardized)
        absolute = self.model.denormalize_training(normalized)
        zero_point = self.model.train_score_mean
        anomaly = max(absolute - zero_point, 0.0)
        self.model.record_rub_anomaly_score(anomaly)
        indices, scores, colors = self.model.latest_rub_anomaly_series(self.model.display_count)
        self.view.plot_rub_anomaly_scatter(indices, scores, colors)
        low, medium, high = self.model.rub_threshold_offsets()
        self.view.threshold(low, medium, high)
        if anomaly > high:
            self.save_jpg(anomaly)

    def get_folder_path(self):
        """Allow the operator to pick (or create) a directory for captured files."""
        dialog = QFileDialog(self.view)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setWindowTitle("Select folder")
        if self.selected_path:
            dialog.setDirectory(str(self.selected_path))

        if dialog.exec_() != QFileDialog.Accepted:
            return self.selected_path

        selected = Path(dialog.selectedFiles()[0])
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        memo = self.view.textEdit_memo.toPlainText().strip()
        folder_name = f"{timestamp}_{memo}" if memo else timestamp
        folder_path = selected / folder_name

        if self.view.confirm(f"Create folder {folder_path}?"):
            self.make_dir(folder_path)
            return folder_path

        return selected

    def make_dir(self, folder_path: Path):
        folder_path.mkdir(parents=True, exist_ok=True)

    def make_dir(self, folder_path):

        folder_path.mkdir(parents=True, exist_ok=True)
    
    
    def save_jpg(self, anomaly: float) -> None:
        frame = getattr(self.model, 'camera_data', None)
        if frame is None:
            return

        image = frame.transpose((1, 0, 2)).copy()
        height, width, _ = image.shape
        bytes_per_line = 3 * width

        q_image = QImage(
            image.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        )

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{anomaly:.2f}.jpg"
        base_path = Path(self.selected_path)
        base_path.mkdir(parents=True, exist_ok=True)
        target_path = base_path / filename
        unique_path = Path(get_unique_filepath(str(target_path)))

        if not q_image.save(str(unique_path), 'JPG', 90):
            self.view.error(f"Failed to save snapshot to {unique_path}.")

def get_unique_filepath(filepath_str: str) -> str:
    """Return a unique file path, appending an index if the file already exists."""
    path = Path(filepath_str)
    if not path.exists():
        return str(path)

    parent = path.parent
    stem = path.stem
    suffix = path.suffix

    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return str(candidate)
        i += 1


