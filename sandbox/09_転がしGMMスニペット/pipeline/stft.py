from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np
from scipy import signal

class ShortTimeFourierTransform(BaseEstimator, TransformerMixin):

    def __init__(self, model):
        self.model = model

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return self._stft_any(X)

    def _stft_one(self, x):
        """
        x: 1D 波形
        - 長い場合: 通常の STFT (多フレーム)
        - 短い場合: 1フレーム FFT (ゼロパディング) として扱う
        """
        x = np.asarray(x).astype(np.float32)
        n_fft = self.model.n_fft
        fs = self.model.sample_rate

        # --- 短い信号: FFT 1フレーム ---
        if x.size < n_fft:
            # ゼロパディング
            pad = n_fft - x.size
            if pad > 0:
                x_pad = np.pad(x, (0, pad))
            else:
                x_pad = x

            # 窓
            win = signal.get_window(self.model.window, n_fft, fftbins=True)
            frame = x_pad[:n_fft] * win

            # 実数 FFT
            Z = np.fft.rfft(frame)  # (n_fft/2+1,)
            Z = Z[:self.f_range]    # 周波数範囲を制限
            S = np.abs(Z)[np.newaxis, :]  # (1, F)

        # --- 十分長い信号: 普通に STFT ---
        else:
            f, t, Zxx = signal.stft(
                x,
                fs=fs,
                window=self.model.window,
                nperseg=n_fft,
                noverlap=self.model.noverlap,
                nfft=n_fft,
                return_onesided=True,
            )
            # Zxx: (F, T)
            Zxx = Zxx[:self.f_range, :]  # F を制限
            S = np.abs(Zxx).T            # (T, F)

        # power の適用（既存の仕様を踏襲）
        if self.model.power is not None and self.model.power != 1.0:
            S = S ** self.model.power

        return S  # (T, F)

    def _stft_any(self, X):
        """
        - list/tuple: それぞれ _stft_one してリストで返す（既存仕様維持）
        - 1D: 単一波形として処理
        - 2D: バッチとして各行に _stft_one を適用して縦に結合
        """
        if isinstance(X, (list, tuple)):
            return [self._stft_one(np.asarray(x)) for x in X]

        X = np.asarray(X)

        if X.ndim == 1:
            return self._stft_one(X)

        elif X.ndim == 2:
            outs = [self._stft_one(row) for row in X]
            # フレームを全部繋ぐ（用途に応じてここを変えても良い）
            return np.concatenate(outs, axis=0)

        else:
            raise ValueError(f"X must be 1D or 2D, got shape {X.shape}")

    @property
    def f_range(self):
        # 既存の仕様そのまま
        return int(self.model.n_fft / 2.56) + 1
