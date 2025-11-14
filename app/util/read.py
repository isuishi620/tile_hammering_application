from PyQt5.QtCore import QObject
import sounddevice as sd
from pycaw.pycaw import AudioUtilities, IMMDevice

# ===[ modelに移植済み　不要25/10/29 ]===
class Read(QObject):

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.stream = None

        self.time = 0
        self.model.audio_is_stream = False
        self.model.camera_is_stream = False
        self.initialize()

    def initialize(self):
        try:
            self.reset()
            api_num = None
            device_num = None

            # apis = sd.query_hostapis()
            # api_num = next((i for i, api in enumerate(apis) if self.model.api in api["name"]), None)
            # if api_num is None:
                # raise ValueError("WASAPIが見つかりません")

            # devices = sd.query_devices()
            # device_num = next((j for j, device in enumerate(devices) if self.model.device in device["name"] and device["hostapi"] == api_num), None)
            # if device_num is None:
                # raise ValueError("USBAudioが見つかりません")

            # sd.default.device = [device_num, None]
            # device_dict = sd.query_devices(device_num)
            
            # if device_dict['max_input_channels'] != self.model.input:
                # raise ValueError("デバイスの入力チャンネル数が一致しません")

            # if device_dict['default_samplerate'] != self.model.sample_rate:
                # raise ValueError("デバイスのサンプルレートが一致しません")
            
            # sd.default.samplerate = self.model.sample_rate
            # sd.default.channels = self.model.input
            # sd.default.dtype = self.model.dtype
            # sd.default.blocksize = self.model.block_size

            sd.default.samplerate = 48000
            sd.default.dtype = 'int16'
            sd.default.blocksize = 2048

            # current_mic = AudioUtilities.GetMicrophone()
            # current_mic_id = current_mic.QueryInterface(IMMDevice).GetId()
            
            # devices = AudioUtilities.GetAllDevices()
            # target_mic_id = next((device.id for device in devices if "Active" in str(device.state) and self.model.device in str(device.FriendlyName)), None)
            # if current_mic_id != target_mic_id:
                # raise ValueError("入力デバイスをUSBAudioに設定してください")


        except Exception as e:
            raise ValueError(e)
    
    def start(self):
        if not self.model.audio_is_stream:
            self.stream = sd.InputStream(callback=self.callback)
            self.stream.start()
            self.model.audio_is_stream = True
            

    def stop(self):
        if self.model.audio_is_stream and self.stream is not None:
            self.stream.close()
            self.stream = None
            self.model.audio_is_stream = False


    def callback(self, indata, frames, time, status):
        data = indata[:, self.model.ch] * self.model.eu
        self.time += frames / self.model.sample_rate
        self.model.read_time = self.time
        self.model.block_data = data.copy()
        

    def reset(self):
        sd._terminate()
        sd._initialize()

    def time_reset(self):
        self.time = 0
        self.model.read_time = 0



   
