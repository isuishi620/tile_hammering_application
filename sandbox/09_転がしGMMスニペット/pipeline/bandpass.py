from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np
from scipy import signal

class BandPassFilter(BaseEstimator, TransformerMixin):
    def __init__(self, model):
        self.model = model
        self.b, self.a = self._design_filter()

    def _design_filter(self):
        fn = self.model.sample_rate / 2
        fp = np.array([self.model.f_min, self.model.f_max])
        fs = np.array([self.model.f_min/2, self.model.f_max*1.5])
        wp = fp / fn
        ws = fs / fn
        N, Wn = signal.buttord(wp, ws, self.model.g_pass, self.model.g_stop)
        b, a = signal.butter(N, Wn, "band")
        return b, a

    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return self._bandpass(X)
    
    def _bandpass(self, x):
        y = signal.filtfilt(self.b, self.a, x)
        return y
