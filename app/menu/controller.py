import sys
import os
import pickle


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication
from app.base.model import ModelBase
from app.base.view import ViewBase
from app.base.controller import ControllerBase
from app.util.window import Window

class MenuController(ControllerBase):
    
    def __init__(self, model: ModelBase, view: ViewBase):
        super().__init__(model, view)
        self.model = model

    # pushButton_new_training
    # ===[ TRAINへの遷移 ]===
    def on_pushButton_new_training_clicked(self):
        # self.view.error('new training。')
        self.model.curl_window = 1
        self.signal.emit(Window.TRAIN)
    
    # pushButton_load_condition
    # ===[ 条件読み込みかどうかを決定後　TESTへの遷移 ]===
    def on_pushButton_load_condition_clicked(self):
        self._load_condition()
        # self.view.error('load condtion。')
        self.model.curl_window = 2
        self.signal.emit(Window.TEST)

    # pushButton_end
    def on_pushButton_end_clicked(self):
        QApplication.quit()

    def _delete_threshold_data(self):
        self.model.thresholded = False
        del self.model.threshold_data

    def _delete_train_data(self):
        self.model.trained = False
        del self.model.train_data

    # ===[ 条件読み込み ]===
    def _load_condition(self):
        if self.view.confirm('データを読み込みますか？'):
            filepath = self.view.read_file_dialog()
            if filepath is None:
                self.view.error('ファイルパスが設定されていません')
                return
            
            self._delete_threshold_data()
            self._delete_train_data()
            
            with open(filepath, 'rb') as file:
                data = pickle.load(file)

            self.model.train_data = data['train_data']            
            self.model.threshold_data = data['threshold_data']
            # print(f'{data['trigger_threshold']=}')
            self.model.trigger_threshold = data['trigger_threshold']
            self.model.anomaly_threshold = data['anomaly_threshold']
            # ===[ トリガーレベル ]===
            self.model.trig_level_val = self.model.trig_th2level()
            # print(f'{self.model.threshold=}')
            # print(f'{self.model.trig_level_val=}')

            if self.model.tap_train_sample_number == self.model.tap_train_target_count:
                self.model.pipeline.fit(self.model.train_data)
                self.model.trained = True
                

            if self.model.tap_th_sample_number == self.model.tap_threshold_target_count:
                self.model.thresholded = True
                anomaly = self.model.pipeline.transform(self.model.threshold_data)
                self.model.anomaly_threshold = anomaly
               
