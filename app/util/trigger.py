import numpy as np
from PyQt5.QtCore import QObject

class Trigger(QObject):

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.buffer_num: int = -5
        self.hold: float = 0.05
        self.offset: int = -1024
        self.length: int = 4096
   

    def trigger(self):
        
        if not self._should_trigger():
            return

        self.model.time_reset()

        buffer_data_list = list(self.model.__dict__['_buffer_data'])
        buffer_num = self.buffer_num  

        # トリガーをかけるために監視したブロックの一つ前からのバッファを取得
        buffer_slice = buffer_data_list[buffer_num-1:]
        trigger_data = self._extract_trigger_data(np.concatenate(buffer_slice))
        self.model.trigger_data = trigger_data

    def start(self):
        self.model.trigger_is_active = True

    def stop(self):
        self.model.trigger_is_active = False

    def _should_trigger(self):
        return (
            self.is_active and
            self.height is not None and
            self._is_threshold_exceeded() and
            self.model.read_time >= self.hold
        )
    
    def _is_threshold_exceeded(self):
        # buffer_dataのゲッターはコンカチされちゃってる
        buffer_data_list = list(self.model.__dict__['_buffer_data'])
        buffer_num = self.buffer_num
        return np.any(buffer_data_list[buffer_num] >= self.height)

    def _extract_trigger_data(self, data):
        index = np.argmax(data >= self.height)
        start = max(0, index + self.offset)
        end = start + self.length
        return data[start:end]
    
    @property
    def is_active(self):
        return self.model.trigger_is_active

    @property
    def height(self):
        return self.model.trigger_threshold
    

