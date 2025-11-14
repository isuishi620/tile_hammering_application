from sklearn.base import BaseEstimator, TransformerMixin
from scipy.sparse import csr_matrix
import librosa.filters as filter

class Mel(BaseEstimator, TransformerMixin):
    def __init__(self, model):
        self.model = model
        self.melfb = csr_matrix(filter.mel(sr=self.fs,
                                    n_fft=self.n_fft,
                                    n_mels=self.n_mels,
                                    fmin=self.f_min,
                                    fmax=self.f_max,
                                    htk=True,
                                    norm=1)[:,:self.f_range])

    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return self._mel(X)
    
    def _mel(self, x):
        return self.melfb.dot(x.T).T

    @property
    def fs(self):
        return self.model.sample_rate
    
    @property
    def n_mels(self):
        return self.model.PL_MEL_n_mels
    
    @property
    def n_fft(self):
        return self.model.PL_FFT_n_fft
    
    @property
    def f_min(self):
        return self.model.PL_MEL_f_min

    @property
    def f_max(self):
        return self.model.PL_MEL_f_max
    
    @property
    def f_range(self):
        return int(self.n_fft/2.56)+1