import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.mixture import GaussianMixture


class GMM(BaseEstimator, TransformerMixin):
    def __init__(self, model):
        self.model = model
        self.gmm_ = None
        self._logp_mean = None
        self._logp_std = None

    def fit(self, X, y=None):
        X = np.asarray(X)
        if X.ndim == 1:
            X = X[np.newaxis, :]

        self.gmm_ = GaussianMixture(
            n_components=self.model.n_components,
            covariance_type=self.model.covariance_type,
            random_state=self.model.random_state,
        )
        self.gmm_.fit(X)

        logp_train = self.gmm_.score_samples(X)
        self._logp_mean = float(logp_train.mean())
        self._logp_std = float(logp_train.std() + 1e-8)
        converged = getattr(self.gmm_, "converged_", None)
        n_iter = getattr(self.gmm_, "n_iter_", None)
        print(
            "[GMM Fit] shape={}, components={}, converged={}, iter={}, "
            "logp_mean={:.3f}, logp_std={:.3f}".format(
                X.shape,
                self.model.n_components,
                converged,
                n_iter,
                self._logp_mean,
                self._logp_std,
            )
        )
        return self

    def transform(self, X):
        return self._anomaly_scores(X)

    def fit_transform(self, X, y=None):
        return self.fit(X, y).transform(X)

    def _anomaly_scores(self, X):
        if self.gmm_ is None:
            raise RuntimeError("GMM must be fitted before calling transform().")

        X = np.asarray(X)
        if X.ndim == 1:
            X = X[np.newaxis, :]

        log_probs = self.gmm_.score_samples(X)
        return -log_probs
