import sys
import os
import pyqtgraph as pg
# (QImage と QImage.Format をインポートしておく必要があります)
from PyQt5.QtGui import QImage
from datetime import datetime

import tkinter as tk
from tkinter import filedialog
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication
from app.base.model import ModelBase
from app.base.view import ViewBase
from app.base.controller import ControllerBase
from app.util.window import Window

import cv2

class TestController(ControllerBase):

    def __init__(self, model: ModelBase, view: ViewBase):
        super().__init__(model, view)
        # self.add_config_updated_method(self.on_pushButton_3_clicked)
        # ===[ True:tapping / False:rub or 未選択 ]===
        self.sw_tapping: bool = True
        # self._set_tapping()
        # ===[ True:play / False:pause ]===
        self.sw_play: bool = False
        self.selected_path: str = os.getcwd()
        # ===[ 1:monitor view on ]===
        self.sw_monitor_view_on: bool = True


        self.model = model
        self.view = view

        # self.model.timer.signal.connect(self.handle_test_data)
        self.add_timeout_method(self.model.trigger.trigger)
        # self.model.timer.signal.connect(self.model.trigger.trigger)
        self.model.timer.signal.connect(self.handle_camera)
                
        # これを追加すれば、一先ずはトリガが動作するようになります。
        self.model.timer.signal.connect(self.handle_timer_signal)
        self.model.timer.signal.connect(self.handle_rub_inference)


    def on_enter(self, payload=None):
        if self.model.thresholded:
            self.sw_tapping = True
            self._set_tapping()
        elif self.model.rub_trained:
            self.sw_tapping = False
            self._set_tapping()
        else:
            self.view.error('tapping and rubbing 未学習。')
        # ===[ read mic 開始 ]===
        self.start_process()
    
   

    # pushButton_ReturnTraining
    def on_pushButton_ReturnTraining_clicked(self):
        # ===[ read mic 停止 ]===
        self.end_process()
        self.model.curl_window = 1
        self.signal.emit(Window.TRAIN)
    

    # pushButton_Tapping
    def on_pushButton_Tapping_clicked(self):
        self._stop_playback()
        self.sw_tapping = True
        self._set_tapping()

    # pushButton_Rubbing
    def on_pushButton_Rubbing_clicked(self):
        self._stop_playback()
        self.sw_tapping = False
        self._set_tapping()

    # pushButton_NgFolder
    def on_pushButton_NgFolder_clicked(self):
        # ===[ 新規フォルダ作成するか　既存フォルダ選択するか ]===
        self.selected_path = self.get_folder_path()           
        print(f"選択したフォルダ:{self.selected_path=}")

    # pushButton_MonitorViewOn
    def on_pushButton_MonitorViewOn_clicked(self):
        self.sw_monitor_view_on = not self.sw_monitor_view_on
        
        print(f"{self.sw_monitor_view_on=}")
        print(f"{self.model.camera_is_stream=}")
        if self.sw_monitor_view_on:
            # self.model.timer.signal.connect(self.handle_camera)
            # self.model.camera_is_stream = True
            self.view.pushButton_MonitorViewOn.setStyleSheet("background-color: rgb(0, 85, 255); color: white;")
        else:
            self.view.pushButton_MonitorViewOn.setStyleSheet("background-color: grey; color: white;")
            '''
            try:
                # self.model.camera_is_stream = False
                self.model.timer.signal.disconnect(self.handle_camera)
            except TypeError:
                # 接続されていなかった場合、何もしない
                pass
            '''
        

    
    # pushButton_play
    def on_pushButton_play_clicked(self):
        self.view.pushButton_stop.setEnabled(True)
        self.view.pushButton_stop.setStyleSheet("background-color: rgb(0, 85, 255);")
        if self.sw_tapping:
            self.sw_play = not self.sw_play
            if self.sw_play:
                self.view.pushButton_play.setText('⏸')
                self.model.trigger.start()
                self.add_trigger_method(self.handle_test_data)
            else:
                self.view.pushButton_play.setText('▶')
                self.model.trigger.stop()
                self.remove_trigger_method(self.handle_test_data)
        else:
            if not self.model.rub_trained:
                self.view.error('rub 未学習です')
                self.view.pushButton_stop.setEnabled(False)
                self.view.pushButton_stop.setStyleSheet("background-color: grey;")
                return
            self.sw_play = not self.sw_play
            if self.sw_play:
                self.view.pushButton_play.setText('⏸')
                self._set_rub_inference(True)
            else:
                self.view.pushButton_play.setText('▶')
                self._set_rub_inference(False)


    # pushButton_stop
    # ===[ stop button handler ]===
    def on_pushButton_stop_clicked(self):
        self.view.pushButton_play.setEnabled(True)
        self.view.pushButton_play.setStyleSheet("background-color: rgb(0, 85, 255);")
        self.view.pushButton_stop.setStyleSheet("background-color: grey;")
        self._stop_playback()
        

    def handle_camera(self):
        if self.model.camera_is_stream and self.model.curl_window == 2:
            _data = self.model.camera_data
            if self.sw_monitor_view_on: 
                self.view.image(self.view.camera_image, _data)

    def handle_test_data(self):
        if not self.sw_tapping:
            return
        if self.model.audio_is_stream and self.model.curl_window == 2:
            print(f'{self.model.anomaly_threshold=}')
            _trigger_data = self.model.trigger_data
            self.model.test_data = _trigger_data
            anomaly = self.model.pipeline.transform(_trigger_data)[0]
            print(f'{anomaly=}')
            self.model.test_anomaly = anomaly

            self.view.plot_anomaly_scatter(
                                self.model.test_anomaly,
                                self.model.anomaly_threshold,
                                self.model.display_count
            )

            
            # ===[ jpg保存 ]===
            medium = self.model.anomaly_threshold[-1]
            flg_test = True
            if anomaly > medium and flg_test:
                # print('save jpg')
                self.save_jpg(anomaly)



    def _set_tapping(self):
        # ===[ tapping testを選択 ]===
        if self.sw_tapping:
            self.view.pushButton_Rubbing.setStyleSheet("background-color: grey;")
            if self.model.thresholded:
                self.view.pushButton_Tapping.setStyleSheet("background-color: rgb(0, 85, 255);")
                self.view.pushButton_play.setEnabled(True)
                self.view.pushButton_play.setStyleSheet("background-color: rgb(0, 85, 255);")
                self.view.threshold(low=self.model.anomaly_threshold[0],
                            medium=self.model.anomaly_threshold[-1])
            else:
                print(f"{self.model.thresholded=} tapping 未学習")
                self.view.error('tapping 未学習。')
                self.view.pushButton_play.setEnabled(False)
                self.view.pushButton_stop.setEnabled(False)
                self.view.pushButton_play.setStyleSheet("background-color: grey;")
                self.view.pushButton_stop.setStyleSheet("background-color: grey;")
                self.view.pushButton_play.setText('▶')
                
        # ===[ rub testを選択 ]===
        else:
            self.view.pushButton_Tapping.setStyleSheet("background-color: grey;")
            if self.model.rub_trained:
                self.view.pushButton_Rubbing.setStyleSheet("background-color: rgb(0, 85, 255);")
                self.view.pushButton_play.setEnabled(True)
                self.view.pushButton_play.setStyleSheet("background-color: rgb(0, 85, 255);")
                low, medium, _ = self.model.rub_threshold_bands
                self.view.threshold(low, medium)
            else:
                print(f"{self.model.rub_trained=} rub 未学習")
                self.view.error('rub 未学習。')
                self.view.pushButton_play.setEnabled(False)
                self.view.pushButton_stop.setEnabled(False)
                self.view.pushButton_play.setStyleSheet("background-color: grey;")
                self.view.pushButton_stop.setStyleSheet("background-color: grey;")
                self.view.pushButton_play.setText('▶')
                
            


    def _stop_playback(self):
        if self.sw_tapping:
            self.model.trigger.stop()
            self.remove_trigger_method(self.handle_test_data)
        else:
            self._set_rub_inference(False)
        self.sw_play = False
        self.view.pushButton_play.setText('▶')
        self.view.pushButton_stop.setEnabled(False)
        self.view.pushButton_stop.setStyleSheet("background-color: grey;")

    def _set_rub_inference(self, enabled: bool):
        self.model.gmm_is_infering = enabled
        if not enabled:
            return

    def handle_rub_inference(self):
        if not (self.model.audio_is_stream and self.model.curl_window == 2):
            return
        if self.sw_tapping or not self.model.gmm_is_infering or not self.model.rub_trained:
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
        normalized = max(0.0, normalized)
        absolute = self.model.denormalize_training(normalized)
        self.model.record_rub_anomaly_score(absolute)
        indices, scores, colors = self.model.latest_rub_anomaly_series(self.model.display_count)
        self.view.plot_rub_anomaly_scatter(indices, scores, colors)
        low, medium, high = self.model.rub_threshold_bands
        self.view.threshold(low, medium)
        if absolute > high:
            self.save_jpg(absolute)

    def get_folder_path(self):
        """
        フォルダ選択ダイアログを開き、選択されたフォルダのパスを返す。
        """
    
        # メインウィンドウを作成し、非表示にする
        root = tk.Tk()
        root.withdraw()
      
        # 1. ダイアログが最初に開く場所（=現在開いたフォルダ）を定義
        # initial_folder = os.getcwd()
        initial_folder = self.selected_path
        # print(f"ダイアログを '{initial_folder}' で開きます...")

        # 2. initialdir を指定してダイアログを開く
        _selected_path = filedialog.askdirectory(
            title="フォルダを選択してください",
            initialdir=initial_folder
        )
    
        # 3. 戻り値をチェック
        if _selected_path:
            # フォルダが選択された場合
            print("OKが押されました。")
            time = datetime.now().strftime("%Y%m%d%H%M%S")
            folder_name = time + '_' + self.view.textEdit_memo.toPlainText()
            folder_path = Path(_selected_path + '/' + folder_name)
            # folder_path_for_saving = str(folder_path)
            # print(f"{folder_path_for_saving=}")
            if self.view.confirm('新規フォルダ' + str(folder_path) + 'を作成しますか？'):
                self.make_dir(folder_path)
                return folder_path
            else:
                return _selected_path
        else:
            # キャンセルが押された場合 (selected_path == "")
            print("キャンセルが押されました。")
            # 保持しておいた「最初に開いた場所」のパスを返す
            return initial_folder

    
    def make_dir(self, folder_path):
        # 作成したいフォルダのパスを指定
        # folder_path = Path("my_project/data/logs") 
        # (例: C:/Users/YourName/my_project/data/logs など)

        # フォルダを作成 (存在しない場合のみ)
        # 途中の 'my_project' や 'data' フォルダも自動で作られる
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"フォルダ '{folder_path}' の準備ができました。")
    
    
    def save_jpg(self, anomaly):
        # ===[ jpgファイルとして保存 ]===
        try:
            # 1. ImageItemからNumpy配列データを取得
            # numpy_data = self.view.camera_image.image
            # self.model.camera_data            
            # numpy_data = self.model.camera_data
            numpy_data = self.model.camera_data
            
            if numpy_data is None:
                print("エラー: ImageItemに画像データがありません。")
                return
            numpy_data_for_save = numpy_data.transpose((1, 0, 2))

            # 1. (numpy_data_for_save は (H, W, 3) の RGB データと仮定)
            #    (もし .copy() していない場合、安全のためにコピーします)
            if not numpy_data_for_save.flags['C_CONTIGUOUS']:
                numpy_data_for_save = numpy_data_for_save.copy()

            height, width, channel = numpy_data_for_save.shape
            bytes_per_line = 3 * width # 1行あたりのバイト数

            # 2. QImageを「RGB888」形式として明示的に作成
            q_image = QImage(
                numpy_data_for_save.data,  # Numpy配列のデータバッファ
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888 # ★これがRGBであることを指定
            )

            # 2. Numpy配列をQImageに変換
            #    pg.makeQImageがデータ型やRGB/グレースケールを自動判別します
            #    (transpose=False はNumpy配列の形状 (row, col, ch) を維持するため)
            # q_image = pg.makeQImage(numpy_data_for_save, transpose=False)
            # (numpy_data_for_save は (H, W, C) の BGR データとします)

            time = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = time + f"_{anomaly:.2f}.jpg"
            base_path = Path(self.selected_path)
            final_path = base_path / file_name
            file_path_for_saving = str(final_path)
            # print(f"{file_path_for_saving=}")

            # 3. ★ユニークなパスを取得する関数を呼び出す★
            unique_path = get_unique_filepath(file_path_for_saving)
            # print(f"保存先: {unique_path}")

            # 4. QImage.save() でBMP形式で保存
            # success = q_image.save(unique_path, "BMP")
            # 4. (推奨) 品質を指定して保存 (例: 90%)
            # -1 から 100 までの整数。-1はデフォルト値。
            quality = 90 
            success = q_image.save(unique_path, "JPG", quality)
            if success:
                print(f"画像を '{unique_path}' として保存しました。")
            else:
                print(f"ファイルの保存に失敗しました。")

        except Exception as e:
            print(f"保存中にエラーが発生しました: {e}")


def get_unique_filepath(filepath_str: str) -> str:
    """
    指定されたファイルパスが存在するか確認し、
    もし存在すれば、ユニークなファイル名（例: file_1.jpg）を返します。
    """
    path = Path(filepath_str)

    # 1. もしファイルが存在しなければ、そのままのパスを返す
    if not path.exists():
        return str(path)

    # 2. ファイルが存在する場合、新しい名前を試す
    parent = path.parent   # 親フォルダ (例: C:/my_folder)
    stem = path.stem       # ファイル名 (例: output)
    suffix = path.suffix   # 拡張子 (例: .jpg)
    
    i = 1
    while True:
        # 新しいファイル名を生成 (例: output_1.jpg)
        new_filename = f"{stem}_{i}{suffix}"
        new_path = parent / new_filename
        
        # 新しいパスが存在しないかチェック
        if not new_path.exists():
            return str(new_path) # ユニークなパスが見つかった
        
        i += 1 # 存在したので、次の番号 (i+1) を試す
