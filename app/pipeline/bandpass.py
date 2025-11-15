from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np
from scipy import signal

class BandPassFilter(BaseEstimator, TransformerMixin):
    def __init__(self, model):
        self.model = model
        self.b, self.a = self._design_filter()

    def _design_filter(self):
        fn = self.fs / 2
        fp = np.array([self.f_min, self.f_max])
        fs = np.array([self.f_min/2, self.f_max*1.5])
        wp = fp / fn
        ws = fs / fn
        N, Wn = signal.buttord(wp, ws, self.g_pass, self.g_stop)
        # バターワースではゲインを触らず、次数とカットオフで決める
        # LPFとHPFを分けるにしてもNの数は把握しておきたい
        b, a = signal.butter(N, Wn, "band")
        return b, a

    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return self._bandpass(X)
    
    def _bandpass(self, x):
        y = signal.filtfilt(self.b, self.a, x)
        return y

    @property
    def fs(self):
        return self.model.sample_rate
    
    @property
    def f_min(self):
        return self.model.bandpass_min_hz

    @property
    def f_max(self):
        return self.model.bandpass_max_hz
    
    @property
    def g_pass(self):
        return self.model.bandpass_pass_ripple_db
    
    @property
    def g_stop(self):
        return self.model.bandpass_stop_ripple_db
