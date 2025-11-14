from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

class FastFourierTransform(BaseEstimator, TransformerMixin):
    def __init__(self, model):
        self.model = model

    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return self._fft(X)
    
    def _fft(self, x):
        if x.ndim == 1:
            x = x.reshape(1,-1)

        win = np.hanning(x.shape[-1])
        data = x * win
        spec = np.fft.rfft(a=data,
                           n=self.n_fft,
                           norm='forward')[:,:self.f_range]
        spec /= np.mean(win)
        spec = np.abs(spec) ** self.power
        spec[:,1:] *= 2
        return spec

    @property
    def fs(self):
        return self.model.sample_rate
    
    @property
    def n_fft(self):
        return self.model.PL_FFT_n_fft
    
    @property
    def power(self):
        return self.model.PL_FFT_power
    
    @property
    def f_range(self):
        return int(self.n_fft/2.56)+1