import sys
import os
import time
from datetime import datetime
import pickle

import numpy as np


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from app.base.model import ModelBase
from app.base.view import ViewBase
from app.base.controller import ControllerBase
from app.util.window import Window
from app.model.rub import RubPhase

import cv2

# import sounddevice as sd


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


class TrainController(ControllerBase):

    def __init__(self, model: ModelBase, view: ViewBase):
        super().__init__(model, view)
        # self.add_config_updated_method(self.on_pushButton_3_clicked)


        self._set_tapping()
        # ===[ トリガレベルのint値で設定 ]===
        self.view.set_slider(self.model.trig_level_min,
                             self.model.trig_level_max,
                             self.model.trig_level_val)
        

        # ===[ All tap学習と閾値回数 rub学習と閾値時間s　の設定 ]===
        self.view.set_lcdNumberAll(self.model.tap_train_target_count,
                                   self.model.tap_threshold_target_count,
                                   self.model.rub_train_duration_sec,
                                   self.model.rub_threshold_duration_sec)
        
        self.model = model        
        self.view = view

        self.model.timer.signal.connect(self.handle_audio)
        self.model.timer.signal.connect(self.model.trigger.trigger)
        self.model.timer.signal.connect(self.handle_camera)
        self.model.rub_progress.connect(self._on_rub_progress)
        self._gmm_fit_worker = None

    def on_enter(self, payload=None):
        self.view.set_threshold(self.model.trigger_threshold) 
        self.view.verticalSlider_TrigLevel.setValue(self.model.trig_level_val)
        # ===[ read mic 開始 ]===
        self.start_process()

        
    # pushButton_StartTest
    def on_pushButton_StartTest_clicked(self):
        self._save_condition()
        # self.view.error('TEST。')
        # ===[ read mic 停止 ]===
        self.end_process()
        self.model.curl_window = 2
        self.signal.emit(Window.TEST)
    
    # pushButton_ReturnMenu
    def on_pushButton_ReturnMenu_clicked(self):
        if self.model.thresholded:
            self._save_condition()
        # ===[ read mic 停止 ]===
        self.end_process()
        self.model.curl_window = 0
        self.signal.emit(Window.MENU)
    
    
    def on_pushButton_SetTap_clicked(self):
        # ボタン色が変わり有効となる
        self._set_tapping()
     

    def on_pushButton_SetRub_clicked(self):
        # ボタン色が変わり有効となる
        # self.view.error('TEST。')
        self._set_rub()

    
    # pushButton_TrigLevel
    def on_pushButton_TrigLevel_clicked(self):
        
        # 現在の範囲と値を確認（コンソールに出力）
        # print(f"スライダーの最小値: {self.view.verticalSlider_TrigLevel.minimum()}")
        # print(f"スライダーの最大値: {self.view.verticalSlider_TrigLevel.maximum()}")
        print(f"トリガレベルの現在int値: {self.view.verticalSlider_TrigLevel.value()}")
        # ===[ トリガレベルの物理値 ]===        
        print(f"トリガレベルの現在物理値: {self.model.trigger_threshold:.2f}")

    # ===[ 閾値verticalSlider_TrigLevelの値変更 ]===
    def on_verticalSlider_TrigLevel_valueChanged(self, _name, _widget, _event, value):
        """スライダーが変更された後に実行されるメソッド"""
        # self.model.trig_level_val = self.view.verticalSlider_TrigLevel.value()
        # ===[ スライダーint value ]===
        self.model.trig_level_val = value
        # ===[ 閾値の物理値 ]===
        self.model.trigger_threshold = self.model.trig_level2th()
        self.view.set_threshold(self.model.trigger_threshold)        
        # print('============================================')
        # print(f'スライダーの値は：{self.model.trig_level_val}')
        # print(f'閾値は：{self.model.trigger_threshold:.2f}')



    
    # pushButton_TapTrainSampleStart
    def on_pushButton_TapTrainSampleStart_clicked(self):
        if self.model.trained:
            if self.view.confirm('訓練データを消去しますか？'):
                self._delete_train_data()
                # ===[ 閾値データも消去　トリガー停止 ]===
                self._delete_threshold_data()
                self._tap_th_sample_stop()
                self._set_tapping()
                
            else:
                # self.view.trigger_button_click(self.view.pushButton_8, 0)
                self._tap_train_sample_stop()
                pass
        
        self.model.trigger.start()
        # print(f"trigger_is_active: {self.model.trigger_is_active}")
        self.add_trigger_method(self.handle_train_data)
              
        self.view.lcdNumber_TapTrainSampleNumber.display(self.model.tap_train_sample_number)
        print(f"回数取得: {self.view.lcdNumber_TapTrainSampleNumber.intValue()}")


    def _tap_train_sample_stop(self):
        self.model.trigger.stop()
        self.remove_trigger_method(self.handle_train_data)


    # pushButton_TapTHSampleStart
    def on_pushButton_TapTHSampleStart_clicked(self):
        if self.model.thresholded:
            if self.view.confirm('閾値データを消去しますか？'):
                self._delete_threshold_data()
                self._set_tapping()
            else:
                # self.view.trigger_button_click(self.view.pushButton_13, 0)
                self._tap_th_sample_stop()
                pass

        self.model.trigger.start()
        self.add_trigger_method(self.handle_threshold_data)

        self.view.lcdNumber_TapTHSampleNumber.display(self.model.tap_th_sample_number)
        print(f"回数取得: {self.view.lcdNumber_TapTHSampleNumber.intValue()}") 
    
    def _tap_th_sample_stop(self):
        self.model.trigger.stop()
        self.remove_trigger_method(self.handle_threshold_data)

    # pushButton_RubTrainSampleStart
    def on_pushButton_RubTrainSampleStart_clicked(self):
        if self._gmm_fit_worker is not None:
            self.view.error('GMM fitting is running. Please wait.')
            return
        if self.model.rub_session.is_active():
            self.view.error('Audio capture is already active.')
            return
        if self.model.rub_pretrained:
            if not self.view.confirm('Remove existing rub training data?'):
                return
            self._reset_rub_learning()

        self.model.set_rub_train_elapsed(0.0)
        self.view.lcdNumber_RubTrainSampleTime.display(0)
        self._start_rub_capture(RubPhase.PRETRAIN, self.model.rub_train_duration_sec)
        self.view.label_RubFinish.setText('-pretrain-')
        self.view.label_RubFinish.setStyleSheet('background-color: rgb(0, 85, 255); color: white;')
        
    # pushButtopushButton_RubTHSampleStartn_RubTrainSampleStart
    def on_pushButton_RubTHSampleStart_clicked(self):
        if self._gmm_fit_worker is not None:
            self.view.error('GMM fitting is running. Please wait.')
            return
        if self.model.rub_session.is_active():
            self.view.error('Audio capture is already active.')
            return
        if not self.model.rub_pretrained:
            self.view.error('Complete rub pre-training first.')
            return
        if self.model.rub_trained:
            if not self.view.confirm('Remove existing rub threshold data?'):
                return

        self.model.rub_trained = False
        self.model.set_rub_threshold_elapsed(0.0)
        self.view.lcdNumber_RubTHSampleTimes.display(0)
        self._start_rub_capture(RubPhase.TRAIN, self.model.rub_threshold_duration_sec)
        self.view.label_RubFinish.setText('-training-')
        self.view.label_RubFinish.setStyleSheet('background-color: rgb(0, 85, 255); color: white;')


 
    
    def _set_tapping(self):
        
        # tapping 有効
        self.view.pushButton_SetTap.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")
        
        self.view.pushButton_TrigLevel.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")
        self.view.pushButton_TrigLevel.setEnabled(True)
        self.view.verticalSlider_TrigLevel.setStyleSheet("background-color: rgb(0, 85, 255);")
        self.view.verticalSlider_TrigLevel.setEnabled(True)
        self.view.pushButton_TapTrainSampleStart.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")
        self.view.pushButton_TapTrainSampleStart.setEnabled(True)
        
        if self.model.trained:
            self.view.pushButton_TapTHSampleStart.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")
            self.view.pushButton_TapTHSampleStart.setEnabled(True)
        else:
            self.view.pushButton_TapTHSampleStart.setStyleSheet("background-color: grey; color: white;")
            self.view.pushButton_TapTHSampleStart.setEnabled(False)
        if self.model.thresholded:
            self.view.label_TapFinish.setText('-finish-')
            self.view.label_TapFinish.setStyleSheet("background-color: rgb(0, 85, 255); color: red;")
        else:
            self.view.label_TapFinish.setText('-begin-')
            self.view.label_TapFinish.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")        
        

        # rub 無効
        self.view.pushButton_SetRub.setStyleSheet("background-color: grey; color: white;")

        self.view.pushButton_RubTrainSampleStart.setStyleSheet("background-color: grey; color: white;")
        self.view.pushButton_RubTrainSampleStart.setEnabled(False)
        self.view.pushButton_RubTHSampleStart.setStyleSheet("background-color: grey; color: white;")
        self.view.pushButton_RubTHSampleStart.setEnabled(False)
        self.view.label_RubFinish.setStyleSheet("background-color: grey;")
        # ===[ テスト開始を有効 ]===
        self._set_start_test()

    def _set_rub(self):
        
        # tapping 無効
        self.view.pushButton_SetTap.setStyleSheet("background-color: grey; color: white;")
        
        self.view.pushButton_TrigLevel.setStyleSheet("background-color: grey; color: white;")
        self.view.pushButton_TrigLevel.setEnabled(False)
        self.view.verticalSlider_TrigLevel.setStyleSheet("background-color: grey; color: white;")
        self.view.verticalSlider_TrigLevel.setEnabled(False)
        self.view.pushButton_TapTrainSampleStart.setStyleSheet("background-color: grey; color: white;")
        self.view.pushButton_TapTrainSampleStart.setEnabled(False)
        self.view.pushButton_TapTHSampleStart.setStyleSheet("background-color: grey; color: white;")
        self.view.pushButton_TapTHSampleStart.setEnabled(False)
        # self.view.label_TapFinish.setText('-begin-')
        self.view.label_TapFinish.setStyleSheet("background-color: grey;")

        # rub 有効
        self.view.pushButton_SetRub.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")

        self.view.pushButton_RubTrainSampleStart.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")
        self.view.pushButton_RubTrainSampleStart.setEnabled(True)
        self.view.pushButton_RubTHSampleStart.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")
        self.view.pushButton_RubTHSampleStart.setEnabled(True)
        self._update_rub_finish_label()
        # ===[ テスト開始を有効 ]===
        self._set_start_test()

    # pushButton_StartTest
    def _set_start_test(self):
        if self.model.rub_trained or self.model.thresholded:
            self.view.pushButton_StartTest.setEnabled(True)
            self.view.pushButton_StartTest.setStyleSheet("background-color: rgb(0, 85, 255);")
        else:
            self.view.pushButton_StartTest.setEnabled(False)
            self.view.pushButton_StartTest.setStyleSheet("background-color: grey;")

    def _start_rub_capture(self, phase: RubPhase, duration: float):
        self.model.start_rub_collection(time.monotonic(), phase, duration)

    def _on_rub_progress(self, *_):
        if not self.model.rub_session.is_active():
            return
        now = time.monotonic()
        elapsed = self.model.rub_elapsed(now)
        phase = self.model.rub_phase()
        if phase == RubPhase.PRETRAIN:
            self.view.set_lcd(self.view.lcdNumber_RubTrainSampleTime, int(elapsed))
        elif phase == RubPhase.TRAIN:
            self.view.set_lcd(self.view.lcdNumber_RubTHSampleTimes, int(elapsed))

        if self.model.rub_collection_completed(now):
            self._complete_rub_session()

    def _complete_rub_session(self):
        phase = self.model.rub_phase()
        self.model.stop_rub_collection()
        frames = self.model.rub_frames()
        if phase is None or not frames:
            self.view.error('Failed to capture audio data.')
            return

        elapsed = self.model.rub_session.counting_time
        if phase == RubPhase.PRETRAIN:
            self.model.set_rub_train_elapsed(elapsed)
            self.view.set_lcd(self.view.lcdNumber_RubTrainSampleTime, int(elapsed))
            self._finish_rub_pretraining(frames)
        elif phase == RubPhase.TRAIN:
            self.model.set_rub_threshold_elapsed(elapsed)
            self.view.set_lcd(self.view.lcdNumber_RubTHSampleTimes, int(elapsed))
            self._finish_rub_training(frames)
        self._set_rub()

    def _finish_rub_pretraining(self, frames):
        buffer = self.model.rub_buffer
        if buffer.size == 0:
            self.view.error('Pre-training buffer is empty.')
            return
        worker = GMMFitWorker(self.model.gmm_pipeline, buffer.copy())
        worker.succeeded.connect(lambda: self._on_pretrain_fit_done(frames))
        worker.failed.connect(self._handle_fit_failed)
        worker.finished.connect(self._clear_gmm_worker)
        self._gmm_fit_worker = worker
        self.view.show_popup('GMM pre-training is running...')
        worker.start()

    def _on_pretrain_fit_done(self, frames):
        scores = self._compute_rub_scores(frames)
        if not scores:
            self.view.error('Failed to compute anomaly scores for pre-training.')
            return
        self.model.pretrain_score_mean = float(np.mean(scores))
        self.model.pretrain_score_std = float(np.std(scores) + 1e-8)
        self.model.rub_pretrained = True
        self._update_rub_finish_label()

    def _finish_rub_training(self, frames):
        if not self.model.rub_pretrained:
            self.view.error('Pre-training has not finished yet.')
            return
        scores = self._compute_rub_scores(frames)
        if not scores:
            self.view.error('Failed to compute anomaly scores for training.')
            return
        standardized = np.asarray([self.model.standardize_pretrain(s) for s in scores], dtype=float)
        self.model.train_score_mean = float(np.mean(standardized))
        self.model.train_score_std = float(np.std(standardized) + 1e-8)
        sigma1 = self.model.train_score_mean + self.model.train_score_std
        sigma2 = self.model.train_score_mean + 2 * self.model.train_score_std
        sigma3 = self.model.train_score_mean + 3 * self.model.train_score_std
        self.model.set_rub_threshold_bands(sigma1, sigma2, sigma3)
        self.model.rub_trained = True
        self.model.gmm_trained = True
        self._update_rub_finish_label()

    def _handle_fit_failed(self, message: str):
        self.view.close_popup()
        self.view.error(f'GMM fitting failed: {message}')

    def _clear_gmm_worker(self):
        self.view.close_popup()
        if self._gmm_fit_worker is not None:
            self._gmm_fit_worker.deleteLater()
            self._gmm_fit_worker = None

    def _compute_rub_scores(self, frames):
        scores = []
        for frame in frames:
            if frame.size == 0:
                continue
            try:
                score = self.model.compute_rub_anomaly(frame)
            except Exception as exc:
                self.view.error(str(exc))
                return []
            scores.append(score)
        return scores

    def _reset_rub_learning(self):
        if self.model.rub_session.is_active():
            self.model.stop_rub_collection()
        self.model.rub_pretrained = False
        self.model.rub_trained = False
        self.model.gmm_trained = False
        self.model.pretrain_score_mean = 0.0
        self.model.pretrain_score_std = 1.0
        self.model.train_score_mean = 0.0
        self.model.train_score_std = 1.0
        self.model.rub_anomaly_scores.clear()
        self.model.set_rub_train_elapsed(0.0)
        self.model.set_rub_threshold_elapsed(0.0)
        self.model.set_rub_threshold_bands(0.0, 0.0, 0.0)
        self.view.lcdNumber_RubTrainSampleTime.display(0)
        self.view.lcdNumber_RubTHSampleTimes.display(0)
        self._update_rub_finish_label()
        self._set_start_test()

    def _update_rub_finish_label(self):
        if self.model.rub_trained:
            self.view.label_RubFinish.setText('-finish-')
            self.view.label_RubFinish.setStyleSheet("background-color: rgb(0, 85, 255); color: red;")
        elif self.model.rub_pretrained:
            self.view.label_RubFinish.setText('-pretrained-')
            self.view.label_RubFinish.setStyleSheet("background-color: rgb(0, 85, 255); color: yellow;")
        else:
            self.view.label_RubFinish.setText('-begin-')
            self.view.label_RubFinish.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")

    def handle_audio(self): 
        if self.model.audio_is_stream and self.model.curl_window == 1:
            # self.view.plot(self.view.audio_curve, self.model.block_data)
            self.view.plot(self.view.audio_curve, self.model.buffer_data)
            
    
    def handle_camera(self):
        if self.model.camera_is_stream and self.model.curl_window == 1:
            self.view.image(self.view.camera_image, self.model.camera_data)


    def handle_train_data(self):
        # print(f"handle_train_data: ")
        # print(len(self.model.train_data))
        if not self.model.trained:
            self.model.train_data = self.model.trigger_data
            self.view.set_lcd(self.view.lcdNumber_TapTrainSampleNumber, self.model.tap_train_sample_number)

            if self.model.tap_train_sample_number == self.model.tap_train_target_count:
                self.model.pipeline.fit(self.model.train_data)                
                self.model.trained = True
                self._set_tapping()
                # self._threshold_ready(True)                
                self._tap_train_sample_stop()

    def handle_threshold_data(self):
        if not self.model.thresholded:
            self.model.threshold_data = self.model.trigger_data         
            self.view.set_lcd(self.view.lcdNumber_TapTHSampleNumber, self.model.tap_th_sample_number)

            if self.model.tap_th_sample_number == self.model.tap_threshold_target_count:
                self.model.thresholded = True
                anomaly = self.model.pipeline.transform(self.model.threshold_data)
                print(f"{anomaly=}")
                self.model.anomaly_threshold = anomaly
                print(f"{self.model.anomaly_threshold=}")
                self._set_tapping()
                # self._threshold_finish(True)
                self._tap_th_sample_stop()

    '''
    def _threshold_ready(self,bool):
        print(f"self.model.trained: {self.model.trained}")
        self.view.pushButton_TapTHSampleStart.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")
        self.view.pushButton_TapTHSampleStart.setEnabled(bool)

    def _threshold_finish(self,bool):
        print(f"self.model.thresholded: {self.model.thresholded}")
        self.view.label_TapFinish.setText('-finish-')
    '''


    def _delete_train_data(self):
        self.model.trained = False
        del self.model.train_data
        self.view.set_lcd(self.view.lcdNumber_TapTrainSampleNumber, self.model.tap_train_sample_number)
        # self._threshold_ready(False)

    def _delete_threshold_data(self):
        self.model.thresholded = False
        del self.model.threshold_data
        self.view.set_lcd(self.view.lcdNumber_TapTHSampleNumber, self.model.tap_th_sample_number)

    def _save_condition(self):
        if self.view.confirm('データを保存しますか？'):
            time = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = 'TRAIN_' + time
            filepath = self.view.save_file_dialog(filename)
            if filepath is None:
                self.view.error('ファイルパスが設定されていません')
                return
            
            data = {
                'trigger_threshold':self.model.trigger_threshold,
                'train_data':self.model.train_data,
                'threshold_data':self.model.threshold_data,
                'anomaly_threshold':self.model.anomaly_threshold
            }

            with open(filepath, 'wb') as file:
                pickle.dump(data, file)

    
