import time
from typing import Iterable, List, Sequence

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from base import ControllerBase
from rub import RubPhase


class GMMFitWorker(QThread):
    succeeded = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, pipeline, data):
        super().__init__()
        self._pipeline = pipeline
        self._data = data

    def run(self):
        try:
            self._pipeline.fit(self._data)
            self.succeeded.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class Controller(ControllerBase):
    def __init__(self, model, view):
        super().__init__(model, view)
        timer_signal = self.model.timer.signal
        timer_signal.connect(self.handle_audio)
        timer_signal.connect(self.handle_camera)
        timer_signal.connect(self.handle_gmm_inference)
        self.model.rub_progress.connect(self._on_rub_progress)
        self._gmm_fit_worker = None
        self.start()

    @property
    def rub(self):
        return self.model.rub_session

    def on_pushButton_clicked(self):
        """Pre-training phase."""
        self._start_capture(RubPhase.PRETRAIN)

    def on_pushButton_2_clicked(self):
        """Training phase."""
        if not self.model.gmm_pretrained:
            self.view.error("Please finish the pre-training phase first.")
            return
        self._start_capture(RubPhase.TRAIN)

    def on_pushButton_3_clicked(self):
        """Testing phase toggle."""
        if self.model.gmm_is_infering:
            self._set_gmm_inference(False)
        else:
            if not self.model.gmm_calibrated:
                self.view.error("Complete the training phase before testing.")
                return
            self._set_gmm_inference(True)

    def _start_capture(self, phase: RubPhase) -> None:
        if self._gmm_fit_worker is not None:
            self.view.error("GMM fitting is still running. Please wait.")
            return
        if self.rub.is_active():
            self.view.error("Audio capture is already active.")
            return
        if self.model.gmm_is_infering:
            self.view.error("Stop testing before collecting new data.")
            return
        self.model.start_rub_collection(time.monotonic(), phase)

    def start(self):
        self.model.mic.start()
        self.model.mic_is_stream = True
        self.model.camera_is_stream = True

    def handle_audio(self):
        if self.model.mic_is_stream:
            self.view.plot(self.view.audio_curve, self.model.buffer)

    def handle_camera(self):
        if self.model.camera_is_stream:
            self.view.image(self.view.camera_image, self.model.camera_data)

    def handle_gmm_inference(self):
        if not (self.model.gmm_is_infering and self.model.gmm_calibrated):
            return

        x = self.model.mic_data   # current frame (2048 samples)
        if x is None or x.size == 0:
            return

        raw_anomaly = self.model.compute_anomaly(x)
        standardized = self.model.standardize_pretrain(raw_anomaly)
        z2 = self.model.standardize_training(standardized)
        z2 = max(0.0, z2)
        self.model.record_anomaly_score(z2)
        self._refresh_anomaly_plot()
        self.view.set_lcd(self.view.lcdNumber_2, z2)

        is_anomaly = z2 > self.model.anomaly_threshold
        status = 'ANOMALY' if is_anomaly else 'normal'
        print(f"[Testing] {z2:.3f} -> {status}")

    def _on_rub_progress(self):
        if not self.rub.is_active():
            return

        now = time.monotonic()
        elapsed = self.model.rub_elapsed(now)
        self.view.set_lcd(self.view.lcdNumber, int(elapsed))

        if self.model.rub_collection_completed(now):
            self._complete_session()

    def _complete_session(self):
        phase = self.model.rub_phase()
        self.model.stop_rub_collection()

        frames = self.model.rub_frames()
        if phase is None or not frames:
            self.view.error("Failed to capture audio data.")
            return

        if phase == RubPhase.PRETRAIN:
            self._finish_pretraining(frames)
        elif phase == RubPhase.TRAIN:
            self._finish_training(frames)

    def _finish_pretraining(self, frames):
        buffer = self.model.rub_buffer
        if buffer.size == 0:
            self.view.error("Pre-training buffer is empty.")
            return
        worker = GMMFitWorker(self.model.gmm_pipeline, buffer.copy())
        worker.succeeded.connect(lambda: self._on_pretrain_fit_done(frames))
        worker.failed.connect(self._on_fit_failed)
        worker.finished.connect(self._clear_fit_worker)
        self._gmm_fit_worker = worker
        worker.start()
        print("[Pre-training] GMM fitting started asynchronously.")

    def _finish_training(self, frames):
        if not self.model.gmm_pretrained:
            self.view.error("Pre-training has not finished yet.")
            return

        scores = self._compute_scores(frames)
        if not scores:
            self.view.error("Failed to compute anomaly scores for training.")
            return

        standardized = [self.model.standardize_pretrain(s) for s in scores]
        self.model.train_score_mean = float(np.mean(standardized))
        self.model.train_score_std = float(np.std(standardized) + 1e-8)
        self.model.gmm_calibrated = True
        print(
            f"[Training] mu'={self.model.train_score_mean:.3f}, "
            f"sigma'={self.model.train_score_std:.3f}"
        )

    def _on_pretrain_fit_done(self, frames):
        scores = self._compute_scores(frames)
        if not scores:
            self.view.error("Failed to compute anomaly scores for pre-training.")
            return
        self.model.pretrain_score_mean = float(np.mean(scores))
        self.model.pretrain_score_std = float(np.std(scores) + 1e-8)
        self.model.gmm_pretrained = True
        print(
            f"[Pre-training] mu={self.model.pretrain_score_mean:.3f}, "
            f"sigma={self.model.pretrain_score_std:.3f}"
        )

    def _on_fit_failed(self, message: str):
        self.view.error(f"GMM fitting failed: {message}")

    def _clear_fit_worker(self):
        if self._gmm_fit_worker is not None:
            self._gmm_fit_worker.deleteLater()
            self._gmm_fit_worker = None

    def _compute_scores(self, frames):
        scores = []
        for frame in frames:
            if frame.size == 0:
                continue
            score = self.model.compute_anomaly(frame)
            scores.append(score)
        return scores

    def _set_gmm_inference(self, enabled: bool) -> None:
        self.model.gmm_is_infering = enabled
        self._refresh_anomaly_plot()
        state = "started" if enabled else "stopped"
        print(f"GMM inference {state}.")

    def _refresh_anomaly_plot(self):
        indices, scores, colors = self.model.latest_anomaly_series()
        self.view.update_anomaly_scatter(indices, scores, colors)

