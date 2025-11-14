import sounddevice as sd
from pycaw.pycaw import AudioUtilities, IMMDevice
import numpy as np

self_api = 'WASAPI'
self_device = 'ライン'
self_sample_rate = 48000
self_input = 2
self_dtype = np.int16
self_block_size = 2048
self_is_active = False

def initialize():
    global self_is_active
    try:
        api_num = None
        device_num = None

        apis = sd.query_hostapis()
        api_num = next((i for i, api in enumerate(apis) if self_api in api["name"]), None)
        if api_num is None:
            raise ValueError("WASAPIが見つかりません")

        devices = sd.query_devices()
        device_num = next((j for j, device in enumerate(devices) if self_device in device["name"] and device["hostapi"] == api_num), None)
        if device_num is None:
            raise ValueError("USBAudioが見つかりません")

        sd.default.device = [device_num, None]
        device_dict = sd.query_devices(device_num)

        if device_dict['max_input_channels'] != self_input:
            raise ValueError("デバイスの入力チャンネル数が一致しません")

        if device_dict['default_samplerate'] != self_sample_rate:
            raise ValueError("デバイスのサンプルレートが一致しません")

        sd.default.samplerate = self_sample_rate
        sd.default.channels = self_input
        sd.default.dtype = self_dtype
        sd.default.blocksize = self_block_size

        current_mic = AudioUtilities.GetMicrophone()
        current_mic_id = current_mic.QueryInterface(IMMDevice).GetId()

        devices = AudioUtilities.GetAllDevices()
        target_mic_id = next((device.id for device in devices if "Active" in str(device.state) and self_device in str(device.FriendlyName)), None)
        if current_mic_id != target_mic_id:
            raise ValueError("入力デバイスをUSBAudioに設定してください")

        self_is_active = True

    except Exception as e:
        self_is_active = False
        raise ValueError(e)

def callback(indata, frames, time, status):
    data = indata[:, 0] * 0.00061035
    print(data.shape, data)

def main():
    initialize()
    with sd.InputStream(
        callback=callback,
        channels=self_input,
        samplerate=self_sample_rate,
        blocksize=self_block_size,
        dtype=self_dtype
    ):
        print("Streaming... Press Ctrl+C to stop.")
        while True:
            pass  # または time.sleep(1)

if __name__ == "__main__":
    main()
