from sklearn.base import BaseEstimator, TransformerMixin
from scipy.sparse import csr_matrix
import librosa.filters as filter

class Mel(BaseEstimator, TransformerMixin):
    def __init__(self, model):
        self.model = model
        self.melfb = csr_matrix(filter.mel(sr=self.model.sample_rate,
                                    n_fft=self.model.n_fft,
                                    n_mels=self.model.n_mels,
                                    fmin=self.model.f_min,
                                    fmax=self.model.f_max,
                                    htk=True,
                                    norm=1)[:,:self.f_range])

    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return self._mel(X)
    
    def _mel(self, x):
        return self.melfb.dot(x.T).T
    @property
    def f_range(self):
        return int(self.model.n_fft/2.56)+1