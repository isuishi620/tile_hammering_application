import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class ZScore(BaseEstimator, TransformerMixin):
    def __init__(self):
        self._mean = None
        self._std = None

    def fit(self, X, y=None):
        self.mean = np.mean(X, axis=0)
        self.std = np.std(X, axis=0)
        self.std[self.std == 0] = 1e-8
        print(self.mean.shape, self.std.shape)

    def transform(self, X):
        z_scores = (X - self.mean) / self.std
        anomaly = np.mean(np.abs(z_scores), axis=1)
        return anomaly

    def fit_transform(self, X, y=None):
        return self.fit(X).transform(X)

    @property
    def mean(self):
        return self._mean

    @mean.setter
    def mean(self, value):
        self._mean = value

    @property
    def std(self):
        return self._std

    @std.setter
    def std(self, value):
        self._std = value
