import numpy as np
from scipy import signal
from sklearn.base import BaseEstimator, TransformerMixin


class ShortTimeFourierTransform(BaseEstimator, TransformerMixin):
    def __init__(self, model):
        self.model = model

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return self._stft_any(X)

    def _stft_one(self, x):
        """短いフレームではゼロ詰めFFTへ切り替えながらSTFTを適用する。"""
        x = np.asarray(x).astype(np.float32)
        n_fft = self.model.fft_size
        fs = self.model.sample_rate

        if x.size < n_fft:
            pad = n_fft - x.size
            x_pad = np.pad(x, (0, pad)) if pad > 0 else x
            win = signal.get_window(self.model.fft_window, n_fft, fftbins=True)
            frame = x_pad[:n_fft] * win
            Z = np.fft.rfft(frame)
            Z = Z[: self.f_range]
            S = np.abs(Z)[np.newaxis, :]
        else:
            f, t, Zxx = signal.stft(
                x,
                fs=fs,
                window=self.model.fft_window,
                nperseg=n_fft,
                noverlap=self.model.stft_overlap,
                nfft=n_fft,
                return_onesided=True,
            )
            Zxx = Zxx[: self.f_range, :]
            S = np.abs(Zxx).T
        if self.model.fft_power not in (None, 1.0):
            S = S**self.model.fft_power

        return S

    def _stft_any(self, X):
        if isinstance(X, (list, tuple)):
            return [self._stft_one(np.asarray(x)) for x in X]

        X = np.asarray(X)

        if X.ndim == 1:
            return self._stft_one(X)
        if X.ndim == 2:
            outs = [self._stft_one(row) for row in X]
            return np.concatenate(outs, axis=0)

        raise ValueError(f"X must be 1D or 2D, got shape {X.shape}")

    @property
    def f_range(self):
        return int(self.model.fft_size / 2.56) + 1
